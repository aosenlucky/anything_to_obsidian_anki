from __future__ import annotations

import os

from fastapi import APIRouter

from app.config import load_config
from app.models import StatusResult
from app.services.ankiconnect_client import AnkiConnectClient


router = APIRouter(prefix="/api/status", tags=["status"])


@router.get("", response_model=StatusResult)
def status() -> StatusResult:
    config = load_config()
    ai_config = config.section("ai")
    api_key_env = ai_config.get("api_key_env", "DEEPSEEK_API_KEY")
    deepseek = "已配置" if os.getenv(api_key_env) else "未配置"
    obsidian = "已配置" if config.vault_path.exists() else "路径无效"
    anki = "已连接" if AnkiConnectClient(config).is_available() else "未连接"
    return StatusResult(
        deepseek=f"DeepSeek API：{deepseek}",
        anki=f"AnkiConnect：{anki}",
        obsidian=f"Obsidian Vault：{obsidian}",
        config_path=config.config_path.as_posix(),
        vault_path=config.vault_path.as_posix(),
    )
