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

    prompt_dir: Path = BASE_DIR / "prompts"
    prompt_versions: dict[str, dict[str, str] | str] = {
        "annotation": "v3",
        "dependency_analysis": {
            "annotated": "v3",
            "text": "v1",
        },
    }

    @property
    def models(self) -> list[str] :
        return self.ollama_models.split(",")

    def prompt_path(self, task: str, variant:str | None=None, step: int | None = None) -> Path:
        try:
            versions = self.prompt_versions[task]
        except KeyError:
            raise KeyError(
                f"No prompt version configured for task {task!r}. "
                f"Add it to Settings.prompt_versions in config.py."
            )

        if isinstance(versions, dict):
            if variant is None:
                raise ValueError(
                    f"prompt_path requires a 'variant' for task {task!r} "
                    f"(one of {list(versions.keys())})."
                )
            try:
                version = versions[variant]
            except KeyError:
                raise KeyError(
                    f"No prompt version configured for {task!r} variant {variant!r}. "
                    f"Add it to Settings.prompt_versions[{task!r}] in config.py."
                )

            base = f"{task}_{version}"
            filename = f"{base}_text.txt" if variant == "text" else (
                f"{base}.txt" if step is None else f"{base}_step_{step}.txt"
            )
            return self.prompt_dir / task / variant / version / filename

        if variant is not None:
            raise ValueError(f"Task {task!r} does not support variants, but variant={variant!r} was given.")
        version = versions
        base = f"{task}_{version}"
        filename = f"{base}.txt" if step is None else f"{base}_step_{step}.txt"
        return self.prompt_dir / task / version / filename


    class Config:
        env_file = str(env_path)


settings = Settings()