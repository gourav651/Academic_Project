import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database.session import get_db
from app.database.models import AuditLog, ApprovalRecord, WorkflowRun, AgentExecution, TestResult, DebuggingHistory
from app.schemas.requests import ApprovalRequest

router = APIRouter()

@router.get("/governance/{task_id}")
async def get_governance_audit(task_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve full decision traceability, audit logs, and approval records for a task."""
    run_res = await db.execute(select(WorkflowRun).where((WorkflowRun.task_id == task_id) | (WorkflowRun.id == task_id)))
    run = run_res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Workflow task not found")

    logs_res = await db.execute(
        select(AuditLog).where(AuditLog.workflow_run_id == run.id).order_by(AuditLog.timestamp.asc())
    )
    logs = logs_res.scalars().all()

    approvals_res = await db.execute(
        select(ApprovalRecord).where(ApprovalRecord.workflow_run_id == run.id).order_by(ApprovalRecord.created_at.desc())
    )
    approvals = approvals_res.scalars().all()

    agent_execs_res = await db.execute(
        select(AgentExecution).where(AgentExecution.workflow_run_id == run.id).order_by(AgentExecution.started_at.asc())
    )
    agent_execs = agent_execs_res.scalars().all()

    return {
        "task_id": task_id,
        "workflow_status": run.workflow_status,
        "user_requirement": run.user_requirement,
        "started_at": run.started_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "audit_logs": [
            {
                "agent_name": l.agent_name,
                "action": l.action,
                "status": l.status,
                "duration": l.duration,
                "output_summary": l.output_summary,
                "error_info": l.error_info,
                "timestamp": l.timestamp.isoformat()
            }
            for l in logs
        ],
        "approvals": [
            {
                "id": a.id,
                "agent_name": a.agent_name,
                "approval_status": a.approval_status,
                "decision_reason": a.decision_reason,
                "decided_at": a.decided_at.isoformat() if a.decided_at else None,
                "created_at": a.created_at.isoformat()
            }
            for a in approvals
        ],
        "agent_executions": [
            {
                "agent_name": e.agent_name,
                "status": e.status,
                "duration_seconds": e.duration_seconds,
                "output_summary": e.output_summary,
                "error_info": e.error_info
            }
            for e in agent_execs
        ]
    }

@router.post("/approvals/{task_id}")
async def submit_approval_decision(task_id: str, req: ApprovalRequest, db: AsyncSession = Depends(get_db)):
    """Human-in-the-loop checkpoint: approve or reject proposed modifications."""
    run_res = await db.execute(select(WorkflowRun).where((WorkflowRun.task_id == task_id) | (WorkflowRun.id == task_id)))
    run = run_res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Workflow task not found")

    status_val = "approved" if req.approved else "rejected"
    approval = ApprovalRecord(
        id=str(uuid.uuid4()),
        workflow_run_id=run.id,
        agent_name="human_operator",
        approval_status=status_val,
        decision_reason=req.reason or ("Approved by user" if req.approved else "Rejected by user"),
        decided_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    db.add(approval)
    await db.commit()

    return {
        "success": True,
        "task_id": task_id,
        "approval_status": status_val,
        "message": f"Modification {status_val} successfully recorded."
    }

@router.get("/history")
async def get_workflow_history(db: AsyncSession = Depends(get_db)):
    """Retrieve history of all automated engineering runs."""
    res = await db.execute(select(WorkflowRun).order_by(WorkflowRun.started_at.desc()).limit(100))
    runs = res.scalars().all()
    return [
        {
            "task_id": r.task_id,
            "project_id": r.project_id,
            "requirement": r.user_requirement[:120],
            "workflow_status": r.workflow_status,
            "started_at": r.started_at.isoformat(),
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            "error_message": r.error_message
        }
        for r in runs
    ]

@router.get("/stats")
async def get_evaluation_metrics(db: AsyncSession = Depends(get_db)):
    """Compute measurable empirical metrics across all 5 research dimensions."""
    total_runs = (await db.execute(select(func.count(WorkflowRun.id)))).scalar() or 0
    completed_runs = (await db.execute(select(func.count(WorkflowRun.id)).where(WorkflowRun.workflow_status == "completed"))).scalar() or 0
    failed_runs = (await db.execute(select(func.count(WorkflowRun.id)).where(WorkflowRun.workflow_status == "failed"))).scalar() or 0

    total_agent_calls = (await db.execute(select(func.count(AgentExecution.id)))).scalar() or 0
    avg_duration = (await db.execute(select(func.avg(AgentExecution.duration_seconds)))).scalar() or 0.0

    total_tests_run = (await db.execute(select(func.sum(TestResult.total_tests)))).scalar() or 0
    passed_tests = (await db.execute(select(func.sum(TestResult.passed_tests)))).scalar() or 0

    total_debugging_attempts = (await db.execute(select(func.count(DebuggingHistory.id)))).scalar() or 0
    successful_debugs = (await db.execute(select(func.count(DebuggingHistory.id)).where(DebuggingHistory.validation_passed == True))).scalar() or 0

    total_approvals = (await db.execute(select(func.count(ApprovalRecord.id)).where(ApprovalRecord.approval_status == "approved"))).scalar() or 0
    total_rejections = (await db.execute(select(func.count(ApprovalRecord.id)).where(ApprovalRecord.approval_status == "rejected"))).scalar() or 0

    success_rate = round((completed_runs / total_runs * 100), 1) if total_runs > 0 else 0.0
    test_pass_rate = round((passed_tests / total_tests_run * 100), 1) if total_tests_run > 0 else 0.0

    return {
        "efficiency": {
            "total_workflow_runs": total_runs,
            "total_agent_executions": total_agent_calls,
            "average_agent_duration_seconds": round(avg_duration, 2)
        },
        "accuracy": {
            "test_pass_rate_percent": test_pass_rate,
            "total_tests_executed": total_tests_run,
            "passed_tests": passed_tests
        },
        "resilience": {
            "workflow_success_rate_percent": success_rate,
            "total_debugging_attempts": total_debugging_attempts,
            "successful_debug_recoveries": successful_debugs,
            "failed_workflows": failed_runs
        },
        "governance": {
            "recorded_audit_logs": (await db.execute(select(func.count(AuditLog.id)))).scalar() or 0,
            "approved_modifications": total_approvals,
            "rejected_modifications": total_rejections
        },
        "scalability": {
            "integrated_specialized_agents": 6,
            "orchestrator_architecture": "LangGraph StateGraph"
        }
    }
