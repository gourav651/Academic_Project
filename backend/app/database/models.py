from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.database.session import Base

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    workflow_runs: Mapped[List["WorkflowRun"]] = relationship("WorkflowRun", back_populates="project", cascade="all, delete-orphan")
    code_versions: Mapped[List["CodeVersion"]] = relationship("CodeVersion", back_populates="project", cascade="all, delete-orphan")

class GeneratedCode(Base):
    __tablename__ = "generated_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    filename: Mapped[str] = mapped_column(String(255), default="solution.py")
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="python")
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class CodeVersion(Base):
    __tablename__ = "code_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    change_summary: Mapped[str] = mapped_column(Text, default="")

    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="code_versions")

class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    task_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    user_requirement: Mapped[str] = mapped_column(Text, nullable=False)
    workflow_status: Mapped[str] = mapped_column(String(50), default="pending")
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="workflow_runs")
    agent_executions: Mapped[List["AgentExecution"]] = relationship("AgentExecution", back_populates="workflow_run", cascade="all, delete-orphan")
    execution_results: Mapped[List["ExecutionResult"]] = relationship("ExecutionResult", back_populates="workflow_run", cascade="all, delete-orphan")
    test_results: Mapped[List["TestResult"]] = relationship("TestResult", back_populates="workflow_run", cascade="all, delete-orphan")
    debugging_history: Mapped[List["DebuggingHistory"]] = relationship("DebuggingHistory", back_populates="workflow_run", cascade="all, delete-orphan")
    audit_logs: Mapped[List["AuditLog"]] = relationship("AuditLog", back_populates="workflow_run", cascade="all, delete-orphan")
    approval_records: Mapped[List["ApprovalRecord"]] = relationship("ApprovalRecord", back_populates="workflow_run", cascade="all, delete-orphan")

class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    input_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    error_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    workflow_run: Mapped["WorkflowRun"] = relationship("WorkflowRun", back_populates="agent_executions")

class ExecutionResult(Base):
    __tablename__ = "execution_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=True)
    stdout: Mapped[str] = mapped_column(Text, default="")
    stderr: Mapped[str] = mapped_column(Text, default="")
    return_code: Mapped[int] = mapped_column(Integer, default=0)
    execution_time: Mapped[float] = mapped_column(Float, default=0.0)
    error_traceback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workflow_run: Mapped[Optional["WorkflowRun"]] = relationship("WorkflowRun", back_populates="execution_results")

class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=True)
    test_code: Mapped[str] = mapped_column(Text, default="")
    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    passed_tests: Mapped[int] = mapped_column(Integer, default=0)
    failed_tests: Mapped[int] = mapped_column(Integer, default=0)
    test_output: Mapped[str] = mapped_column(Text, default="")
    coverage_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workflow_run: Mapped[Optional["WorkflowRun"]] = relationship("WorkflowRun", back_populates="test_results")

class DebuggingHistory(Base):
    __tablename__ = "debugging_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    error_description: Mapped[str] = mapped_column(Text, default="")
    root_cause: Mapped[str] = mapped_column(Text, default="")
    corrected_code: Mapped[str] = mapped_column(Text, default="")
    correction_explanation: Mapped[str] = mapped_column(Text, default="")
    validation_passed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workflow_run: Mapped[Optional["WorkflowRun"]] = relationship("WorkflowRun", back_populates="debugging_history")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    input_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="completed")
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    code_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    workflow_run: Mapped[Optional["WorkflowRun"]] = relationship("WorkflowRun", back_populates="audit_logs")

class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_run_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    proposed_change: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    previous_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    new_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approval_status: Mapped[str] = mapped_column(String(50), default="pending")
    decision_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    workflow_run: Mapped[Optional["WorkflowRun"]] = relationship("WorkflowRun", back_populates="approval_records")
