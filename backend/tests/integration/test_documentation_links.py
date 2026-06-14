from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def _read_repo_file(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_root_readme_reviewer_entry_points_exist() -> None:
    readme = _read_repo_file("README.md")
    expected_paths = [
        "docs/capstone/README.md",
        "docs/capstone/mvp-status.md",
        "docs/capstone/dashboard-demo-flow.md",
        "docs/capstone/m1-demo-review-checklist.md",
        "docs/architecture/current-data-model.md",
        "docs/architecture/database-implementation-roadmap.md",
        "docs/contracts/database-schema-contract.md",
        "docs/diagrams/README.md",
        "docs/diagrams/database-schema.md",
        "docs/devops/codespaces.md",
        "docs/team/README.md",
        "docs/architecture/locked-plan.md",
    ]

    for relative_path in expected_paths:
        assert f"`{relative_path}`" in readme
        assert (REPO_ROOT / relative_path).is_file()


def test_capstone_index_entries_exist() -> None:
    capstone_index = _read_repo_file("docs/capstone/README.md")
    expected_paths = [
        "mvp-status.md",
        "dashboard-demo-flow.md",
        "m1-demo-review-checklist.md",
        "process.md",
        "phase-2-ideas.md",
    ]

    for relative_path in expected_paths:
        assert f"`{relative_path}`" in capstone_index
        assert (REPO_ROOT / "docs" / "capstone" / relative_path).is_file()
