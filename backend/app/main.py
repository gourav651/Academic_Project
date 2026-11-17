import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import logger
from app.database.init_db import init_db
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite tables on startup
    await init_db()
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

@app.get("/")
async def root():
    return {
        "framework": "Agentic AI Autonomous Software Engineering Framework",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/api/health"
    }
