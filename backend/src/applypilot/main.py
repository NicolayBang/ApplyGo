"""Application entrypoint for the ApplyPilot backend scaffold."""

from fastapi import FastAPI

from applypilot.api.router import api_router
from applypilot.config.settings import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(api_router)
