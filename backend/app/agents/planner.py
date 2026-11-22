import json
import re
from typing import Dict, Any, Optional
from app.services.ollama_service import OllamaService
from app.core.logging_config import logger

import json
import re
from typing import Dict, Any, Optional
from app.services.ollama_service import OllamaService
from app.core.logging_config import logger

PLANNER_SYSTEM_PROMPT = """You are an expert software engineering planner in an autonomous software development framework.
Your task is to analyze programming requirements and quickly produce a clear, concise implementation plan in natural English sentences and points.
Do NOT output raw JSON or code blocks. Write natural, clear, professional English.

Format your response strictly using these sections:

PROBLEM UNDERSTANDING:
Write 1-2 clear, direct sentences in normal English summarizing what the program should do.

IMPLEMENTATION STEPS:
1. Step Title: Clear explanation of what this step does.
2. Step Title: Clear explanation of what this step does.
3. Step Title: Clear explanation of what this step does.

KEY CONSIDERATIONS & EDGE CASES:
- Clear sentence describing an edge case or important validation.
- Clear sentence describing another consideration.
"""

class PlannerAgent:
    def __init__(self, ollama_service: OllamaService):
        self.ollama = ollama_service
        self.name = "Planner Agent"

    async def execute(self, requirement: str, model: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Analyzing requirement: {requirement[:80]}...")
        prompt = f"""Analyze the following programming requirement and produce a structured implementation plan:

REQUIREMENT:
{requirement}

Write your plan in natural English using the section headers: PROBLEM UNDERSTANDING, IMPLEMENTATION STEPS (numbered 1, 2, 3), and KEY CONSIDERATIONS & EDGE CASES. Do NOT output JSON."""

        try:
            raw_response = await self.ollama.generate(prompt, PLANNER_SYSTEM_PROMPT, model, num_predict=450)
            plan = self._parse_plan(raw_response)
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

    def _parse_plan(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned).strip()

        # Check if response is already valid JSON (e.g. from mock or test)
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            try:
                data = json.loads(match.group())
                if isinstance(data, dict) and "problem_understanding" in data:
                    # Sanitize if nested JSON was returned
                    pu = data.get("problem_understanding", "")
                    if isinstance(pu, str) and (pu.startswith("{") or "problem_understanding" in pu):
                        data["problem_understanding"] = self._clean_sentence(pu)
                    return data
            except json.JSONDecodeError:
                pass

        # Extract structured sections from plain English output
        pu_match = re.search(
            r'PROBLEM\s+UNDERSTANDING:?\s*([\s\S]*?)(?=(?:IMPLEMENTATION\s+STEPS|KEY\s+CONSIDERATIONS|EDGE\s+CASES|\Z))',
            cleaned,
            re.IGNORECASE
        )
        problem_understanding = self._clean_sentence(pu_match.group(1)) if pu_match else ""

        # Extract implementation steps
        steps_match = re.search(
            r'IMPLEMENTATION\s+STEPS:?\s*([\s\S]*?)(?=(?:KEY\s+CONSIDERATIONS|EDGE\s+CASES|\Z))',
            cleaned,
            re.IGNORECASE
        )
        steps_text = steps_match.group(1).strip() if steps_match else ""

        steps = []
        if steps_text:
            step_items = re.findall(
                r'(?:^|\n)\s*(\d+)[\.\)]\s*(.*?)(?=(?:\n\s*\d+[\.\)]|\n\s*[A-Z\s]{4,}:|\Z))',
                steps_text,
                re.DOTALL
            )
            for num, item_str in step_items:
                item_str = self._clean_sentence(item_str)
                if not item_str:
                    continue
                if ":" in item_str:
                    desc, details = item_str.split(":", 1)
                    steps.append({
                        "step": int(num),
                        "description": desc.strip(),
                        "details": details.strip()
                    })
                else:
                    steps.append({
                        "step": int(num),
                        "description": f"Step {num}",
                        "details": item_str
                    })

        # Extract edge cases / considerations
        edge_match = re.search(
            r'(?:KEY\s+CONSIDERATIONS\s*(?:&\s*EDGE\s+CASES)?|EDGE\s+CASES):?\s*([\s\S]*?)$',
            cleaned,
            re.IGNORECASE
        )
        edge_text = edge_match.group(1).strip() if edge_match else ""
        edge_cases = []
        if edge_text:
            for line in edge_text.splitlines():
                cleaned_line = self._clean_sentence(line.lstrip("-*•0123456789. "))
                if cleaned_line and len(cleaned_line) > 3:
                    edge_cases.append(cleaned_line)

        # Fallback if text didn't follow section markers
        if not problem_understanding:
            lines = [self._clean_sentence(line) for line in cleaned.splitlines() if line.strip() and not line.strip().startswith("#")]
            problem_understanding = lines[0] if lines else "Implement requested software specification."

        if not steps:
            steps = [{"step": 1, "description": "Implement solution", "details": problem_understanding}]

        return {
            "problem_understanding": problem_understanding,
            "functional_requirements": [problem_understanding],
            "technical_constraints": ["Python 3 standard libraries"],
            "implementation_plan": steps,
            "required_functions": [],
            "expected_behavior": "Executes logic as requested",
            "edge_cases": edge_cases or ["Validate input types", "Handle boundary conditions"],
            "estimated_complexity": "medium"
        }

    def _clean_sentence(self, text: str) -> str:
        if not text:
            return ""
        s = text.strip()
        # Remove any JSON artifacts
        s = re.sub(r'```(?:json)?', '', s)
        s = re.sub(r'^\s*\{.*?"problem_understanding"\s*:\s*"?', '', s, flags=re.DOTALL)
        s = re.sub(r'["`{}\[\]]+', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def _parse_json(self, text: str) -> Dict[str, Any]:
        """Backward-compatible alias for _parse_plan."""
        return self._parse_plan(text)
