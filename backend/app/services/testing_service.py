import os
import re
import sys
import tempfile
import shutil
import subprocess
from typing import Dict, Any
from app.core.logging_config import logger

class TestingService:
    async def run_tests(self, test_code: str, source_code: str) -> Dict[str, Any]:
        """Run pytest on generated unit tests against the source code in a sandbox directory."""
        tmp_dir = tempfile.mkdtemp(prefix="agentic_pytest_")
        try:
            # Write solution code
            with open(os.path.join(tmp_dir, "solution.py"), 'w', encoding='utf-8') as f:
                f.write(source_code)

            # Write test code
            with open(os.path.join(tmp_dir, "test_solution.py"), 'w', encoding='utf-8') as f:
                f.write(test_code)

            # Configure sys.path via conftest
            with open(os.path.join(tmp_dir, "conftest.py"), 'w', encoding='utf-8') as f:
                f.write("import sys, os\nsys.path.insert(0, os.path.dirname(__file__))\n")

            # Run pytest using current Python executable
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "test_solution.py", "-v", "--tb=short", "--no-header", "-rN"],
                capture_output=True, text=True, timeout=45, cwd=tmp_dir
            )

            output = result.stdout + ("\n" + result.stderr if result.stderr else "")
            total, passed, failed = self._parse_pytest_output(output)

            return {
                "success": result.returncode == 0,
                "total_tests": total,
                "passed_tests": passed,
                "failed_tests": failed,
                "test_output": output,
                "return_code": result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "test_output": "Test execution timed out after 45 seconds.",
                "return_code": -1
            }
        except Exception as e:
            logger.error(f"Test execution error: {e}")
            return {
                "success": False,
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "test_output": f"Failed to execute tests: {str(e)}",
                "return_code": -1
            }
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _parse_pytest_output(self, output: str):
        passed = 0
        failed = 0
        # Parse pytest summary e.g. "2 passed, 1 failed in 0.12s" or "3 passed in 0.05s"
        m_passed = re.search(r'(\d+)\s+passed', output)
        if m_passed:
            passed = int(m_passed.group(1))

        m_failed = re.search(r'(\d+)\s+failed', output)
        if m_failed:
            failed = int(m_failed.group(1))

        m_error = re.search(r'(\d+)\s+error', output)
        if m_error:
            failed += int(m_error.group(1))

        total = passed + failed
        return total, passed, failed

testing_service = TestingService()
