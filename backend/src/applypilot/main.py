"""Application entrypoint for the ApplyPilot backend scaffold."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from applypilot.api.router import api_router
from applypilot.config.settings import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev-only: restrict in production via settings
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
