import os
import json
from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DB_PATH = os.path.join(BASE_DIR, "agentic_framework.db").replace("\\", "/")

class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:1.5b"
    ollama_timeout: int = 120
    max_debug_attempts: int = 3
    execution_timeout: int = 30
    database_url: str = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"
    secret_key: str = "dev-secret-key-change-in-production"
    cors_origins: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("["):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
        "case_sensitive": False
    }

settings = Settings()
