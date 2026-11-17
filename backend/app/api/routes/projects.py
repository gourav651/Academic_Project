import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database.session import get_db
from app.database.models import Project, WorkflowRun, CodeVersion
from app.schemas.requests import CreateProjectRequest
from app.services.version_service import version_service

router = APIRouter()

@router.get("/projects")
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all user projects."""
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat() if p.updated_at else None
        }
        for p in projects
    ]

@router.post("/projects")
async def create_project(req: CreateProjectRequest, db: AsyncSession = Depends(get_db)):
    """Create a new project workspace."""
    project = Project(
        id=str(uuid.uuid4()),
        name=req.name,
        description=req.description or "",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat()
    }

@router.get("/projects/{project_id}")
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get project details, runs, and code versions."""
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    runs_res = await db.execute(
        select(WorkflowRun)
        .where(WorkflowRun.project_id == project_id)
        .order_by(WorkflowRun.started_at.desc())
    )
    runs = runs_res.scalars().all()

    versions = await version_service.get_versions(db, project_id)

    return {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
        "workflow_runs": [
            {
                "task_id": r.task_id,
                "workflow_status": r.workflow_status,
                "requirement": r.user_requirement[:120],
                "started_at": r.started_at.isoformat(),
                "completed_at": r.completed_at.isoformat() if r.completed_at else None
            }
            for r in runs
        ],
        "versions": [
            {
                "version_number": v.version_number,
                "change_summary": v.change_summary,
                "created_at": v.created_at.isoformat()
            }
            for v in versions
        ]
    }

@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a project and all associated runs and versions."""
    res = await db.execute(select(Project).where(Project.id == project_id))
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await db.execute(delete(Project).where(Project.id == project_id))
    await db.commit()
    return {"success": True, "message": f"Project '{project.name}' deleted"}

@router.get("/versions/{project_id}")
async def list_versions(project_id: str, db: AsyncSession = Depends(get_db)):
    """List code versions for rollback."""
    versions = await version_service.get_versions(db, project_id)
    return [
        {
            "id": v.id,
            "version_number": v.version_number,
            "source_code": v.source_code,
            "change_summary": v.change_summary,
            "created_at": v.created_at.isoformat()
        }
        for v in versions
    ]

@router.post("/versions/{project_id}/rollback")
async def rollback_version(project_id: str, body: dict, db: AsyncSession = Depends(get_db)):
    """Roll back code to a previous version."""
    version_num = body.get("version_number")
    if not version_num:
        raise HTTPException(status_code=400, detail="version_number is required")
    try:
        code = await version_service.rollback_to_version(db, project_id, int(version_num))
        # Save as new version recording rollback
        new_ver = await version_service.save_version(
            db, project_id, code, f"Rolled back to version {version_num}"
        )
        return {
            "success": True,
            "restored_version": version_num,
            "new_version": new_ver.version_number,
            "source_code": code
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
