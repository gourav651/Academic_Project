from fastapi import APIRouter
from app.services.ollama_service import ollama_service
from app.services.execution_service import execution_service
from app.schemas.responses import HealthResponse

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
async def check_system_health():
    """Health check for Ollama, Docker container engine, and backend services."""
    ollama_status = await ollama_service.check_connection()
    docker_status = execution_service.check_available()
    
    return HealthResponse(
        status="healthy",
        ollama_connected=ollama_status.get("connected", False),
        ollama_error=ollama_status.get("error"),
        docker_available=docker_status.get("available", False),
        docker_error=docker_status.get("error"),
        model=ollama_service.model,
        version="1.0.0"
    )
