import time
from datetime import datetime
from typing import Dict, Any, List
from app.agents.planner import PlannerAgent
from app.agents.code_generator import CodeGeneratorAgent
from app.agents.code_reviewer import CodeReviewerAgent
from app.agents.debugger import DebuggerAgent
from app.agents.test_generator import TestGeneratorAgent
from app.agents.explainer import ExplainerAgent
from app.services.ollama_service import ollama_service
from app.services.analysis_service import analysis_service
from app.services.execution_service import execution_service
from app.services.testing_service import testing_service
from app.graph.state import WorkflowState
from app.core.config import settings
from app.core.logging_config import logger

def _timestamp() -> str:
    return datetime.utcnow().isoformat()

def _update_status(
    state: WorkflowState,
    agent_key: str,
    status: str,
    output: str = "",
    error: str = "",
    duration: float = None
) -> Dict[str, Any]:
    statuses = dict(state.get("agent_statuses", {}))
    existing = statuses.get(agent_key, {})
    now = _timestamp()
    
    statuses[agent_key] = {
        "name": agent_key,
        "status": status,
        "started_at": existing.get("started_at") or now,
        "completed_at": now if status in ("completed", "failed", "skipped") else None,
        "duration": duration if duration is not None else existing.get("duration"),
        "output_summary": output or existing.get("output_summary", ""),
        "error": error or existing.get("error", "")
    }
    return statuses


async def planner_node(state: WorkflowState) -> WorkflowState:
    """Agent 1: Understand requirement and formulate implementation plan."""
    start_time = time.time()
    agent = PlannerAgent(ollama_service)
    statuses = _update_status(state, "planner", "running")
    logs = list(state.get("execution_logs", []))
    logs.append(f"[{_timestamp()}] [PLANNER] Analyzing user requirement...")
    
    result = await agent.execute(state["user_requirement"], state.get("model"))
    dur = round(time.time() - start_time, 2)
    
    if result["success"]:
        steps = len(result["plan"].get("implementation_plan", []))
        summary = f"Plan created: {steps} steps decomposed, complexity: {result['plan'].get('estimated_complexity', 'medium')}"
        statuses = _update_status({**state, "agent_statuses": statuses}, "planner", "completed", summary, duration=dur)
        logs.append(f"[{_timestamp()}] [PLANNER] Plan completed in {dur}s ({steps} steps).")
        return {
            **state,
            "implementation_plan": result["plan"],
            "agent_statuses": statuses,
            "execution_logs": logs
        }
    else:
        err = result.get("error", "Unknown planner error")
        statuses = _update_status({**state, "agent_statuses": statuses}, "planner", "failed", error=err, duration=dur)
        logs.append(f"[{_timestamp()}] [PLANNER] FAILED: {err}")
        return {
            **state,
            "workflow_status": "failed",
            "error_details": f"Planner failed: {err}",
            "agent_statuses": statuses,
            "execution_logs": logs
        }


async def code_generator_node(state: WorkflowState) -> WorkflowState:
    """Agent 2: Generate Python source code based on implementation plan."""
    start_time = time.time()
    agent = CodeGeneratorAgent(ollama_service)
    statuses = _update_status(state, "code_generator", "running")
    logs = list(state.get("execution_logs", []))
    logs.append(f"[{_timestamp()}] [CODE_GENERATOR] Generating Python source code...")
    
    plan = state.get("implementation_plan") or {}
    result = await agent.execute(plan, state["user_requirement"], state.get("model"))
    dur = round(time.time() - start_time, 2)
    
    if result["success"]:
        code = result["result"].get("source_code", "")
        filename = result["result"].get("filename", "solution.py")
        summary = f"Generated {filename} ({len(code.splitlines())} lines)"
        statuses = _update_status({**state, "agent_statuses": statuses}, "code_generator", "completed", summary, duration=dur)
        logs.append(f"[{_timestamp()}] [CODE_GENERATOR] Completed in {dur}s: {filename}")
        return {
            **state,
            "generated_code": code,
            "code_filename": filename,
            "code_version": 1,
            "agent_statuses": statuses,
            "execution_logs": logs
        }
    else:
        err = result.get("error", "Code generator error")
        statuses = _update_status({**state, "agent_statuses": statuses}, "code_generator", "failed", error=err, duration=dur)
        logs.append(f"[{_timestamp()}] [CODE_GENERATOR] FAILED: {err}")
        return {
            **state,
            "workflow_status": "failed",
            "error_details": f"Code generator failed: {err}",
            "agent_statuses": statuses,
            "execution_logs": logs
        }


async def code_reviewer_node(state: WorkflowState) -> WorkflowState:
    """Agent 3: Perform static analysis (AST & Ruff) and AI reasoning-based review."""
    start_time = time.time()
    agent = CodeReviewerAgent(ollama_service, analysis_service)
    statuses = _update_status(state, "code_reviewer", "running")
    logs = list(state.get("execution_logs", []))
    logs.append(f"[{_timestamp()}] [REVIEWER] Executing AST static analysis and code review...")
    
    code = state.get("corrected_code") or state.get("generated_code") or ""
    result = await agent.execute(code, state.get("model"))
    dur = round(time.time() - start_time, 2)
    
    review_data = result.get("review", {})
    findings_count = len(review_data.get("findings", []))
    summary = f"Quality: {review_data.get('overall_quality', 'unknown')}, {findings_count} findings detected"
    
    statuses = _update_status({**state, "agent_statuses": statuses}, "code_reviewer", "completed", summary, duration=dur)
    logs.append(f"[{_timestamp()}] [REVIEWER] Review complete in {dur}s ({findings_count} findings)")
    
    return {
        **state,
        "review_results": review_data,
        "static_analysis_results": review_data.get("static_analysis", {}),
        "agent_statuses": statuses,
        "execution_logs": logs
    }


async def test_generator_node(state: WorkflowState) -> WorkflowState:
    """Agent 5: Generate unit tests and execute with Pytest."""
    start_time = time.time()
    agent = TestGeneratorAgent(ollama_service)
    statuses = _update_status(state, "test_generator", "running")
    logs = list(state.get("execution_logs", []))
    logs.append(f"[{_timestamp()}] [TEST_GENERATOR] Creating pytest test suite...")
    
    code = state.get("corrected_code") or state.get("generated_code") or ""
    result = await agent.execute(code, state.get("model"))
    dur = round(time.time() - start_time, 2)
    
    if result["success"]:
        test_code = result["result"].get("test_code", "")
        cases_count = len(result["result"].get("test_cases", []))
        summary = f"Generated {cases_count} unit test cases"
        
        # Execute tests via testing_service
        test_run = None
        if test_code:
            logs.append(f"[{_timestamp()}] [TEST_GENERATOR] Running pytest validation...")
            test_run = await testing_service.run_tests(test_code, code)
            summary += f" | {test_run.get('passed_tests', 0)} passed, {test_run.get('failed_tests', 0)} failed"
        
        statuses = _update_status({**state, "agent_statuses": statuses}, "test_generator", "completed", summary, duration=dur)
        logs.append(f"[{_timestamp()}] [TEST_GENERATOR] Completed in {dur}s: {summary}")
        
        return {
            **state,
            "test_code": test_code,
            "test_results": test_run,
            "agent_statuses": statuses,
            "execution_logs": logs
        }
    else:
        err = result.get("error", "Test generation error")
        statuses = _update_status({**state, "agent_statuses": statuses}, "test_generator", "failed", error=err, duration=dur)
        logs.append(f"[{_timestamp()}] [TEST_GENERATOR] FAILED: {err}")
        return {
            **state,
            "test_code": None,
            "test_results": None,
            "agent_statuses": statuses,
            "execution_logs": logs
        }


async def execution_node(state: WorkflowState) -> WorkflowState:
    """Execute code in isolated Docker container."""
    logs = list(state.get("execution_logs", []))
    logs.append(f"[{_timestamp()}] [EXECUTION] Running code in isolated sandbox...")
    
    code = state.get("corrected_code") or state.get("generated_code") or ""
    result = await execution_service.execute_code(code)
    
    # Check if there was an execution failure (syntax error, runtime error, or test failure)
    has_errors = False
    error_details = None
    
    if not result.get("success", False) and result.get("return_code") != 0:
        # If Docker is available and container execution failed with error
        if result.get("docker_available", True):
            has_errors = True
            error_details = result.get("stderr") or result.get("error") or "Runtime error during execution"
    
    # Also check if test generator tests failed
    test_res = state.get("test_results") or {}
    if test_res.get("failed_tests", 0) > 0 and not has_errors:
        has_errors = True
        error_details = f"Unit test failures: {test_res.get('failed_tests')} test(s) failed.\nOutput:\n{test_res.get('test_output', '')}"

    status_str = "SUCCESS" if not has_errors else f"ERROR DETECTED: {error_details[:100]}"
    logs.append(f"[{_timestamp()}] [EXECUTION] Status: {status_str}")
    
    return {
        **state,
        "execution_results": result,
        "has_errors": has_errors,
        "error_details": error_details,
        "execution_logs": logs
    }


async def debugger_node(state: WorkflowState) -> WorkflowState:
    """Agent 4: Analyze error traceback, find root cause, and apply correction."""
    start_time = time.time()
    attempts = state.get("debugging_attempts", 0) + 1
    agent = DebuggerAgent(ollama_service, analysis_service, state.get("max_debug_attempts", 3))
    
    statuses = _update_status(state, "debugger", "running")
    logs = list(state.get("execution_logs", []))
    logs.append(f"[{_timestamp()}] [DEBUGGER] Starting self-debugging cycle (attempt {attempts}/{state.get('max_debug_attempts', 3)})...")
    
    code = state.get("corrected_code") or state.get("generated_code") or ""
    error = state.get("error_details") or "Runtime/Logical failure detected"
    
    result = await agent.execute(code, error, attempts, state.get("model"))
    dur = round(time.time() - start_time, 2)
    
    history = list(state.get("debugging_history", []))
    
    if result["success"]:
        res_data = result["result"]
        corrected = res_data.get("corrected_code", "")
        root_cause = res_data.get("root_cause", "Root cause identified")
        confidence = res_data.get("confidence", "medium")
        
        history.append({
            "attempt": attempts,
            "root_cause": root_cause,
            "confidence": confidence,
            "explanation": res_data.get("explanation", ""),
            "changes_made": res_data.get("changes_made", []),
            "syntax_valid": res_data.get("syntax_valid", False)
        })
        
        summary = f"Attempt {attempts}: {confidence} confidence fix proposed. Root cause: {root_cause[:80]}"
        statuses = _update_status({**state, "agent_statuses": statuses}, "debugger", "completed", summary, duration=dur)
        logs.append(f"[{_timestamp()}] [DEBUGGER] Attempt {attempts} finished in {dur}s: {summary}")
        
        return {
            **state,
            "corrected_code": corrected,
            "debugging_attempts": attempts,
            "debugging_history": history,
            "agent_statuses": statuses,
            "execution_logs": logs
        }
    else:
        err = result.get("error", "Debugging cycle failed")
        statuses = _update_status({**state, "agent_statuses": statuses}, "debugger", "failed", error=err, duration=dur)
        logs.append(f"[{_timestamp()}] [DEBUGGER] FAILED: {err}")
        return {
            **state,
            "debugging_attempts": attempts,
            "agent_statuses": statuses,
            "execution_logs": logs
        }


async def explainer_node(state: WorkflowState) -> WorkflowState:
    """Agent 6: Formulate comprehensive explainability report for the solution."""
    start_time = time.time()
    agent = ExplainerAgent(ollama_service)
    statuses = _update_status(state, "explainer", "running")
    logs = list(state.get("execution_logs", []))
    logs.append(f"[{_timestamp()}] [EXPLAINER] Generating complete transparency and explanation report...")
    
    code = state.get("corrected_code") or state.get("generated_code") or ""
    context = {
        "debugging_history": state.get("debugging_history", []),
        "test_results": state.get("test_results"),
        "review_results": state.get("review_results")
    }
    
    result = await agent.execute(code, context, state.get("model"))
    dur = round(time.time() - start_time, 2)
    
    if result["success"]:
        summary = "Comprehensive explainability report compiled"
        statuses = _update_status({**state, "agent_statuses": statuses}, "explainer", "completed", summary, duration=dur)
        logs.append(f"[{_timestamp()}] [EXPLAINER] Completed in {dur}s.")
        return {
            **state,
            "explanation": result["result"],
            "workflow_status": "completed",
            "agent_statuses": statuses,
            "execution_logs": logs
        }
    else:
        err = result.get("error", "Explainer failed")
        statuses = _update_status({**state, "agent_statuses": statuses}, "explainer", "failed", error=err, duration=dur)
        logs.append(f"[{_timestamp()}] [EXPLAINER] FAILED: {err}")
        return {
            **state,
            "explanation": None,
            "workflow_status": "completed",
            "agent_statuses": statuses,
            "execution_logs": logs
        }


def route_after_execution(state: WorkflowState) -> str:
    """Conditional router: decide whether to trigger self-debugging or finalize explanation."""
    has_errors = state.get("has_errors", False)
    attempts = state.get("debugging_attempts", 0)
    max_attempts = state.get("max_debug_attempts", 3)
    
    if has_errors and attempts < max_attempts:
        logger.info(f"[Router] Errors detected (attempts {attempts}/{max_attempts}). Routing to Debugger.")
        return "debugger"
    
    logger.info("[Router] No errors or max retry limit reached. Routing to Explainer.")
    return "explainer"


def route_after_debugger(state: WorkflowState) -> str:
    """After debugger generates a fix, route back to reviewer and execution to re-validate."""
    attempts = state.get("debugging_attempts", 0)
    max_attempts = state.get("max_debug_attempts", 3)
    
    if attempts >= max_attempts:
        logger.info("[Router] Debugger reached maximum retry limit. Routing to Explainer.")
        return "explainer"
    
    logger.info(f"[Router] Debugger completed attempt {attempts}. Re-validating code through execution.")
    return "execution"
