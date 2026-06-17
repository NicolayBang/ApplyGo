"""Application entrypoint for the ApplyPilot backend scaffold."""

import os
import pathlib

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from applypilot.api.router import api_router
from applypilot.config.settings import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)

# Build explicit allowed origins. In Codespaces, cross-origin fetch from the
# forwarded frontend port requires the exact origin + credentials.
_codespace = os.environ.get("CODESPACE_NAME", "")
_cs_domain = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")
_allowed_origins = settings.allowed_cors_origins(
    codespace_name=_codespace,
    codespaces_domain=_cs_domain,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Serve the frontend from the same port so no cross-origin fetch is needed.
# Accessible at /ui/ — eliminates Codespaces port auth issues.
_frontend_dir = pathlib.Path(__file__).parent.parent.parent.parent / "frontend"
if _frontend_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
