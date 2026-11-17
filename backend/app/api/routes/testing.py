from fastapi import APIRouter
from app.schemas.requests import TestCodeRequest
from app.services.ollama_service import ollama_service
from app.services.testing_service import testing_service
from app.agents.test_generator import TestGeneratorAgent

router = APIRouter()

@router.post("/test")
async def generate_and_run_unit_tests(req: TestCodeRequest):
    """Direct invocation of Test Generator Agent and test runner."""
    agent = TestGeneratorAgent(ollama_service)
    gen_result = await agent.execute(req.code, req.model)

    if not gen_result["success"]:
        return {
            "success": False,
            "error": gen_result.get("error", "Test generation failed")
        }

    test_code = gen_result["result"].get("test_code", "")
    run_result = await testing_service.run_tests(test_code, req.code)

    return {
        "success": True,
        "test_code": test_code,
        "test_cases": gen_result["result"].get("test_cases", []),
        "coverage_areas": gen_result["result"].get("coverage_areas", []),
        "test_strategy": gen_result["result"].get("test_strategy"),
        "run_result": run_result
    }
