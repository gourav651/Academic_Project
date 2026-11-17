import os
import tempfile
import shutil
import time
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
                "error": "Docker daemon is not running. Please start Docker Desktop or the Docker Engine daemon to enable safe, isolated container execution."
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
        """Safely execute Python code in an isolated Docker container with resource constraints."""
        timeout = timeout or settings.execution_timeout
        check = self.check_available()

        if not check["available"]:
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "return_code": -1,
                "execution_time": 0.0,
                "error": f"Safe execution blocked: {check.get('error')}. Arbitrary code is NOT executed on the host system to prevent system damage.",
                "traceback": "",
                "docker_available": False
            }

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
                "docker_available": True
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
                "docker_available": True
            }
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

execution_service = ExecutionService()
