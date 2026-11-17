import json
import asyncio
from unittest.mock import AsyncMock
from app.services.ollama_service import OllamaService
from app.services.analysis_service import AnalysisService
from app.agents.planner import PlannerAgent
from app.agents.code_generator import CodeGeneratorAgent
from app.agents.code_reviewer import CodeReviewerAgent
from app.agents.debugger import DebuggerAgent
from app.agents.test_generator import TestGeneratorAgent
from app.agents.explainer import ExplainerAgent
from app.graph.nodes import route_after_execution, route_after_debugger

def test_planner_agent():
    async def _run():
        service = OllamaService()
        service.generate = AsyncMock(return_value=json.dumps({
            "problem_understanding": "Sort integers using quicksort",
            "functional_requirements": ["Accept list", "Return sorted list"],
            "technical_constraints": ["In-place or new list"],
            "implementation_plan": [{"step": 1, "description": "Partition", "details": "Choose pivot"}],
            "required_functions": [{"name": "quicksort", "purpose": "sort", "inputs": "arr", "outputs": "list"}],
            "expected_behavior": "Sorted output",
            "edge_cases": ["Empty list"],
            "estimated_complexity": "medium"
        }))
        agent = PlannerAgent(service)
        result = await agent.execute("Implement quicksort in Python")
        assert result["success"] is True
        assert result["plan"]["problem_understanding"] == "Sort integers using quicksort"
        assert len(result["plan"]["implementation_plan"]) == 1
    asyncio.run(_run())

def test_code_generator_agent():
    async def _run():
        service = OllamaService()
        service.generate = AsyncMock(return_value=json.dumps({
            "filename": "solution.py",
            "source_code": "def quicksort(arr):\n    return sorted(arr)",
            "dependencies": [],
            "implementation_summary": "Quicksort algorithm",
            "functions_implemented": ["quicksort"]
        }))
        agent = CodeGeneratorAgent(service)
        result = await agent.execute({"plan": []}, "quicksort")
        assert result["success"] is True
        assert "quicksort" in result["result"]["source_code"]
    asyncio.run(_run())

def test_code_reviewer_agent_deterministic():
    async def _run():
        analysis_svc = AnalysisService()
        code = "def divide(a, b):\n    return a / b\n"
        ast_res = await analysis_svc.run_ast_analysis(code)
        assert ast_res["syntax_valid"] is True
        assert any(f["type"] == "missing_docstring" for f in ast_res["findings"])
    asyncio.run(_run())

def test_debugger_agent():
    async def _run():
        service = OllamaService()
        analysis_svc = AnalysisService()
        service.generate = AsyncMock(return_value=json.dumps({
            "root_cause": "Division by zero",
            "error_category": "runtime",
            "corrected_code": "def divide(a, b):\n    if b == 0: raise ValueError('Zero division')\n    return a / b",
            "changes_made": [{"line": 2, "original": "return a/b", "corrected": "guard check", "reason": "prevent zero div"}],
            "explanation": "Added zero check",
            "confidence": "high",
            "prevention_tips": ["Validate denominators"]
        }))
        agent = DebuggerAgent(service, analysis_svc, max_attempts=3)
        result = await agent.execute("def divide(a, b): return a / b", "ZeroDivisionError: division by zero", attempt=1)
        assert result["success"] is True
        assert result["result"]["confidence"] == "high"
        assert result["result"]["syntax_valid"] is True
    asyncio.run(_run())

def test_test_generator_agent():
    async def _run():
        service = OllamaService()
        service.generate = AsyncMock(return_value=json.dumps({
            "test_code": "import pytest\nfrom solution import divide\n\ndef test_divide():\n    assert divide(4, 2) == 2",
            "test_cases": [{"name": "test_divide", "description": "checks standard division", "category": "normal"}],
            "coverage_areas": ["divide"],
            "test_strategy": "Unit assertions"
        }))
        agent = TestGeneratorAgent(service)
        result = await agent.execute("def divide(a, b): return a / b")
        assert result["success"] is True
        assert len(result["result"]["test_cases"]) == 1
    asyncio.run(_run())

def test_explainer_agent():
    async def _run():
        service = OllamaService()
        service.generate = AsyncMock(return_value=json.dumps({
            "overview": "Division helper function",
            "functions": [{"name": "divide", "purpose": "divides numbers", "parameters": "a, b", "returns": "float", "complexity": "O(1)", "explanation": "Simple arithmetic"}],
            "execution_flow": "Receives a and b, calculates quotient",
            "key_concepts": ["Arithmetic"],
            "debugging_explanation": "None",
            "test_explanation": "Verified with test",
            "improvement_recommendations": []
        }))
        agent = ExplainerAgent(service)
        result = await agent.execute("def divide(a, b): return a / b")
        assert result["success"] is True
        assert result["result"]["overview"] == "Division helper function"
    asyncio.run(_run())

def test_routing_logic():
    # Route to debugger when error detected and attempts < max
    state_with_error = {"has_errors": True, "debugging_attempts": 1, "max_debug_attempts": 3}
    assert route_after_execution(state_with_error) == "debugger"

    # Route to explainer when no errors
    state_clean = {"has_errors": False, "debugging_attempts": 0, "max_debug_attempts": 3}
    assert route_after_execution(state_clean) == "explainer"

    # Route to explainer when max attempts reached
    state_maxed = {"has_errors": True, "debugging_attempts": 3, "max_debug_attempts": 3}
    assert route_after_execution(state_maxed) == "explainer"

    # Debugger loopback
    assert route_after_debugger({"debugging_attempts": 1, "max_debug_attempts": 3}) == "execution"
    assert route_after_debugger({"debugging_attempts": 3, "max_debug_attempts": 3}) == "explainer"
