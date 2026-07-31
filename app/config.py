from pydantic_settings import BaseSettings
from pathlib import Path
from dotenv import dotenv_values

from errors import AppError

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

    prompt_dir: Path = BASE_DIR / "prompts"
    prompt_version: dict[str, str] = {
        "annotation": "v3",
        "dependency_analysis" : "v1",
    }

    @property
    def models(self) -> list[str] :
        return self.ollama_models.split(",")  # Split the comma-separated string into a list

    def prompt_path(self, task: str, step: int | None = None) -> Path:
        """
        Resolve a prompt file for a given task and step if the sequential chain of thought is used.
        Layout: prompts/<task>/<version>/<task>_<version>_[step_<n>].txt
        task: "annotation" or "dependency_analysis"
        step: None for single shot prompt (<task>_<version>.txt),
            otherwise the step number/name (<task>_<version>_<step>_<n>.txt)

        Raises:
            KeyError if the task has no version registed in prompt_versions
        """
        try:
            version = self.prompt_version[task]
        except KeyError:
            raise KeyError(
                f"No prompt version configured for task {task!r}. "
                f"Add it to Settings.prompt_version in config.py."
            )
        base= f"{task}_{version}"
        filename = f"{base}.txt" if step is None else f"{base}_step_{step}.txt"
        return self.prompt_dir / task / version / filename


    class Config:
        env_file = ".env"


settings = Settings()