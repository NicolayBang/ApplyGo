"""Top-level API router for milestone-1 scaffolding."""

from fastapi import APIRouter

router = APIRouter()
api_router = APIRouter()


@router.get("/health", tags=["system"])
def healthcheck() -> dict[str, str]:
    """Return a basic health response for local bootstrapping."""
    return {"status": "ok", "service": "applypilot"}


api_router.include_router(router)
