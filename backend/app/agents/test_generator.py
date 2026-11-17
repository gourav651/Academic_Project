import json
import re
from typing import Dict, Any, Optional
from app.services.ollama_service import OllamaService
from app.core.logging_config import logger

TESTGEN_SYSTEM_PROMPT = """You are a senior test engineer specializing in Pytest.
Your task is to generate comprehensive, robust unit tests for the provided Python source code.

Test writing requirements:
- Import all functions directly from `solution` (e.g. `from solution import *` or explicit function names).
- Cover 3 categories:
  1. "normal": Expected valid inputs and typical workflows.
  2. "edge": Boundary conditions, zeros, empty strings, empty lists, large numbers.
  3. "invalid": Incorrect types, negative numbers where disallowed, handling exceptions using `pytest.raises(...)`.
- Include clear docstrings for every test function.
- Do NOT mock internal logic unnecessarily unless dealing with I/O or external systems.

You must ALWAYS respond with ONLY a valid JSON object matching this schema:
{
  "test_code": "import pytest\\nfrom solution import *\\n\\ndef test_sample():\\n    assert True",
  "test_cases": [
    {
      "name": "test_sample",
      "description": "Validates basic behavior",
      "category": "normal|edge|invalid"
    }
  ],
  "coverage_areas": ["function_name_1", "function_name_2"],
  "test_strategy": "Explanation of testing approach"
}
Do NOT include markdown backticks or commentary outside the JSON."""

class TestGeneratorAgent:
    __test__ = False  # Inform pytest this is an agent class, not a test suite
    def __init__(self, ollama_service: OllamaService):
        self.ollama = ollama_service
        self.name = "Test Generator Agent"

    async def execute(self, code: str, model: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Generating pytest unit test suite...")
        prompt = f"""Generate a comprehensive pytest unit test suite for the following Python code:

SOURCE CODE:
```python
{code}
```

Respond with strictly valid JSON matching the schema."""

        try:
            raw_response = await self.ollama.generate(prompt, TESTGEN_SYSTEM_PROMPT, model)
            result = self._parse_json(raw_response)
            logger.info(f"[{self.name}] Generated {len(result.get('test_cases', []))} test cases")
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
            logger.error(f"[{self.name}] Test generation error: {e}")
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

        code_match = re.search(r'```python\n([\s\S]*?)\n```', text)
        code = code_match.group(1) if code_match else "# Test suite extraction failed"
        return {
            "test_code": code,
            "test_cases": [],
            "coverage_areas": [],
            "test_strategy": "Extracted from generator output"
        }
