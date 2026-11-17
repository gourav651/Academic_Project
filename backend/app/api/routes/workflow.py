import uuid
import asyncio
import json
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import get_db, AsyncSessionLocal
from app.database.models import (
    WorkflowRun,
    AgentExecution,
    ExecutionResult,
    TestResult,
    DebuggingHistory,
    AuditLog,
    CodeVersion,
    GeneratedCode
)
from app.graph.state import WorkflowState
from app.graph.workflow import autonomous_graph
from app.schemas.requests import GenerateCodeRequest
from app.core.config import settings
from app.core.logging_config import logger

router = APIRouter()

# In-memory workflow state cache for fast polling and SSE stream
active_workflows: Dict[str, Dict[str, Any]] = {}

@router.post("/workflow/start")
async def start_autonomous_workflow(req: GenerateCodeRequest, db: AsyncSession = Depends(get_db)):
    """Initialize and trigger the full 6-agent autonomous engineering workflow."""
    task_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())

    workflow_run = WorkflowRun(
        id=run_id,
        project_id=req.project_id,
        task_id=task_id,
        user_requirement=req.requirement,
        workflow_status="running",
        started_at=datetime.utcnow()
    )
    db.add(workflow_run)
    await db.commit()

    initial_state: WorkflowState = {
        "task_id": task_id,
        "project_id": req.project_id,
        "model": req.model or settings.ollama_model,
        "user_requirement": req.requirement,
        "implementation_plan": None,
        "generated_code": None,
        "code_filename": "solution.py",
        "code_version": 1,
        "review_results": None,
        "static_analysis_results": None,
        "test_code": None,
        "test_results": None,
        "execution_results": None,
        "has_errors": False,
        "error_details": None,
        "debugging_attempts": 0,
        "max_debug_attempts": settings.max_debug_attempts,
        "corrected_code": None,
        "debugging_history": [],
        "approval_status": "pending",
        "explanation": None,
        "agent_statuses": {},
        "workflow_status": "running",
        "execution_logs": [f"[{datetime.utcnow().isoformat()}] Autonomous engineering workflow started for Task {task_id}"]
    }

    active_workflows[task_id] = {
        "status": "running",
        "state": initial_state,
        "run_id": run_id
    }

    # Execute workflow in background task
    asyncio.create_task(_execute_workflow_task(task_id, initial_state, run_id))

    return {
        "task_id": task_id,
        "status": "running",
        "message": "Workflow started successfully"
    }


async def _execute_workflow_task(task_id: str, initial_state: WorkflowState, run_id: str):
    """Orchestrate LangGraph execution and persist results into SQLite."""
    try:
        logger.info(f"[Workflow] Running LangGraph for Task {task_id}")
        final_state = await autonomous_graph.ainvoke(initial_state)

        workflow_status = final_state.get("workflow_status", "completed")
        active_workflows[task_id]["status"] = workflow_status
        active_workflows[task_id]["state"] = final_state

        async with AsyncSessionLocal() as db:
            res = await db.execute(select(WorkflowRun).where(WorkflowRun.id == run_id))
            run = res.scalar_one_or_none()
            if run:
                run.workflow_status = workflow_status
                run.completed_at = datetime.utcnow()
                if final_state.get("error_details"):
                    run.error_message = final_state["error_details"]

                # Persist Agent Executions & Audit Logs
                for agent_name, info in final_state.get("agent_statuses", {}).items():
                    agent_exec = AgentExecution(
                        id=str(uuid.uuid4()),
                        workflow_run_id=run.id,
                        agent_name=agent_name,
                        status=info.get("status", "completed"),
                        input_summary=final_state.get("user_requirement")[:300],
                        output_summary=info.get("output_summary"),
                        error_info=info.get("error"),
                        duration_seconds=info.get("duration")
                    )
                    db.add(agent_exec)

                    audit = AuditLog(
                        id=str(uuid.uuid4()),
                        workflow_run_id=run.id,
                        agent_name=agent_name,
                        action=f"Executed {agent_name}",
                        status=info.get("status", "completed"),
                        duration=info.get("duration"),
                        error_info=info.get("error"),
                        output_summary=info.get("output_summary")
                    )
                    db.add(audit)

                # Persist Execution Result
                exec_res = final_state.get("execution_results")
                if exec_res:
                    db.add(ExecutionResult(
                        id=str(uuid.uuid4()),
                        workflow_run_id=run.id,
                        stdout=exec_res.get("stdout", ""),
                        stderr=exec_res.get("stderr", ""),
                        return_code=exec_res.get("return_code", 0),
                        execution_time=exec_res.get("execution_time", 0.0),
                        error_traceback=exec_res.get("traceback")
                    ))

                # Persist Test Result
                test_res = final_state.get("test_results")
                if test_res:
                    db.add(TestResult(
                        id=str(uuid.uuid4()),
                        workflow_run_id=run.id,
                        test_code=final_state.get("test_code", ""),
                        total_tests=test_res.get("total_tests", 0),
                        passed_tests=test_res.get("passed_tests", 0),
                        failed_tests=test_res.get("failed_tests", 0),
                        test_output=test_res.get("test_output", "")
                    ))

                # Persist Code Version if project attached
                final_code = final_state.get("corrected_code") or final_state.get("generated_code")
                if final_code and run.project_id:
                    db.add(CodeVersion(
                        id=str(uuid.uuid4()),
                        project_id=run.project_id,
                        version_number=1,
                        source_code=final_code,
                        change_summary=f"Generated from task {task_id}"
                    ))

                await db.commit()
                logger.info(f"[Workflow] Task {task_id} data persisted to DB successfully.")

    except Exception as e:
        logger.error(f"[Workflow] Unhandled error in Task {task_id}: {e}")
        active_workflows[task_id]["status"] = "failed"
        active_workflows[task_id]["state"]["workflow_status"] = "failed"
        active_workflows[task_id]["state"]["error_details"] = str(e)
        active_workflows[task_id]["state"]["execution_logs"].append(f"[{datetime.utcnow().isoformat()}] Workflow failed with error: {str(e)}")

        async with AsyncSessionLocal() as db:
            res = await db.execute(select(WorkflowRun).where(WorkflowRun.id == run_id))
            run = res.scalar_one_or_none()
            if run:
                run.workflow_status = "failed"
                run.error_message = str(e)
                run.completed_at = datetime.utcnow()
                await db.commit()


@router.get("/workflow/{task_id}")
async def get_workflow_status(task_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve current state and output snapshots for a task with DB persistence fallback."""
    workflow = active_workflows.get(task_id)
    if workflow:
        state = workflow.get("state", {})
        return {
            "task_id": task_id,
            "status": workflow.get("status"),
            "workflow_status": state.get("workflow_status"),
            "user_requirement": state.get("user_requirement"),
            "agent_statuses": state.get("agent_statuses", {}),
            "generated_code": state.get("corrected_code") or state.get("generated_code"),
            "implementation_plan": state.get("implementation_plan"),
            "review_results": state.get("review_results"),
            "test_code": state.get("test_code"),
            "test_results": state.get("test_results"),
            "execution_results": state.get("execution_results"),
            "explanation": state.get("explanation"),
            "debugging_attempts": state.get("debugging_attempts", 0),
            "debugging_history": state.get("debugging_history", []),
            "execution_logs": state.get("execution_logs", []),
            "error_details": state.get("error_details")
        }

    # Fallback: Query SQLite database if memory cache is not present
    res = await db.execute(select(WorkflowRun).where((WorkflowRun.task_id == task_id) | (WorkflowRun.id == task_id)))
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Task not found")

    # Fetch agent execution statuses
    agent_execs_res = await db.execute(
        select(AgentExecution).where(AgentExecution.workflow_run_id == run.id)
    )
    agent_execs = agent_execs_res.scalars().all()
    agent_statuses = {}
    for ae in agent_execs:
        agent_statuses[ae.agent_name] = {
            "name": ae.agent_name,
            "status": ae.status,
            "output_summary": ae.output_summary or "",
            "error": ae.error_info or "",
            "duration": ae.duration_seconds
        }

    # Fetch generated code
    code_text = ""
    if run.project_id:
        code_res = await db.execute(
            select(GeneratedCode).where(GeneratedCode.project_id == run.project_id).order_by(GeneratedCode.created_at.desc())
        )
        code_obj = code_res.scalars().first()
        if code_obj:
            code_text = code_obj.source_code
    if not code_text:
        code_res = await db.execute(
            select(GeneratedCode).order_by(GeneratedCode.created_at.desc())
        )
        code_obj = code_res.scalars().first()
        if code_obj:
            code_text = code_obj.source_code

    # Fetch test result
    test_res = await db.execute(
        select(TestResult).where(TestResult.workflow_run_id == run.id).order_by(TestResult.created_at.desc())
    )
    test_obj = test_res.scalars().first()
    test_data = {
        "success": (test_obj.failed_tests == 0 and test_obj.total_tests > 0),
        "total_tests": test_obj.total_tests,
        "passed_tests": test_obj.passed_tests,
        "failed_tests": test_obj.failed_tests,
        "test_output": test_obj.test_output
    } if test_obj else None

    # Fetch audit logs for execution log display
    audit_res = await db.execute(
        select(AuditLog).where(AuditLog.workflow_run_id == run.id).order_by(AuditLog.timestamp.asc())
    )
    logs = [
        f"[{l.timestamp.isoformat()}] [{l.agent_name.upper()}] {l.action} ({l.status})"
        for l in audit_res.scalars().all()
    ]
    if not logs:
        logs = [f"Workflow completed for Task {task_id}"]

    return {
        "task_id": task_id,
        "status": run.workflow_status,
        "workflow_status": run.workflow_status,
        "user_requirement": run.user_requirement,
        "agent_statuses": agent_statuses,
        "generated_code": code_text,
        "implementation_plan": None,
        "review_results": None,
        "test_code": test_obj.test_code if test_obj else None,
        "test_results": test_data,
        "execution_results": None,
        "explanation": None,
        "debugging_attempts": 0,
        "debugging_history": [],
        "execution_logs": logs,
        "error_details": run.error_message
    }


@router.get("/workflow/{task_id}/events")
async def stream_workflow_events(task_id: str):
    """Server-Sent Events (SSE) endpoint to stream live agent logs and state changes to the UI."""
    async def sse_publisher():
        last_log_idx = 0
        iterations = 0
        max_iterations = 600  # 10 minutes timeout

        while iterations < max_iterations:
            workflow = active_workflows.get(task_id)
            if not workflow:
                # Check if it was already completed in DB
                async with AsyncSessionLocal() as db:
                    res = await db.execute(select(WorkflowRun).where((WorkflowRun.task_id == task_id) | (WorkflowRun.id == task_id)))
                    run = res.scalar_one_or_none()
                    if run:
                        yield f"data: {json.dumps({'type': 'status', 'workflow_status': run.workflow_status, 'agent_statuses': {}})}\n\n"
                        yield f"data: {json.dumps({'type': 'done', 'final_status': run.workflow_status})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'error', 'message': 'Workflow not found'})}\n\n"
                break

            state = workflow.get("state", {})
            logs = state.get("execution_logs", [])

            # Emit any new log lines
            if len(logs) > last_log_idx:
                for log_line in logs[last_log_idx:]:
                    yield f"data: {json.dumps({'type': 'log', 'message': log_line})}\n\n"
                last_log_idx = len(logs)

            # Emit status packet
            yield f"data: {json.dumps({'type': 'status', 'workflow_status': state.get('workflow_status'), 'agent_statuses': state.get('agent_statuses', {})})}\n\n"

            # Check completion
            if workflow.get("status") in ("completed", "failed"):
                yield f"data: {json.dumps({'type': 'done', 'final_status': workflow.get('status')})}\n\n"
                break

            await asyncio.sleep(1)
            iterations += 1

    return StreamingResponse(
        sse_publisher(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
