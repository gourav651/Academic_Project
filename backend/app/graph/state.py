from typing import TypedDict, Optional, List, Dict, Any

class AgentStatusInfo(TypedDict, total=False):
    name: str
    status: str            # "pending" | "running" | "completed" | "failed" | "skipped"
    started_at: Optional[str]
    completed_at: Optional[str]
    duration: Optional[float]
    output_summary: Optional[str]
    error: Optional[str]

class WorkflowState(TypedDict, total=False):
    # Identifiers
    task_id: str
    project_id: Optional[str]
    model: Optional[str]
    
    # Requirement
    user_requirement: str
    
    # Agent 1: Planner
    implementation_plan: Optional[Dict[str, Any]]
    
    # Agent 2: Code Generator
    generated_code: Optional[str]
    code_filename: Optional[str]
    code_version: int
    
    # Agent 3: Code Reviewer & Static Analysis
    review_results: Optional[Dict[str, Any]]
    static_analysis_results: Optional[Dict[str, Any]]
    
    # Agent 5: Test Generator & Testing Service
    test_code: Optional[str]
    test_results: Optional[Dict[str, Any]]
    
    # Code Execution Engine
    execution_results: Optional[Dict[str, Any]]
    has_errors: bool
    error_details: Optional[str]
    
    # Agent 4: Debugger Agent
    debugging_attempts: int
    max_debug_attempts: int
    corrected_code: Optional[str]
    debugging_history: List[Dict[str, Any]]
    
    # Human in the loop / Approval
    approval_status: Optional[str]  # "pending" | "approved" | "rejected"
    
    # Agent 6: Explainer Agent
    explanation: Optional[Dict[str, Any]]
    
    # Workflow Tracing & Observability
    agent_statuses: Dict[str, Dict[str, Any]]
    workflow_status: str            # "pending" | "running" | "completed" | "failed" | "awaiting_approval"
    execution_logs: List[str]
