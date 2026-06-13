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

# Build allowed origins. In Codespaces, cross-origin fetch from the forwarded
# frontend port requires the exact origin + credentials, since wildcard is
# incompatible with credentials. Outside Codespaces we fall back to localhost.
_codespace = os.environ.get("CODESPACE_NAME", "")
_cs_domain = os.environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "app.github.dev")

if _codespace:
    _allowed_origins = [
        f"https://{_codespace}-4173.{_cs_domain}",
        f"https://{_codespace}-3000.{_cs_domain}",
        f"https://{_codespace}-5173.{_cs_domain}",
        "http://localhost:4173",
        "http://localhost:3000",
        "http://localhost:5173",
    ]
else:
    _allowed_origins = ["*"]

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
