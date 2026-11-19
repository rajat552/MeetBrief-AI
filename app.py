"""
MeetBrief AI — FastAPI Server & Safe SSE Streaming API
"""

import json
from typing import Dict, Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from backend.agent import MeetBriefOrchestrator
from backend.config import settings
from backend.models import ManualMeetingRequest

app = FastAPI(
    title="MeetBrief AI — Autonomous Meeting Intelligence API",
    version="0.1.0",
    description="High-performance meeting intelligence powered by Bifrost AI Gateway, Tavily Search, and LangGraph multi-agent orchestration."
)

# CORS Middleware for modern SPA frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CalendarDateRequest(BaseModel):
    date: str


@app.get("/api/health")
async def health_check():
    """
    Health check endpoint returning system status, Bifrost gateway connectivity,
    and active environment configuration.
    """
    orchestrator = MeetBriefOrchestrator()
    gw_status = await orchestrator.gateway.check_health()

    return {
        "status": "healthy",
        "service": "MeetBrief AI",
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
        "gateway": {
            "mode": gw_status.mode,
            "is_healthy": gw_status.is_healthy,
            "endpoint": gw_status.endpoint,
            "reason": gw_status.reason,
            "available_models": gw_status.available_models
        },
        "research_provider": "Tavily Search API (Configured)" if settings.is_tavily_configured() else "Tavily (Unconfigured)"
    }


@app.post("/api/briefings/generate")
async def generate_briefing(request: ManualMeetingRequest):
    """
    Primary API Endpoint: Generates a Scannable One-Page Executive Dossier
    from manual meeting inputs using Safe Server-Sent Events (SSE).
    """
    try:
        orchestrator = MeetBriefOrchestrator()
        return StreamingResponse(
            orchestrator.execute_stream(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/briefings/calendar")
async def calendar_sync(date_req: CalendarDateRequest):
    """
    Secondary / Optional Endpoint: Calendar Sync.
    If calendar integration is not configured, yields a graceful fallback notice
    directing the user to the primary manual input workflow.
    """
    async def calendar_fallback_stream():
        # Inform the frontend that calendar integration is unavailable
        event_payload = {
            "type": "calendar_status",
            "status": "unavailable",
            "message": "Google Calendar integration is currently unconfigured. Please use the primary Manual Input form for instant briefing generation."
        }
        yield f"event: calendar_status\ndata: {json.dumps(event_payload)}\n\n"

    return StreamingResponse(
        calendar_fallback_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache"}
    )


# Serve built UI static files in single-server deployment
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

UI_DIST_DIR = os.path.join(os.path.dirname(__file__), "ui", "dist")
if os.path.exists(UI_DIST_DIR):
    assets_dir = os.path.join(UI_DIST_DIR, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Do not intercept /api routes
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")
        file_path = os.path.join(UI_DIST_DIR, full_path)
        html_headers = {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }
        if full_path and os.path.exists(file_path) and os.path.isfile(file_path):
            headers = html_headers if file_path.endswith(".html") else None
            return FileResponse(file_path, headers=headers)
        return FileResponse(os.path.join(UI_DIST_DIR, "index.html"), headers=html_headers)


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 60)
    print(" 🚀 MeetBrief AI — Autonomous Meeting Intelligence")
    print(f" 👉 Access Web UI at:  http://localhost:{settings.PORT}")
    print(f" 👉 Direct URL:        http://127.0.0.1:{settings.PORT}")
    print("=" * 60 + "\n")
    uvicorn.run("app:app", host=settings.HOST, port=settings.PORT, reload=True)
