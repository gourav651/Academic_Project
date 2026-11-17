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

IMPORTANT: In the "source_code" field, provide ONLY the Python code. Do NOT wrap the JSON response in markdown code blocks."""

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
        cleaned = text.strip()
        # 1. Strip markdown fences if wrapping the JSON
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
            cleaned = re.sub(r"\n?```$", "", cleaned)

        # 2. Try standard json.loads
        try:
            data = json.loads(cleaned)
            code = data.get("source_code", "")
            code = re.sub(r"^```[a-zA-Z]*\n?", "", code.strip())
            code = re.sub(r"\n?```$", "", code.strip())
            return {
                "filename": data.get("filename", "solution.py"),
                "source_code": code,
                "dependencies": data.get("dependencies", []),
                "implementation_summary": data.get("implementation_summary", ""),
                "functions_implemented": data.get("functions_implemented", [])
            }
        except Exception:
            pass

        # 3. Robust Regex Extraction
        # Extract filename
        fn_match = re.search(r'["\']filename["\']\s*:\s*["\']([^"\']+)["\']', text)
        filename = fn_match.group(1) if fn_match else "solution.py"

        # Extract source_code when model outputs raw triple quotes
        code_match = re.search(r'["\']source_code["\']\s*:\s*(?:"""|\'\'\'|")([\s\S]*?)(?:"""|\'\'\'|")\s*,\s*["\']', text)
        if code_match:
            code = code_match.group(1).strip()
        else:
            py_block = re.search(r'```(?:python|py)\n([\s\S]*?)\n```', text)
            if py_block:
                code = py_block.group(1).strip()
            else:
                code_start = re.search(r'(?:def\s+|class\s+|import\s+|from\s+)', text)
                if code_start:
                    raw_code = text[code_start.start():]
                    raw_code = re.split(r'(?:"""|\'\'\'|")\s*,\s*["\'](?:dependencies|implementation_summary|functions_implemented)', raw_code)[0]
                    code = raw_code.strip()
                else:
                    code = text.strip()

        # Clean any accidental outer markdown fences
        code = re.sub(r"^```[a-zA-Z]*\n?", "", code.strip())
        code = re.sub(r"\n?```$", "", code.strip())

        return {
            "filename": filename,
            "source_code": code,
            "dependencies": [],
            "implementation_summary": "Extracted from generator output",
            "functions_implemented": []
        }
