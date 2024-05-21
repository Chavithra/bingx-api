from pathlib import Path

from pydantic import BaseModel

PATH_PROJECT_FOLDER = (Path(__file__) / ".." / ".." / ".." / "..").resolve()
PATH_CONFIG_FOLDER = PATH_PROJECT_FOLDER / "config"
PATH_CONFIG_FILE = PATH_CONFIG_FOLDER / "bingx" / "bingx_api.json"
PATH_LOG_FOLDER = PATH_PROJECT_FOLDER / "log"


class APIConfig(BaseModel):
    API_KEY: str
    API_SECRET: str


def build_api_config(
    location: Path = PATH_CONFIG_FILE,
    override: dict | None = None,
) -> APIConfig:
    if not location and not override:
        raise AttributeError("You need to provide at least on argument.")

    config = {}

    if override:
        config.update(override)

    api_config = APIConfig.model_validate_json(location.read_text())

    return api_config
