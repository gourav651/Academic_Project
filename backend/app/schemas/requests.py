from pydantic import BaseModel, Field
from typing import Optional

class GenerateCodeRequest(BaseModel):
    requirement: str = Field(..., description="Natural language software requirements")
    project_id: Optional[str] = Field(None, description="Optional project ID to associate with")
    model: Optional[str] = Field(None, description="Optional specific Ollama model to use")

class DebugCodeRequest(BaseModel):
    code: str = Field(..., description="Python source code containing errors")
    error: str = Field(..., description="Traceback or description of the error")
    project_id: Optional[str] = Field(None, description="Optional project ID")
    model: Optional[str] = Field(None, description="Optional Ollama model")

class ExecuteCodeRequest(BaseModel):
    code: str = Field(..., description="Python source code to execute in isolation")
    timeout: Optional[int] = Field(None, description="Execution timeout in seconds")

class ReviewCodeRequest(BaseModel):
    code: str = Field(..., description="Python source code to review")
    model: Optional[str] = Field(None, description="Optional Ollama model")

class TestCodeRequest(BaseModel):
    code: str = Field(..., description="Python source code to generate unit tests for")
    model: Optional[str] = Field(None, description="Optional Ollama model")

class ExplainCodeRequest(BaseModel):
    code: str = Field(..., description="Python source code to explain")
    context: Optional[str] = Field(None, description="Optional context about debugging or testing")
    model: Optional[str] = Field(None, description="Optional Ollama model")

class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field("", description="Project description")

class ApprovalRequest(BaseModel):
    approved: bool = Field(..., description="Whether the proposed code correction is approved")
    reason: Optional[str] = Field(None, description="Reason for approval or rejection")

class ModelSelectRequest(BaseModel):
    model: str = Field(..., description="Ollama model name to set as default")
