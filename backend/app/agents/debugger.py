import json
import re
from typing import Dict, Any, Optional, List
from app.services.ollama_service import OllamaService
from app.services.analysis_service import AnalysisService
from app.core.logging_config import logger

DEBUGGER_SYSTEM_PROMPT = """You are an expert Python debugging engineer in an autonomous framework.
Your task is to analyze failing Python code, tracebacks, and error outputs, determine the exact root cause, and produce an accurate, minimal, working correction.

You must ALWAYS respond with ONLY a valid JSON object matching this schema:
{
  "root_cause": "Detailed explanation of why the failure occurred",
  "error_category": "syntax|runtime|logical|type|import|index|key|attribute",
  "corrected_code": "# complete corrected Python code with the fix applied",
  "changes_made": [
    {
      "line": 15,
      "original": "code snippet before",
      "corrected": "code snippet after",
      "reason": "Why this change fixes the error"
    }
  ],
  "explanation": "Human-readable explanation of the fix and why it works",
  "confidence": "high|medium|low",
  "prevention_tips": ["Best practice tip 1", "Best practice tip 2"]
}
Do NOT include markdown backticks or commentary outside the JSON."""

class DebuggerAgent:
    def __init__(self, ollama_service: OllamaService, analysis_service: AnalysisService, max_attempts: int = 3):
        self.ollama = ollama_service
        self.analysis = analysis_service
        self.max_attempts = max_attempts
        self.name = "Debugger Agent"
        self._history: List[Dict[str, Any]] = []

    async def execute(self, code: str, error: str, attempt: int = 1, model: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Initiating debugging attempt {attempt}/{self.max_attempts}...")
        
        if attempt > self.max_attempts:
            return {
                "success": False,
                "error": f"Max debugging attempts ({self.max_attempts}) reached without resolution.",
                "result": None
            }

        # Snapshot for rollback
        self._history.append({
            "attempt": attempt,
            "code": code,
            "error": error
        })

        # Static analysis on failing code
        ast_result = await self.analysis.run_ast_analysis(code)

        prompt = f"""Debug the following failing Python code.

FAILING CODE:
```python
{code}
```

ERROR / TRACEBACK:
{error}

STATIC ANALYSIS FINDINGS:
{json.dumps(ast_result.get('findings', []))}

ATTEMPT NUMBER: {attempt} of {self.max_attempts}

Identify the root cause and provide the FULL corrected code. Respond with strictly valid JSON matching the schema."""

        try:
            raw_response = await self.ollama.generate(prompt, DEBUGGER_SYSTEM_PROMPT, model)
            result = self._parse_json(raw_response)
            
            # Deterministic AST validation on proposed correction
            corrected_code = result.get('corrected_code', '')
            if corrected_code:
                validation = await self.analysis.run_ast_analysis(corrected_code)
                result['syntax_valid'] = validation.get('syntax_valid', False)
                result['ast_findings'] = validation.get('findings', [])

            logger.info(f"[{self.name}] Attempt {attempt} finished: confidence={result.get('confidence')}, syntax_valid={result.get('syntax_valid')}")
            return {
                "success": True,
                "result": result,
                "attempt": attempt,
                "history": self._history,
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
            logger.error(f"[{self.name}] Debugging error: {e}")
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
        code = code_match.group(1) if code_match else ""
        return {
            "root_cause": "Extracted from debugger output",
            "error_category": "runtime",
            "corrected_code": code,
            "changes_made": [],
            "explanation": text[:300],
            "confidence": "medium",
            "prevention_tips": []
        }

    def get_history(self) -> List[Dict[str, Any]]:
        return self._history

    def rollback_to_attempt(self, attempt_number: int) -> str:
        for entry in self._history:
            if entry["attempt"] == attempt_number:
                return entry["code"]
        raise ValueError(f"No history recorded for attempt {attempt_number}")
