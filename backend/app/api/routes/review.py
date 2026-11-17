from fastapi import APIRouter
from app.schemas.requests import ReviewCodeRequest
from app.services.ollama_service import ollama_service
from app.services.analysis_service import analysis_service
from app.agents.code_reviewer import CodeReviewerAgent

router = APIRouter()

@router.post("/review")
async def review_code_directly(req: ReviewCodeRequest):
    """Direct invocation of Code Reviewer Agent combining deterministic tools and LLM."""
    agent = CodeReviewerAgent(ollama_service, analysis_service)
    result = await agent.execute(req.code, req.model)
    return result
