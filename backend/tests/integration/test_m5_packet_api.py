"""API integration coverage for the M5 packet read-model (PR3, Issue #219).

Drives the M5 HTTP surface against PostgreSQL through a real ``TestClient`` whose
tracker unit of work is bound to a SAVEPOINT-isolated session: the handlers'
``commit()`` calls only release savepoints, and the outer transaction is rolled back
at teardown so no row persists. Skipped automatically when the database is unreachable.

Requires migrations applied (``alembic upgrade head``).
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from applypilot.config.settings import get_settings
from applypilot.db.dependencies import TrackerUnitOfWork, get_tracker_unit
from applypilot.main import app

_CONNECT_TIMEOUT = 2


@pytest.fixture()
def db_session():
    """Yield a SAVEPOINT-isolated session; the outer transaction is always rolled back."""
    settings = get_settings()
    engine = create_engine(
        settings.database_url,
        future=True,
        connect_args={"connect_timeout": _CONNECT_TIMEOUT},
    )
    try:
        connection = engine.connect()
    except Exception as exc:
        engine.dispose()
        pytest.skip(f"PostgreSQL not available (start with: docker compose up -d postgres): {exc}")

    transaction = connection.begin()
    session = sessionmaker(
        bind=connection,
        autoflush=False,
        autocommit=False,
        join_transaction_mode="create_savepoint",
    )()
    try:
        yield session
    finally:
        session.close()
        if transaction.is_active:
            transaction.rollback()
        connection.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    """A TestClient whose tracker unit is bound to the isolated session."""
    def override_tracker_unit():
        yield TrackerUnitOfWork(db_session)

    app.dependency_overrides[get_tracker_unit] = override_tracker_unit
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_tracker_unit, None)


def _new_application(client: TestClient) -> str:
    job = client.post("/jobs", json={"title": "Backend Engineer", "company": "ApplyPilot"})
    assert job.status_code == 201, job.text
    created = client.post("/applications", json={"job_id": job.json()["id"]})
    assert created.status_code == 201, created.text
    return created.json()["id"]


def _unique_key(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# Full document flow
# ---------------------------------------------------------------------------

def test_full_document_flow(client: TestClient) -> None:
    create = client.post("/documents", json={"doc_type": "resume", "name": "Primary resume"})
    assert create.status_code == 201, create.text
    document_id = create.json()["id"]

    v1 = client.post(f"/documents/{document_id}/versions", json={"content": "resume v1"})
    v2 = client.post(
        f"/documents/{document_id}/versions", json={"content_json": {"b": 2, "a": 1}}
    )
    assert v1.status_code == 201 and v2.status_code == 201
    assert v1.json()["version_number"] == 1
    assert v2.json()["version_number"] == 2
    v1_id, v2_id = v1.json()["id"], v2.json()["id"]
    v1_checksum, v2_checksum = v1.json()["checksum"], v2.json()["checksum"]

    versions = client.get(f"/documents/{document_id}/versions")
    assert [v["version_number"] for v in versions.json()] == [1, 2]

    archived = client.post(f"/documents/{document_id}/archive")
    assert archived.status_code == 200 and archived.json()["is_archived"] is True
    # Archived documents are excluded from default reads but readable by ID.
    assert document_id not in [d["id"] for d in client.get("/documents").json()]
    assert client.get(f"/documents/{document_id}").status_code == 200

    application_id = _new_application(client)
    # Attach the older version with a higher display_order to prove ordering, then newer.
    older = client.post(
        f"/applications/{application_id}/documents",
        json={"document_version_id": v1_id, "role": "resume", "display_order": 1},
    )
    newer = client.post(
        f"/applications/{application_id}/documents",
        json={"document_version_id": v2_id, "role": "resume", "display_order": 0},
    )
    assert older.status_code == 201 and newer.status_code == 201

    listed = client.get(f"/applications/{application_id}/documents").json()
    # Deterministic order by display_order: newer (0) before older (1).
    assert [a["document_version_id"] for a in listed] == [v2_id, v1_id]
    assert [a["version_number"] for a in listed] == [2, 1]
    assert [a["checksum"] for a in listed] == [v2_checksum, v1_checksum]
    for entry in listed:
        assert entry["document_id"] == document_id
    # The prior attachment was not mutated by attaching a newer version.
    assert older.json()["document_version_id"] == v1_id


# ---------------------------------------------------------------------------
# Full answer flow
# ---------------------------------------------------------------------------

def test_full_answer_flow(client: TestClient) -> None:
    key = _unique_key("why_us")
    answer = client.post(
        "/answers",
        json={"question_key": key, "question_text": "Why us?", "answer_text": "Original"},
    )
    assert answer.status_code == 201, answer.text
    answer_id = answer.json()["id"]

    app_a = _new_application(client)
    sourced = client.post(
        f"/applications/{app_a}/answers", json={"answer_library_id": answer_id}
    )
    assert sourced.status_code == 201
    assert sourced.json()["answer_text"] == "Original"
    assert sourced.json()["question_key"] == key

    # Edit the library answer; the existing snapshot must be unchanged.
    patched = client.patch(f"/answers/{answer_id}", json={"answer_text": "Rewritten"})
    assert patched.status_code == 200 and patched.json()["answer_text"] == "Rewritten"
    snapshots = client.get(f"/applications/{app_a}/answers").json()
    assert snapshots[0]["answer_text"] == "Original"

    # Archive the library answer; it may still seed a snapshot by ID (into a new application).
    # Sourcing copies the library's CURRENT text, so the new snapshot reflects the edit.
    assert client.post(f"/answers/{answer_id}/archive").status_code == 200
    app_b = _new_application(client)
    sourced_again = client.post(
        f"/applications/{app_b}/answers", json={"answer_library_id": answer_id}
    )
    assert sourced_again.status_code == 201
    assert sourced_again.json()["answer_text"] == "Rewritten"

    # An unsourced manual snapshot carries no provenance.
    manual = client.post(
        f"/applications/{app_b}/answers",
        json={
            "question_key": _unique_key("start_date"),
            "question_text": "Start date?",
            "answer_text": "Immediately",
        },
    )
    assert manual.status_code == 201
    assert manual.json()["answer_library_id"] is None


# ---------------------------------------------------------------------------
# Packet read model
# ---------------------------------------------------------------------------

def test_packet_read_model_projects_m5_and_m2_review(client: TestClient) -> None:
    document_id = client.post(
        "/documents", json={"doc_type": "resume", "name": "Resume"}
    ).json()["id"]
    version = client.post(
        f"/documents/{document_id}/versions", json={"content": "body"}
    ).json()
    answer_id = client.post(
        "/answers",
        json={"question_key": _unique_key("q"), "question_text": "Q?", "answer_text": "A"},
    ).json()["id"]

    application_id = _new_application(client)
    client.post(
        f"/applications/{application_id}/documents",
        json={"document_version_id": version["id"], "role": "resume", "display_order": 0},
    )
    client.post(f"/applications/{application_id}/answers", json={"answer_library_id": answer_id})
    review = client.post(
        f"/applications/{application_id}/packet-reviews",
        json={"decision": "approved", "reviewed_by": "reviewer"},
    )
    assert review.status_code == 201

    packet = client.get(f"/applications/{application_id}/packet")
    assert packet.status_code == 200
    body = packet.json()
    assert body["application"]["id"] == application_id
    assert len(body["documents"]) == 1
    assert body["documents"][0]["version_number"] == version["version_number"]
    assert body["documents"][0]["checksum"] == version["checksum"]
    assert len(body["answers"]) == 1
    assert body["answers"][0]["answer_text"] == "A"
    assert body["latest_packet_review"]["id"] == review.json()["id"]


def test_packet_read_model_empty_collections(client: TestClient) -> None:
    application_id = _new_application(client)

    body = client.get(f"/applications/{application_id}/packet").json()
    assert body["documents"] == []
    assert body["answers"] == []
    assert body["latest_packet_review"] is None


def test_review_summary_remains_unchanged_alongside_packet(client: TestClient) -> None:
    application_id = _new_application(client)
    review = client.post(
        f"/applications/{application_id}/packet-reviews",
        json={"decision": "approved", "reviewed_by": "reviewer"},
    )
    assert review.status_code == 201

    summary = client.get(f"/applications/{application_id}/review-summary")
    assert summary.status_code == 200
    # The packet reuses the same M2 review evidence without altering the M2 route.
    assert summary.json()["latest_packet_review"]["id"] == review.json()["id"]
    packet = client.get(f"/applications/{application_id}/packet")
    assert packet.json()["latest_packet_review"]["id"] == review.json()["id"]


# ---------------------------------------------------------------------------
# Error paths: 400 / 404 / 409
# ---------------------------------------------------------------------------

def test_document_and_version_error_paths(client: TestClient) -> None:
    assert client.post("/documents", json={"doc_type": "banana", "name": "x"}).status_code == 400
    assert client.post("/documents", json={"doc_type": "resume", "name": "   "}).status_code == 400
    assert client.post(
        "/documents", json={"doc_type": "resume", "name": "x" * 257}
    ).status_code == 400

    document_id = client.post(
        "/documents", json={"doc_type": "other", "name": "Doc"}
    ).json()["id"]
    # Missing payload on a version is a 400.
    assert client.post(f"/documents/{document_id}/versions", json={}).status_code == 400

    missing = uuid.uuid4()
    assert client.get(f"/documents/{missing}").status_code == 404
    assert client.get(f"/documents/{missing}/versions").status_code == 404
    assert client.get(f"/document-versions/{missing}").status_code == 404
    assert client.post(f"/documents/{missing}/archive").status_code == 404


def test_answer_error_paths(client: TestClient) -> None:
    key = _unique_key("dup")
    assert client.post(
        "/answers", json={"question_key": key, "question_text": "Q", "answer_text": "A"}
    ).status_code == 201
    # Duplicate active key conflicts.
    assert client.post(
        "/answers", json={"question_key": key, "question_text": "Q2", "answer_text": "A2"}
    ).status_code == 409
    # Blank key is a 400.
    assert client.post(
        "/answers", json={"question_key": "  ", "question_text": "Q", "answer_text": "A"}
    ).status_code == 400
    assert client.post(
        "/answers",
        json={"question_key": "x" * 257, "question_text": "Q", "answer_text": "A"},
    ).status_code == 400

    answers = client.get("/answers").json()
    answer_id = next(a["id"] for a in answers if a["question_key"] == key)
    # Empty patch is a 400; missing answer is a 404.
    assert client.patch(f"/answers/{answer_id}", json={}).status_code == 400
    assert client.patch(f"/answers/{uuid.uuid4()}", json={"answer_text": "x"}).status_code == 404


def test_attachment_error_paths(client: TestClient) -> None:
    application_id = _new_application(client)
    document_id = client.post(
        "/documents", json={"doc_type": "resume", "name": "Resume"}
    ).json()["id"]
    version_id = client.post(
        f"/documents/{document_id}/versions", json={"content": "body"}
    ).json()["id"]

    # Missing application -> 404.
    assert client.post(
        f"/applications/{uuid.uuid4()}/documents",
        json={"document_version_id": version_id, "role": "resume", "display_order": 0},
    ).status_code == 404
    # Missing version -> 400 (invalid reference).
    assert client.post(
        f"/applications/{application_id}/documents",
        json={"document_version_id": str(uuid.uuid4()), "role": "resume", "display_order": 0},
    ).status_code == 400
    # Invalid role and negative order -> 400.
    assert client.post(
        f"/applications/{application_id}/documents",
        json={"document_version_id": version_id, "role": "banana", "display_order": 0},
    ).status_code == 400
    assert client.post(
        f"/applications/{application_id}/documents",
        json={"document_version_id": version_id, "role": "resume", "display_order": -1},
    ).status_code == 400
    assert client.post(
        f"/applications/{application_id}/documents",
        json={
            "document_version_id": version_id,
            "role": "resume",
            "display_order": 0,
            "actor": "x" * 65,
        },
    ).status_code == 400

    first = client.post(
        f"/applications/{application_id}/documents",
        json={"document_version_id": version_id, "role": "resume", "display_order": 0},
    )
    assert first.status_code == 201
    # Duplicate exact attachment -> 409.
    assert client.post(
        f"/applications/{application_id}/documents",
        json={"document_version_id": version_id, "role": "resume", "display_order": 3},
    ).status_code == 409

    assert client.get(f"/applications/{uuid.uuid4()}/documents").status_code == 404


def test_answer_snapshot_error_paths(client: TestClient) -> None:
    application_id = _new_application(client)
    answer_id = client.post(
        "/answers",
        json={"question_key": _unique_key("k"), "question_text": "Q", "answer_text": "A"},
    ).json()["id"]

    # Missing application -> 404.
    assert client.post(
        f"/applications/{uuid.uuid4()}/answers", json={"answer_library_id": answer_id}
    ).status_code == 404
    # Mixed mode -> 400.
    assert client.post(
        f"/applications/{application_id}/answers",
        json={"answer_library_id": answer_id, "answer_text": "x"},
    ).status_code == 400
    # Incomplete manual mode -> 400.
    assert client.post(
        f"/applications/{application_id}/answers", json={"question_key": "only_key"}
    ).status_code == 400

    key = _unique_key("dup")
    assert client.post(
        f"/applications/{application_id}/answers",
        json={"question_key": key, "question_text": "Q", "answer_text": "A"},
    ).status_code == 201
    # Duplicate per-application question_key -> 409.
    assert client.post(
        f"/applications/{application_id}/answers",
        json={"question_key": key, "question_text": "Q2", "answer_text": "A2"},
    ).status_code == 409

    assert client.get(f"/applications/{uuid.uuid4()}/answers").status_code == 404
    assert client.get(f"/applications/{uuid.uuid4()}/packet").status_code == 404
