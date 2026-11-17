# REST API Documentation

Base URL: `http://localhost:8000/api`
Interactive Swagger UI: `http://localhost:8000/docs`

---

## 1. System Health & Models

### `GET /api/health`
Returns connection status of Ollama, Docker engine, active model, and service version.

**Response**:
```json
{
  "status": "healthy",
  "ollama_connected": true,
  "ollama_error": null,
  "docker_available": true,
  "docker_error": null,
  "model": "qwen2.5-coder:1.5b",
  "version": "1.0.0"
}
```

### `GET /api/models`
Lists all local Ollama models installed on the machine.

### `POST /api/models/select`
Switches the active model for all agents.

**Request**:
```json
{ "model": "qwen2.5-coder:1.5b" }
```

---

## 2. Autonomous Multi-Agent Workflow

### `POST /api/workflow/start`
Triggers the full 6-agent LangGraph workflow.

**Request**:
```json
{
  "requirement": "Write a thread-safe LRU Cache in Python with get and put methods.",
  "project_id": "optional-uuid",
  "model": "optional-model-name"
}
```

**Response**:
```json
{
  "task_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "running",
  "message": "Workflow started successfully"
}
```

### `GET /api/workflow/{task_id}`
Retrieves state, outputs, code, plan, review findings, test results, and logs for a task.

### `GET /api/workflow/{task_id}/events`
Server-Sent Events (SSE) streaming live logs and agent state changes in real time.

---

## 3. Dedicated Agent & Tool Endpoints

- `POST /api/generate`: Direct invocation of Planner & Code Generator pipeline.
- `POST /api/review`: AST parser + Ruff linter + Code Reviewer agent.
- `POST /api/test`: Test Generator agent + Pytest execution runner.
- `POST /api/execute`: Runs code inside isolated Docker container sandbox.
- `POST /api/debug`: Debugger agent diagnosis and corrected code generation.

---

## 4. Governance & Versioning

- `GET /api/governance/{task_id}`: Audit logs, agent executions, and approvals for a task.
- `POST /api/approvals/{task_id}`: Record human approval or rejection of code changes.
- `GET /api/history`: Recent workflow runs.
- `GET /api/stats`: Quantitative empirical metrics across all 5 research dimensions.
- `GET /api/projects`: List projects.
- `POST /api/projects`: Create project.
- `GET /api/versions/{project_id}`: List project code versions.
- `POST /api/versions/{project_id}/rollback`: Roll back to a previous code version.
