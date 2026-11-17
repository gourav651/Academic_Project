from fastapi import APIRouter
from app.schemas.requests import ExecuteCodeRequest
from app.services.execution_service import execution_service

router = APIRouter()

@router.post("/execute")
async def execute_code_in_sandbox(req: ExecuteCodeRequest):
    """Execute Python code in isolated Docker environment."""
    return await execution_service.execute_code(req.code, req.timeout)

@router.get("/execute/status")
async def check_execution_environment():
    """Verify Docker container availability and status."""
    return execution_service.check_available()
