import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.models import CodeVersion
from app.core.logging_config import logger

class VersionService:
    async def save_version(self, db: AsyncSession, project_id: Optional[str], code: str, summary: str) -> CodeVersion:
        """Create and persist a new immutable version snapshot."""
        version_number = 1
        if project_id:
            result = await db.execute(
                select(CodeVersion)
                .where(CodeVersion.project_id == project_id)
                .order_by(CodeVersion.version_number.desc())
                .limit(1)
            )
            last_version = result.scalar_one_or_none()
            if last_version:
                version_number = last_version.version_number + 1

        new_version = CodeVersion(
            id=str(uuid.uuid4()),
            project_id=project_id,
            version_number=version_number,
            source_code=code,
            created_at=datetime.utcnow(),
            change_summary=summary
        )
        db.add(new_version)
        await db.commit()
        await db.refresh(new_version)
        logger.info(f"Saved version {version_number} for project {project_id}")
        return new_version

    async def get_versions(self, db: AsyncSession, project_id: str) -> List[CodeVersion]:
        """Fetch all versions of a project in descending order."""
        result = await db.execute(
            select(CodeVersion)
            .where(CodeVersion.project_id == project_id)
            .order_by(CodeVersion.version_number.desc())
        )
        return list(result.scalars().all())

    async def rollback_to_version(self, db: AsyncSession, project_id: str, version_number: int) -> str:
        """Retrieve code for a specific version number to restore."""
        result = await db.execute(
            select(CodeVersion)
            .where(CodeVersion.project_id == project_id, CodeVersion.version_number == version_number)
        )
        ver = result.scalar_one_or_none()
        if not ver:
            raise ValueError(f"Version {version_number} does not exist for project {project_id}")
        return ver.source_code

version_service = VersionService()
