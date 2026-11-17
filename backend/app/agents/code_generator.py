import json
import re
from typing import Dict, Any, Optional
from app.services.ollama_service import OllamaService
from app.core.logging_config import logger

CODEGEN_SYSTEM_PROMPT = """You are an expert Python developer in an autonomous software development framework.
Your task is to convert structured implementation plans and user requirements into clean, production-ready Python code.

Coding standards:
- Adhere strictly to PEP 8 standards.
- Write informative docstrings for every function and class.
- Include explicit type hints for parameters and return types.
- Implement thorough error handling and validate input parameters.
- Handle edge cases properly.

You must ALWAYS respond with ONLY a valid JSON object matching this schema:
{
  "filename": "solution.py",
  "source_code": "# full Python code here",
  "dependencies": ["dependency1"],
  "implementation_summary": "Summary of what was implemented",
  "functions_implemented": ["function_name_1", "function_name_2"]
}
Do NOT include markdown backticks or text outside the JSON."""

class CodeGeneratorAgent:
    def __init__(self, ollama_service: OllamaService):
        self.ollama = ollama_service
        self.name = "Code Generator Agent"

    async def execute(self, plan: Dict[str, Any], requirement: str, model: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Generating Python code...")
        prompt = f"""Generate production-ready Python code fulfilling this requirement and implementation plan:

USER REQUIREMENT:
{requirement}

IMPLEMENTATION PLAN:
{json.dumps(plan, indent=2)}

Respond with strictly valid JSON matching the schema."""

        try:
            raw_response = await self.ollama.generate(prompt, CODEGEN_SYSTEM_PROMPT, model)
            result = self._parse_json(raw_response)
            logger.info(f"[{self.name}] Successfully generated code for {result.get('filename', 'solution.py')}")
            return {
                "success": True,
                "result": result,
                "raw_response": raw_response
            }
        except (ConnectionError, TimeoutError) as e:
            logger.error(f"[{self.name}] LLM unavailable: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
        except Exception as e:
            logger.error(f"[{self.name}] Error: {e}")
            return {
                "success": False,
                "error": str(e),
                "result": None
            }

    def _parse_json(self, text: str) -> Dict[str, Any]:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Fallback to extracting code blocks if LLM returned markdown
        code_match = re.search(r'```python\n([\s\S]*?)\n```', text)
        code = code_match.group(1) if code_match else text
        return {
            "filename": "solution.py",
            "source_code": code,
            "dependencies": [],
            "implementation_summary": "Extracted from generator output",
            "functions_implemented": []
        }
