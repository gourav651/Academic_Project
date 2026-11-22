import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from datetime import datetime
from sqlalchemy import update
from app.core.config import settings
from app.core.logging_config import logger
from app.database.init_db import init_db
from app.database.session import AsyncSessionLocal
from app.database.models import WorkflowRun
from app.api.routes import (
    health,
    models,
    projects,
    workflow,
    generation,
    debugging,
    execution,
    review,
    testing,
    governance
)

os.makedirs("logs", exist_ok=True)

# Path to built frontend
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIST = os.path.join(BASE_DIR, "frontend", "dist")
INDEX_HTML_PATH = os.path.join(FRONTEND_DIST, "index.html")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite tables on startup
    await init_db()
    # Mark any previously interrupted runs as failed
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(
                update(WorkflowRun)
                .where(WorkflowRun.workflow_status == "running")
                .values(
                    workflow_status="failed",
                    error_message="Workflow execution interrupted by server restart. Please trigger a new run.",
                    completed_at=datetime.utcnow()
                )
            )
            await db.commit()
    except Exception as e:
        logger.warning(f"Could not clean up interrupted runs: {e}")
    logger.info("Autonomous Software Engineering Framework Database initialized.")
    yield
    logger.info("Application shutting down.")

app = FastAPI(
    title="Agentic AI Autonomous Software Engineering Framework",
    description="Multi-agent AI framework for automated code generation, deterministic review, isolated execution, unit testing, self-debugging, and explainability with human governance.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router, prefix="/api", tags=["System Health"])
app.include_router(models.router, prefix="/api", tags=["Model Management"])
app.include_router(projects.router, prefix="/api", tags=["Projects & Code Versions"])
app.include_router(workflow.router, prefix="/api", tags=["Autonomous Workflow"])
app.include_router(generation.router, prefix="/api", tags=["Code Generation"])
app.include_router(review.router, prefix="/api", tags=["Code Review & Static Analysis"])
app.include_router(testing.router, prefix="/api", tags=["Automated Testing"])
app.include_router(execution.router, prefix="/api", tags=["Isolated Execution"])
app.include_router(debugging.router, prefix="/api", tags=["Automated Debugging"])
app.include_router(governance.router, prefix="/api", tags=["Governance & Metrics"])

# Mount static assets if frontend/dist exists
if os.path.exists(os.path.join(FRONTEND_DIST, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

@app.get("/api")
@app.get("/api/")
async def api_root():
    return {
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs",
        "endpoints": {
            "health": "/api/health",
            "models": "/api/models",
            "projects": "/api/projects",
            "history": "/api/history",
            "stats": "/api/stats",
            "workflow": "/api/workflow/start"
        }
    }

@app.get("/")
async def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept and os.path.exists(INDEX_HTML_PATH):
        return FileResponse(INDEX_HTML_PATH)
    return {
        "framework": "Agentic AI Autonomous Software Engineering Framework",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/api/health"
    }

@app.get("/{full_path:path}")
async def serve_spa_or_static(full_path: str, request: Request):
    """Serve SPA routes and static root assets, preventing 404 on browser navigation."""
    if full_path.startswith("api/") or full_path == "api":
        return JSONResponse(status_code=404, content={"detail": f"API endpoint '/{full_path}' not found"})
    if full_path.startswith("docs") or full_path.startswith("redoc") or full_path.startswith("openapi.json"):
        return JSONResponse(status_code=404, content={"detail": "Not found"})

    # Check if a static file directly in frontend/dist exists (e.g. favicon.svg)
    candidate_file = os.path.join(FRONTEND_DIST, full_path)
    if os.path.isfile(candidate_file):
        return FileResponse(candidate_file)

    # Return index.html for SPA client-side routing
    if os.path.exists(INDEX_HTML_PATH):
        return FileResponse(INDEX_HTML_PATH)

    return JSONResponse(status_code=404, content={"detail": f"Path '/{full_path}' not found"})
