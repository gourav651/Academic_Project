import json
import re
from typing import Dict, Any, Optional
from app.services.ollama_service import OllamaService
from app.core.logging_config import logger

PLANNER_SYSTEM_PROMPT = """You are an expert software engineering planner in an autonomous software development framework.
Your task is to analyze programming requirements and quickly produce a clear, concise implementation plan.
Keep descriptions short and direct (1-2 sentences each). Do not write lengthy essays.

You must ALWAYS respond with ONLY a valid JSON object matching this exact schema:
{
  "problem_understanding": "Clear 1-sentence summary of the goal",
  "functional_requirements": ["Requirement 1", "Requirement 2"],
  "technical_constraints": ["Constraint 1"],
  "implementation_plan": [
    {"step": 1, "description": "Step title", "details": "Brief implementation details"}
  ],
  "required_functions": [
    {"name": "function_name", "purpose": "What it does", "inputs": "parameter list", "outputs": "return type"}
  ],
  "expected_behavior": "Expected behavior on standard inputs",
  "edge_cases": ["Edge case 1", "Edge case 2"],
  "estimated_complexity": "low|medium|high"
}
Do NOT include markdown backticks or commentary outside the JSON."""

class PlannerAgent:
    def __init__(self, ollama_service: OllamaService):
        self.ollama = ollama_service
        self.name = "Planner Agent"

    async def execute(self, requirement: str, model: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Analyzing requirement: {requirement[:80]}...")
        prompt = f"""Analyze the following programming requirement and produce a structured implementation plan:

REQUIREMENT:
{requirement}

Respond with strictly valid JSON matching the schema."""

        try:
            raw_response = await self.ollama.generate(prompt, PLANNER_SYSTEM_PROMPT, model, num_predict=350)
            plan = self._parse_json(raw_response)
            logger.info(f"[{self.name}] Plan generated with {len(plan.get('implementation_plan', []))} steps")
            return {
                "success": True,
                "plan": plan,
                "raw_response": raw_response
            }
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"[{self.name}] LLM unavailable: {e}")
            return {
                "success": False,
                "error": str(e),
                "plan": None
            }
        except Exception as e:
            logger.error(f"[{self.name}] Unexpected error: {e}")
            return {
                "success": False,
                "error": str(e),
                "plan": None
            }

    def _parse_json(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {
            "problem_understanding": text[:300],
            "functional_requirements": [text[:100]],
            "technical_constraints": ["Python 3 standard libraries"],
            "implementation_plan": [{"step": 1, "description": "Implement solution", "details": text}],
            "required_functions": [],
            "expected_behavior": "Executes logic as requested",
            "edge_cases": ["Empty input", "Invalid types"],
            "estimated_complexity": "medium"
        }
