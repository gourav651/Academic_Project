from fastapi import APIRouter
from app.schemas.requests import GenerateCodeRequest
from app.services.ollama_service import ollama_service
from app.agents.planner import PlannerAgent
from app.agents.code_generator import CodeGeneratorAgent

router = APIRouter()

@router.post("/generate")
async def generate_code_directly(req: GenerateCodeRequest):
    """Direct invocation of Planner & Code Generator pipeline."""
    planner = PlannerAgent(ollama_service)
    code_gen = CodeGeneratorAgent(ollama_service)

    # 1. Plan
    plan_res = await planner.execute(req.requirement, req.model)
    if not plan_res["success"]:
        return {"success": False, "error": plan_res.get("error")}

    # 2. Code Gen
    code_res = await code_gen.execute(plan_res["plan"], req.requirement, req.model)
    if not code_res["success"]:
        return {"success": False, "error": code_res.get("error")}

    return {
        "success": True,
        "plan": plan_res["plan"],
        "code": code_res["result"].get("source_code"),
        "filename": code_res["result"].get("filename"),
        "dependencies": code_res["result"].get("dependencies", []),
        "implementation_summary": code_res["result"].get("implementation_summary")
    }
