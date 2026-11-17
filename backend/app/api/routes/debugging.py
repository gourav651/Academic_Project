from fastapi import APIRouter
from app.schemas.requests import DebugCodeRequest
from app.services.ollama_service import ollama_service
from app.services.analysis_service import analysis_service
from app.agents.debugger import DebuggerAgent
from app.core.config import settings

router = APIRouter()

@router.post("/debug")
async def debug_code_directly(req: DebugCodeRequest):
    """Direct invocation of Debugger Agent for error diagnosis and correction."""
    agent = DebuggerAgent(ollama_service, analysis_service, settings.max_debug_attempts)
    result = await agent.execute(req.code, req.error, 1, req.model)

    if not result["success"]:
        return {
            "success": False,
            "error": result.get("error", "Debugging operation failed")
        }

    res_data = result.get("result", {})
    return {
        "success": True,
        "original_code": req.code,
        "corrected_code": res_data.get("corrected_code"),
        "root_cause": res_data.get("root_cause"),
        "error_category": res_data.get("error_category"),
        "explanation": res_data.get("explanation"),
        "changes_made": res_data.get("changes_made", []),
        "confidence": res_data.get("confidence"),
        "syntax_valid": res_data.get("syntax_valid", False),
        "prevention_tips": res_data.get("prevention_tips", [])
    }
