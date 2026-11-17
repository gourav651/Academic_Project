from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class HealthResponse(BaseModel):
    status: str
    ollama_connected: bool
    ollama_error: Optional[str] = None
    docker_available: bool
    docker_error: Optional[str] = None
    model: str
    version: str

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    created_at: str
    updated_at: Optional[str] = None

class WorkflowStatusResponse(BaseModel):
    task_id: str
    status: str
    workflow_status: Optional[str] = None
    agent_statuses: Dict[str, Any] = {}
    generated_code: Optional[str] = None
    implementation_plan: Optional[Dict[str, Any]] = None
    review_results: Optional[Dict[str, Any]] = None
    test_results: Optional[Dict[str, Any]] = None
    execution_results: Optional[Dict[str, Any]] = None
    explanation: Optional[Dict[str, Any]] = None
    debugging_attempts: int = 0
    execution_logs: List[str] = []
    error_details: Optional[str] = None

class ModelInfoResponse(BaseModel):
    name: str
    size: Optional[int] = 0
    modified_at: Optional[str] = None

class ModelsListResponse(BaseModel):
    connected: bool
    models: List[Dict[str, Any]] = []
    current_model: str
    error: Optional[str] = None
