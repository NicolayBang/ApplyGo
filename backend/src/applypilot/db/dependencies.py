"""Database-backed API dependencies."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from applypilot.db.session import SessionLocal
from applypilot.db.tracker import Tracker


class TrackerUnitOfWork:
    """Small request-scoped unit of work around the application tracker."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.tracker = Tracker(session)

    def commit(self) -> None:
        self.session.commit()

    def refresh(self, instance: object) -> None:
        self.session.refresh(instance)


def get_session() -> Generator[Session]:
    """Yield a database session for one request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_tracker_unit() -> Generator[TrackerUnitOfWork]:
    """Yield a tracker unit of work for API handlers."""
    session = SessionLocal()
    try:
        yield TrackerUnitOfWork(session)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
