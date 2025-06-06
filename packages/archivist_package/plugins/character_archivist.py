"""
Character Archivist Plugin for the Archivist Package.

This plugin provides psychological-relational profiling and character archiving tools.
"""
from typing import Dict, Any
import logging
from core.packages.plugin_system.plugin_interface import (
    ServicePlugin, PluginManifest, ServiceEndpoint, UIComponent
)
from core.packages.archivist_package.components.character_archivist_pipeline import (
    parse_chat_log, emotion_mapping, build_profile, recommend_fmt, generate_report
)
from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# FastAPI router for plugin endpoints
router = APIRouter()

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Placeholder for real authentication logic
    if not credentials or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise Exception("Invalid or missing authentication token")
    # Optionally, validate token here
    return {"token": credentials.credentials}

@router.post("/api/character-archivist/profile")
async def api_profile(request: Request, user=Depends(get_current_user)):
    data = await request.json()
    chat_log = data.get("chat_log", "")
    messages = parse_chat_log(chat_log)
    messages = emotion_mapping(messages)
    profile = build_profile(messages)
    return JSONResponse(profile)

@router.post("/api/character-archivist/fmt")
async def api_fmt(request: Request, user=Depends(get_current_user)):
    data = await request.json()
    chat_log = data.get("chat_log", "")
    stage = data.get("stage", "initial")
    messages = parse_chat_log(chat_log)
    messages = emotion_mapping(messages)
    profile = build_profile(messages)
    fmt = recommend_fmt(profile, stage)
    return JSONResponse(fmt)

@router.post("/api/character-archivist/report")
async def api_report(request: Request, user=Depends(get_current_user)):
    data = await request.json()
    chat_log = data.get("chat_log", "")
    messages = parse_chat_log(chat_log)
    messages = emotion_mapping(messages)
    profile = build_profile(messages)
    report = generate_report(profile, messages)
    return JSONResponse({"report": report})

class CharacterArchivistPlugin(ServicePlugin):
    """
    Character Archivist Plugin implementation for the Archivist Package.
    Implements the Character Archivist Knowledge Base and Profiling Pipeline.
    """
    def __init__(self):
        self.initialized = False
        self.config = {}
        self.knowledge_base = None
    def get_manifest(self) -> PluginManifest:
        return PluginManifest(
            id="character_archivist",
            name="Character Archivist",
            version="1.0.0",
            description="Psychological-relational profiling and archiving system for digital characters.",
            endpoints=[
                ServiceEndpoint(
                    path="/api/character-archivist/profile",
                    method="POST",
                    description="Generate a psychological character profile from chat logs.",
                    auth_required=True
                ),
                ServiceEndpoint(
                    path="/api/character-archivist/fmt",
                    method="POST",
                    description="Recommend Format (FMT) for next interaction stage.",
                    auth_required=True
                ),
                ServiceEndpoint(
                    path="/api/character-archivist/report",
                    method="POST",
                    description="Generate a review report for a character's relationship path.",
                    auth_required=True
                ),
            ],
            ui_components=[
                UIComponent(
                    name="CharacterArchivistDashboard",
                    type="react",
                    path="/components/character_archivist/dashboard",
                    description="Dashboard for character profiling and archiving."
                ),
                UIComponent(
                    name="ProfileViewer",
                    type="react",
                    path="/components/character_archivist/profile_viewer",
                    description="View and analyze character profiles."
                ),
            ],
            dependencies=["rag_system", "ai_council"],
        )
    def initialize(self, config: Dict[str, Any]) -> bool:
        self.config = config
        # Register API router if running in FastAPI context
        try:
            from fastapi import FastAPI
            app = config.get("fastapi_app")
            if isinstance(app, FastAPI):
                app.include_router(router)
        except Exception as e:
            logger.warning(f"Could not register FastAPI router: {e}")
        self.initialized = True
        logger.info("Character Archivist plugin initialized.")
        return True
    def shutdown(self) -> bool:
        self.initialized = False
        logger.info("Character Archivist plugin shut down.")
        return True
    def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy" if self.initialized else "unhealthy", "initialized": self.initialized}
