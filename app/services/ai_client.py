from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

from app.config import AppConfig


class AIClientError(RuntimeError):
    pass


class DeepSeekClient:
    def __init__(self, config: AppConfig):
        ai_config = config.section("ai")
        self.provider = ai_config.get("provider", "deepseek")
        self.base_url = ai_config.get("base_url", "https://api.deepseek.com")
        self.model = ai_config.get("model", "v4-pro")
        self.temperature = float(ai_config.get("temperature", 0.2))
        self.max_output_tokens = int(ai_config.get("max_output_tokens", 8192))
        api_key_env = ai_config.get("api_key_env", "DEEPSEEK_API_KEY")
        self.api_key = os.getenv(api_key_env)
        if not self.api_key:
            raise AIClientError(f"未找到环境变量 {api_key_env}，请先配置 DeepSeek API Key。")
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(self, messages: list[dict[str, str]], json_mode: bool = True) -> str:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_output_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        try:
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise AIClientError(f"DeepSeek API 调用失败：{exc}") from exc

    def analyze_source(self, prompt: str) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": "你只输出严格 JSON，用于知识资产加工系统。"},
            {"role": "user", "content": prompt},
        ]
        raw = self.chat(messages, json_mode=True)
        return self.parse_or_repair_json(raw)

    def parse_or_repair_json(self, raw: str) -> dict[str, Any]:
        parsed = _try_parse_json(raw)
        if parsed is not None:
            return parsed

        extracted = _extract_first_json_object(raw)
        if extracted:
            parsed = _try_parse_json(extracted)
            if parsed is not None:
                return parsed

        repair_prompt = (
            "请把下面内容修复成合法 JSON。只返回 JSON，不要 Markdown，不要解释。\n\n"
            f"{raw}"
        )
        repaired = self.chat([{"role": "user", "content": repair_prompt}], json_mode=True)
        parsed = _try_parse_json(repaired)
        if parsed is not None:
            return parsed
        raise AIClientError("AI 返回内容无法解析为合法 JSON，已尝试自动修复但仍失败。")


def _try_parse_json(value: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _extract_first_json_object(value: str) -> str | None:
    start = value.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(value[start:], start=start):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return value[start : index + 1]
    return None
