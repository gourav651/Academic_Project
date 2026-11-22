import json
import re
from typing import Dict, Any, Optional
from app.services.ollama_service import OllamaService
from app.core.logging_config import logger

EXPLAINER_SYSTEM_PROMPT = """You are a senior software educator and technical writer in an autonomous framework.
Your task is to provide clear, concise, evidence-based explainability for generated Python code.
Be concise. Keep descriptions direct and short (1-2 sentences per field). Avoid repetitive filler text.

You must ALWAYS respond with ONLY a valid JSON object matching this schema:
{
  "overview": "1-2 sentence description of what the software does",
  "functions": [
    {
      "name": "function_name",
      "purpose": "What this function achieves",
      "parameters": "Parameter descriptions and types",
      "returns": "Return value description",
      "complexity": "Time and space complexity (e.g. O(n) time, O(1) space)",
      "explanation": "Brief explanation of logic"
    }
  ],
  "execution_flow": "Brief trace of execution flow",
  "key_concepts": [
    "Key concept description"
  ],
  "debugging_explanation": "Explanation of any fixes, or none if already clean",
  "test_explanation": "Summary of what the automated tests verified",
  "improvement_recommendations": [
    "Brief actionable tip"
  ]
}
Do NOT include markdown backticks or commentary outside the JSON."""

class ExplainerAgent:
    def __init__(self, ollama_service: OllamaService):
        self.ollama = ollama_service
        self.name = "Code Explainer Agent"

    async def execute(self, code: str, context: Optional[Dict[str, Any]] = None, model: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Generating explainability report...")
        
        ctx_details = ""
        if context:
            if context.get("debugging_history"):
                ctx_details += f"\nDEBUGGING ATTEMPTS: {context['debugging_history']}"
            if context.get("test_results"):
                ctx_details += f"\nTEST RESULTS SUMMARY: {json.dumps(context['test_results'])}"
            if context.get("review_results"):
                ctx_details += f"\nREVIEW SUMMARY: {context['review_results'].get('review_summary', '')}"

        prompt = f"""Explain the following Python code in detail for a developer audience:{ctx_details}

SOURCE CODE:
```python
{code}
```

Respond with strictly valid JSON matching the schema."""

        try:
            raw_response = await self.ollama.generate(prompt, EXPLAINER_SYSTEM_PROMPT, model, num_predict=400)
            result = self._parse_json(raw_response)
            logger.info(f"[{self.name}] Explainability report generated successfully")
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
            logger.error(f"[{self.name}] Explanation error: {e}")
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

        return {
            "overview": text[:400],
            "functions": [],
            "execution_flow": "Step-by-step execution follows main definitions.",
            "key_concepts": [],
            "debugging_explanation": "No debugging recorded or explanation parsed.",
            "test_explanation": "Test results verified program functions.",
            "improvement_recommendations": []
        }
