import os
import re
import sys
import tempfile
import shutil
import subprocess
from typing import Dict, Any
from app.core.logging_config import logger

class TestingService:
    async def run_tests(self, test_code: str, source_code: str, filename: str = "solution.py") -> Dict[str, Any]:
        """Run pytest on generated unit tests against the source code in a sandbox directory."""
        tmp_dir = tempfile.mkdtemp(prefix="agentic_pytest_")
        try:
            # Clean fences if any
            clean_source = source_code.strip()
            if clean_source.startswith("```"):
                clean_source = re.sub(r"^```[a-zA-Z]*\n?", "", clean_source)
                clean_source = re.sub(r"\n?```$", "", clean_source).strip()

            clean_test = test_code.strip()
            if clean_test.startswith("```"):
                clean_test = re.sub(r"^```[a-zA-Z]*\n?", "", clean_test)
                clean_test = re.sub(r"\n?```$", "", clean_test).strip()

            # 1. Write solution.py
            with open(os.path.join(tmp_dir, "solution.py"), 'w', encoding='utf-8') as f:
                f.write(clean_source)

            # 2. If custom filename is given and not solution.py, also write it
            if filename and filename != "solution.py":
                base_name = os.path.basename(filename)
                with open(os.path.join(tmp_dir, base_name), 'w', encoding='utf-8') as f:
                    f.write(clean_source)

            # 3. Detect any imported modules in test_code like:
            # from xyz import ... or import xyz
            imported_mods = set(re.findall(r'(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_]*)', clean_test))
            standard_mods = {
                'sys', 'os', 'pytest', 'unittest', 'math', 're', 'json', 'time', 'datetime', 
                'typing', 'collections', 'itertools', 'functools', 'random', 'string', 'pathlib',
                'copy', 'abc', 'enum', 'io', 'tempfile', 'shutil', 'subprocess', 'inspect',
                'decimal', 'fractions', 'statistics', 'dataclasses'
            }
            for mod in imported_mods:
                if mod not in standard_mods and not (mod.startswith('__') or mod == 'solution'):
                    mod_file = os.path.join(tmp_dir, f"{mod}.py")
                    if not os.path.exists(mod_file):
                        with open(mod_file, 'w', encoding='utf-8') as f:
                            f.write(clean_source)

            # 4. Write test code
            with open(os.path.join(tmp_dir, "test_solution.py"), 'w', encoding='utf-8') as f:
                f.write(clean_test)

            # 5. Configure sys.path via conftest
            conftest_content = (
                "import sys, os\n"
                "dir_path = os.path.dirname(__file__)\n"
                "if dir_path not in sys.path:\n"
                "    sys.path.insert(0, dir_path)\n"
            )
            with open(os.path.join(tmp_dir, "conftest.py"), 'w', encoding='utf-8') as f:
                f.write(conftest_content)

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
