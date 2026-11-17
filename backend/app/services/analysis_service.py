import ast
import subprocess
import tempfile
import os
import json
import sys
from typing import Dict, Any, List
from app.core.logging_config import logger

class AnalysisService:
    async def run_ast_analysis(self, code: str) -> Dict[str, Any]:
        """Deterministic Python AST static analysis."""
        findings: List[Dict[str, Any]] = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                # Check functions for docstrings and excessive arguments
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not ast.get_docstring(node):
                        findings.append({
                            "type": "missing_docstring",
                            "line": node.lineno,
                            "message": f"Function '{node.name}' lacks a descriptive docstring",
                            "severity": "info",
                            "source": "ast"
                        })
                    if len(node.args.args) > 6:
                        findings.append({
                            "type": "excessive_parameters",
                            "line": node.lineno,
                            "message": f"Function '{node.name}' has {len(node.args.args)} parameters (consider refactoring)",
                            "severity": "warning",
                            "source": "ast"
                        })

                # Check for bare except
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    findings.append({
                        "type": "bare_except",
                        "line": node.lineno,
                        "message": "Bare 'except:' catches all exceptions including system interrupts",
                        "severity": "warning",
                        "source": "ast"
                    })

                # Check for improper identity comparison (e.g., `x is "val"`)
                if isinstance(node, ast.Compare):
                    for op in node.ops:
                        if isinstance(op, (ast.Is, ast.IsNot)):
                            for comp in node.comparators:
                                if isinstance(comp, ast.Constant) and comp.value is not None and not isinstance(comp.value, bool):
                                    findings.append({
                                        "type": "identity_comparison_with_literal",
                                        "line": node.lineno,
                                        "message": f"Comparison with literal value using 'is'/'is not'; use == or != instead",
                                        "severity": "warning",
                                        "source": "ast"
                                    })

            return {
                "success": True,
                "syntax_valid": True,
                "findings": findings,
                "total_findings": len(findings)
            }
        except SyntaxError as e:
            return {
                "success": False,
                "syntax_valid": False,
                "error": str(e),
                "findings": [{
                    "type": "syntax_error",
                    "line": e.lineno,
                    "message": f"SyntaxError at line {e.lineno}: {e.msg}",
                    "severity": "critical",
                    "source": "ast"
                }],
                "total_findings": 1
            }
        except Exception as e:
            logger.error(f"AST Analysis error: {e}")
            return {
                "success": False,
                "syntax_valid": False,
                "error": str(e),
                "findings": [],
                "total_findings": 0
            }

    async def run_ruff_analysis(self, code: str) -> Dict[str, Any]:
        """Deterministic Ruff linter execution."""
        findings: List[Dict[str, Any]] = []
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(code)
                tmp_path = f.name

            # Run ruff check
            result = subprocess.run(
                ["ruff", "check", "--output-format", "json", tmp_path],
                capture_output=True, text=True, timeout=15
            )

            if result.stdout and result.stdout.strip():
                try:
                    ruff_json = json.loads(result.stdout)
                    for item in ruff_json:
                        findings.append({
                            "type": item.get("code", "style_issue"),
                            "line": item.get("location", {}).get("row", 0),
                            "message": item.get("message", ""),
                            "severity": "warning",
                            "source": "ruff",
                            "fix_available": item.get("fix") is not None
                        })
                except json.JSONDecodeError:
                    pass

            return {
                "success": True,
                "findings": findings,
                "total_findings": len(findings)
            }
        except FileNotFoundError:
            # Ruff binary not on PATH directly, try python -m ruff
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "ruff", "check", "--output-format", "json", tmp_path],
                    capture_output=True, text=True, timeout=15
                )
                if result.stdout and result.stdout.strip():
                    ruff_json = json.loads(result.stdout)
                    for item in ruff_json:
                        findings.append({
                            "type": item.get("code", "style_issue"),
                            "line": item.get("location", {}).get("row", 0),
                            "message": item.get("message", ""),
                            "severity": "warning",
                            "source": "ruff",
                            "fix_available": item.get("fix") is not None
                        })
                return {"success": True, "findings": findings, "total_findings": len(findings)}
            except Exception as e:
                return {
                    "success": False,
                    "findings": [],
                    "error": f"Ruff linter not available: {str(e)}"
                }
        except Exception as e:
            return {"success": False, "findings": [], "error": str(e)}
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

analysis_service = AnalysisService()
