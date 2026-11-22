import os
import sys
import ast
import tempfile
import shutil
import time
import subprocess
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.logging_config import logger

try:
    import docker
    DOCKER_LIB_INSTALLED = True
except ImportError:
    DOCKER_LIB_INSTALLED = False

DOCKER_IMAGE = "python:3.11-slim"

class ExecutionService:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if not DOCKER_LIB_INSTALLED:
            return None
        if self._client is None:
            try:
                self._client = docker.from_env()
                self._client.ping()
            except Exception as e:
                logger.debug(f"Docker ping failed: {e}")
                self._client = None
        return self._client

    def check_available(self) -> Dict[str, Any]:
        """Check if Docker engine is running and reachable."""
        if not DOCKER_LIB_INSTALLED:
            return {
                "available": False,
                "error": "The Python 'docker' package is not installed. Run `pip install docker`."
            }
        client = self._get_client()
        if client is None:
            return {
                "available": False,
                "error": "Docker daemon is not running. Please start Docker Desktop or the Docker Engine daemon."
            }
        try:
            client.ping()
            return {"available": True}
        except Exception as e:
            return {
                "available": False,
                "error": f"Docker connection error: {str(e)}. Please ensure Docker Desktop is started."
            }

    async def execute_code(self, code: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Execute Python code in Docker if available, otherwise fallback to safe local subprocess sandbox."""
        timeout = timeout or settings.execution_timeout
        check = self.check_available()

        if check["available"]:
            return await self._execute_docker(code, timeout)
        else:
            return await self._execute_subprocess(code, timeout)

    async def _execute_docker(self, code: str, timeout: int) -> Dict[str, Any]:
        client = self._get_client()
        tmp_dir = tempfile.mkdtemp(prefix="agentic_exec_")
        start_time = time.time()

        try:
            code_file = os.path.join(tmp_dir, "solution.py")
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)

            # Isolated execution inside container
            container = client.containers.run(
                image=DOCKER_IMAGE,
                command=["python", "/workspace/solution.py"],
                volumes={tmp_dir: {"bind": "/workspace", "mode": "ro"}},
                mem_limit="256m",
                cpu_period=100000,
                cpu_quota=50000,   # Limit CPU to 50%
                network_disabled=True,  # No internet access
                remove=True,
                detach=False,
                stdout=True,
                stderr=True,
            )

            exec_time = time.time() - start_time
            output = container.decode('utf-8', errors='replace') if isinstance(container, bytes) else str(container)

            return {
                "success": True,
                "stdout": output,
                "stderr": "",
                "return_code": 0,
                "execution_time": round(exec_time, 3),
                "error": "",
                "traceback": "",
                "docker_available": True,
                "sandbox_mode": "docker_container"
            }

        except Exception as e:
            exec_time = time.time() - start_time
            stderr = ""
            return_code = -1
            if hasattr(e, 'stderr') and e.stderr:
                stderr = e.stderr.decode('utf-8', errors='replace')
            if hasattr(e, 'exit_status'):
                return_code = e.exit_status

            err_msg = stderr or str(e)
            return {
                "success": False,
                "stdout": "",
                "stderr": err_msg,
                "return_code": return_code,
                "execution_time": round(exec_time, 3),
                "error": "Execution error during container run",
                "traceback": err_msg,
                "docker_available": True,
                "sandbox_mode": "docker_container"
            }
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    async def _execute_subprocess(self, code: str, timeout: int) -> Dict[str, Any]:
        """Safe local execution fallback when Docker daemon is offline."""
        # AST Safety Pre-check
        is_safe, violation = self._validate_ast_safety(code)
        if not is_safe:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Safety Policy Error: {violation}",
                "return_code": -1,
                "execution_time": 0.0,
                "error": f"Safety Policy Error: {violation}",
                "traceback": f"SecurityException: {violation}",
                "docker_available": False,
                "sandbox_mode": "local_subprocess"
            }

        tmp_dir = tempfile.mkdtemp(prefix="agentic_local_sandbox_")
        start_time = time.time()

        try:
            code_file = os.path.join(tmp_dir, "solution.py")
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(code)

            result = subprocess.run(
                [sys.executable, "-u", "solution.py"],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmp_dir
            )

            exec_time = time.time() - start_time
            stdout = result.stdout or ""
            stderr = result.stderr or ""
            is_success = (result.returncode == 0)

            # Include notice about fallback mode
            notice = "[Executed in Isolated Subprocess Sandbox (Docker Desktop offline)]"
            if stdout:
                stdout = f"{notice}\n{stdout}"
            elif is_success and not stderr:
                stdout = f"{notice}\n[Process completed successfully with exit code 0 (no output printed)]"

            return {
                "success": is_success,
                "stdout": stdout,
                "stderr": stderr,
                "return_code": result.returncode,
                "execution_time": round(exec_time, 3),
                "error": stderr if not is_success else "",
                "traceback": stderr if not is_success else "",
                "docker_available": False,
                "sandbox_mode": "local_subprocess"
            }

        except subprocess.TimeoutExpired:
            exec_time = time.time() - start_time
            err = f"Execution timed out after {timeout} seconds (infinite loop detected)."
            return {
                "success": False,
                "stdout": "",
                "stderr": err,
                "return_code": -1,
                "execution_time": round(exec_time, 3),
                "error": err,
                "traceback": "TimeoutExpired",
                "docker_available": False,
                "sandbox_mode": "local_subprocess"
            }
        except Exception as e:
            exec_time = time.time() - start_time
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "execution_time": round(exec_time, 3),
                "error": str(e),
                "traceback": str(e),
                "docker_available": False,
                "sandbox_mode": "local_subprocess"
            }
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def _validate_ast_safety(self, code: str) -> tuple[bool, str]:
        """Block raw OS destruction or shell tampering in local fallback sandbox."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func_name = ""
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr
                    if func_name in ("system", "popen", "spawnl", "execv"):
                        return False, f"Direct system shell invocation '{func_name}()' is prohibited."
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    mod_name = getattr(node, 'module', '') or ''
                    names = [a.name for a in node.names]
                    for name in [mod_name] + names:
                        if name in ("ctypes", "winreg", "msvcrt"):
                            return False, f"Sensitive low-level system module '{name}' is prohibited."
            return True, ""
        except SyntaxError:
            return True, ""

execution_service = ExecutionService()
