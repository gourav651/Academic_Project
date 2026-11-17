from fastapi import APIRouter, HTTPException
from app.services.ollama_service import ollama_service
from app.schemas.requests import ModelSelectRequest
from app.schemas.responses import ModelsListResponse

router = APIRouter()

@router.get("/models", response_model=ModelsListResponse)
async def list_available_models():
    """List all installed local models in the Ollama instance."""
    status = await ollama_service.check_connection()
    if not status.get("connected"):
        return ModelsListResponse(
            connected=False,
            models=[],
            current_model=ollama_service.model,
            error=status.get("error")
        )
    
    models = await ollama_service.list_models()
    return ModelsListResponse(
        connected=True,
        models=models,
        current_model=ollama_service.model,
        error=None
    )

@router.post("/models/select")
async def select_active_model(req: ModelSelectRequest):
    """Set the currently active model for all agents."""
    if not req.model or not req.model.strip():
        raise HTTPException(status_code=400, detail="Model name must not be empty")
    ollama_service.set_model(req.model.strip())
    return {
        "success": True,
        "message": f"Active model set to '{req.model.strip()}'",
        "current_model": req.model.strip()
    }
