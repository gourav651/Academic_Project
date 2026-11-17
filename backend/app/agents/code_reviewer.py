import json
import re
from typing import Dict, Any, Optional, List
from app.services.ollama_service import OllamaService
from app.services.analysis_service import AnalysisService
from app.core.logging_config import logger

REVIEWER_SYSTEM_PROMPT = """You are a senior software architect and code reviewer in an autonomous framework.
Your task is to review Python code for correctness, security vulnerabilities, edge cases, readability, and maintainability.

You must ALWAYS respond with ONLY a valid JSON object matching this schema:
{
  "review_summary": "High-level summary of code quality and readiness",
  "overall_quality": "poor|fair|good|excellent",
  "findings": [
    {
      "type": "bug|security|performance|style|maintainability",
      "severity": "critical|high|medium|low|info",
      "line": 10,
      "description": "What is the issue",
      "suggestion": "How to resolve it",
      "source": "ai"
    }
  ],
  "security_concerns": ["Security concern if any"],
  "maintainability_score": 8,
  "readability_score": 9,
  "recommendations": ["Recommendation 1", "Recommendation 2"],
  "suggested_improvements": "Detailed code improvements"
}
Do NOT include markdown backticks or commentary outside the JSON."""

class CodeReviewerAgent:
    def __init__(self, ollama_service: OllamaService, analysis_service: AnalysisService):
        self.ollama = ollama_service
        self.analysis = analysis_service
        self.name = "Code Reviewer Agent"

    async def execute(self, code: str, model: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"[{self.name}] Initiating review on code...")
        
        # 1. Deterministic AST Analysis
        ast_result = await self.analysis.run_ast_analysis(code)
        
        # 2. Deterministic Ruff Analysis
        ruff_result = await self.analysis.run_ruff_analysis(code)

        prompt = f"""Review the following Python code.
Deterministic Static Analysis has detected the following issues:
AST Findings: {json.dumps(ast_result.get('findings', []))}
Ruff Findings: {json.dumps(ruff_result.get('findings', []))}

CODE TO REVIEW:
```python
{code}
```

Perform thorough semantic review. Respond with strictly valid JSON matching the schema."""

        try:
            raw_response = await self.ollama.generate(prompt, REVIEWER_SYSTEM_PROMPT, model)
            ai_review = self._parse_json(raw_response)
            
            # Combine deterministic findings and AI suggestions, maintaining attribution
            deterministic_findings = ast_result.get('findings', []) + ruff_result.get('findings', [])
            ai_findings = ai_review.get('findings', [])
            all_findings = deterministic_findings + ai_findings

            ai_review['findings'] = all_findings
            ai_review['static_analysis'] = {
                'ast': ast_result,
                'ruff': ruff_result
            }
            logger.info(f"[{self.name}] Review finished: {len(all_findings)} total findings ({len(deterministic_findings)} deterministic, {len(ai_findings)} AI)")
            return {
                "success": True,
                "review": ai_review,
                "raw_response": raw_response
            }

        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"[{self.name}] LLM unavailable ({e}). Falling back to deterministic static analysis results.")
            deterministic_findings = ast_result.get('findings', []) + ruff_result.get('findings', [])
            return {
                "success": True,
                "review": {
                    "review_summary": f"Deterministic static analysis completed (LLM unavailable: {str(e)})",
                    "overall_quality": "unknown",
                    "findings": deterministic_findings,
                    "static_analysis": {'ast': ast_result, 'ruff': ruff_result},
                    "security_concerns": [],
                    "maintainability_score": 6,
                    "readability_score": 6,
                    "recommendations": ["Review deterministic findings above"],
                    "suggested_improvements": "Verify syntax and linter warnings."
                }
            }
        except Exception as e:
            logger.error(f"[{self.name}] Error during review: {e}")
            return {
                "success": False,
                "error": str(e),
                "review": None
            }

    def _parse_json(self, text: str) -> Dict[str, Any]:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {
            "review_summary": text[:300],
            "overall_quality": "good",
            "findings": [],
            "security_concerns": [],
            "maintainability_score": 7,
            "readability_score": 7,
            "recommendations": [],
            "suggested_improvements": text[:200]
        }
