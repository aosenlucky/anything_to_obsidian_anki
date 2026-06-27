from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.yaml"
EXAMPLE_CONFIG_PATH = PROJECT_ROOT / "config.yaml.example"
ENV_PATH = PROJECT_ROOT / ".env"


@dataclass(frozen=True)
class AppConfig:
    raw: dict[str, Any]
    config_path: Path

    @property
    def vault_path(self) -> Path:
        return Path(self.raw["obsidian"]["vault_path"]).expanduser()

    @property
    def storage_dir(self) -> Path:
        return PROJECT_ROOT / "app" / "storage"

    def section(self, name: str) -> dict[str, Any]:
        return dict(self.raw.get(name, {}))

    def domains(self) -> list[str]:
        return list(self.raw.get("domains", []))

    def resolve_vault_path(self, path_value: str | Path) -> Path:
        path = Path(path_value)
        if path.is_absolute():
            return path
        return self.vault_path / path

    def relative_to_vault(self, path_value: str | Path) -> str:
        path = Path(path_value)
        try:
            return path.relative_to(self.vault_path).as_posix()
        except ValueError:
            return path.as_posix()


def _deep_merge(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = dict(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(config_path: str | Path | None = None) -> AppConfig:
    load_dotenv(ENV_PATH, encoding="utf-8-sig")
    env_config = os.getenv("LAP_CONFIG")
    selected = Path(config_path or env_config or DEFAULT_CONFIG_PATH)

    with EXAMPLE_CONFIG_PATH.open("r", encoding="utf-8") as f:
        defaults = yaml.safe_load(f) or {}

    overrides: dict[str, Any] = {}
    if selected.exists():
        with selected.open("r", encoding="utf-8") as f:
            overrides = yaml.safe_load(f) or {}

    return AppConfig(raw=_deep_merge(defaults, overrides), config_path=selected)
