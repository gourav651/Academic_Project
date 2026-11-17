import asyncio
from typing import Optional, List, Dict, Any
import ollama as ollama_lib
from app.core.config import settings
from app.core.logging_config import logger

class OllamaService:
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = ollama_lib.Client(host=self.base_url)
        return self._client

    def set_model(self, model: str):
        self.model = model
        logger.info(f"Ollama default model changed to: {model}")

    async def check_connection(self) -> Dict[str, Any]:
        """Verify if Ollama service is reachable and return list of available models."""
        try:
            loop = asyncio.get_running_loop()
            models_res = await loop.run_in_executor(None, self.client.list)
            # models_res is a ListResponse object with .models attribute
            model_list = []
            if hasattr(models_res, 'models'):
                for m in models_res.models:
                    model_list.append(getattr(m, 'model', str(m)))
            elif isinstance(models_res, dict) and 'models' in models_res:
                model_list = [m.get('name') or m.get('model') for m in models_res['models']]
            return {"connected": True, "models": model_list}
        except Exception as e:
            logger.warning(f"Ollama connection check failed: {e}")
            return {
                "connected": False,
                "error": f"Cannot connect to Ollama at {self.base_url}. Ensure Ollama is installed and running (`ollama serve`). Details: {str(e)}"
            }

    async def generate(self, prompt: str, system: str = "", model: Optional[str] = None) -> str:
        """Execute chat completion with Ollama with timeout and error handling."""
        model_to_use = model or self.model
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            loop = asyncio.get_running_loop()

            def _chat_call():
                return self.client.chat(
                    model=model_to_use,
                    messages=messages,
                    options={"temperature": 0.2, "num_predict": 4096}
                )

            response = await asyncio.wait_for(
                loop.run_in_executor(None, _chat_call),
                timeout=float(settings.ollama_timeout)
            )
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                return response.message.content
            elif isinstance(response, dict):
                return response.get('message', {}).get('content', '')
            return str(response)

        except asyncio.TimeoutError:
            raise TimeoutError(
                f"Ollama request timed out after {settings.ollama_timeout} seconds using model '{model_to_use}'."
            )
        except Exception as e:
            raise ConnectionError(
                f"Ollama generation failed for model '{model_to_use}'. Ensure Ollama is running at {self.base_url}. Error: {str(e)}"
            )

    async def list_models(self) -> List[Dict[str, Any]]:
        """Return formatted model objects with sizes and names."""
        try:
            loop = asyncio.get_running_loop()
            models_res = await loop.run_in_executor(None, self.client.list)
            result = []
            if hasattr(models_res, 'models'):
                for m in models_res.models:
                    result.append({
                        "name": getattr(m, 'model', str(m)),
                        "size": getattr(m, 'size', 0),
                        "modified_at": str(getattr(m, 'modified_at', ''))
                    })
            elif isinstance(models_res, dict) and 'models' in models_res:
                for m in models_res['models']:
                    result.append({
                        "name": m.get('name') or m.get('model'),
                        "size": m.get('size', 0),
                        "modified_at": str(m.get('modified_at', ''))
                    })
            return result
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
            return []

ollama_service = OllamaService()
