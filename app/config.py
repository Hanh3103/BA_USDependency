from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import dotenv_values

BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / ".env"

print(f"ENV path: {env_path}")
print(f"ENV exists: {env_path.exists()}")
print(f"ENV values: {dotenv_values(env_path)}")

class Settings(BaseSettings):
    ollama_base_url: str
    ollama_api_key: str
    ollama_models: str
    ollama_temperature: float
    ollama_top_p: float
    ollama_num_predict: int
    ollama_num_ctx: int
    ollama_keep_alive: float | str
    ollama_think: bool
    ollama_format: str

    @property
    def models(self) -> list[str] :
        return self.ollama_models.split(",")  # Split the comma-separated string into a list

    class Config:
        env_file = ".env"


settings = Settings()