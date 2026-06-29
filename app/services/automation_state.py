from __future__ import annotations

import json
import re
from html import unescape
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from app.config import AppConfig


STATE_FILE = "automation_state.json"
RUNS_FILE = "automation_runs.json"
FAILURES_FILE = "failed_items.json"
MAX_RUNS = 100
MAX_ERROR_LENGTH = 280


def compact_text(value: Any, max_length: int = MAX_ERROR_LENGTH) -> str:
    text = unescape(str(value or "").replace("\x00", " ").strip())
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.split(r"所在位置\s+行:|\+\s+throw\s", text, maxsplit=1)[0]
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_length:
        return text[: max_length - 3].rstrip() + "..."
    return text or "未知错误"


def compact_errors(errors: list[Any]) -> list[str]:
    return [compact_text(error) for error in errors if compact_text(error)]


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def mode_flags(mode: str) -> tuple[bool, bool]:
    if mode == "obsidian_only":
        return False, False
    if mode == "notes_only":
        return True, False
    return True, True


def automation_config(config: AppConfig) -> dict[str, Any]:
    raw = config.section("automation")
    return {
        "enabled": bool(raw.get("enabled", False)),
        "interval_minutes": int(raw.get("interval_minutes", 60)),
        "mode": str(raw.get("mode", "full")),
        "run_on_start": bool(raw.get("run_on_start", True)),
        "notify_on_success": bool(raw.get("notify_on_success", False)),
        "notify_on_failure": bool(raw.get("notify_on_failure", True)),
    }


def state_path(config: AppConfig) -> Path:
    return config.storage_dir / STATE_FILE


def runs_path(config: AppConfig) -> Path:
    return config.storage_dir / RUNS_FILE


def failures_path(config: AppConfig) -> Path:
    return config.storage_dir / FAILURES_FILE


def read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def default_state(config: AppConfig) -> dict[str, Any]:
    auto = automation_config(config)
    return {
        "service_started_at": None,
        "automation_enabled": auto["enabled"],
        "mode": auto["mode"],
        "interval_minutes": auto["interval_minutes"],
        "is_running": False,
        "last_started_at": None,
        "last_finished_at": None,
        "last_status": "idle",
        "last_message": "尚未运行",
        "next_run_at": None,
        "paused": not auto["enabled"],
    }


def read_state(config: AppConfig) -> dict[str, Any]:
    state = default_state(config)
    state.update(read_json(state_path(config), {}))
    return state


def write_state(config: AppConfig, patch: dict[str, Any]) -> dict[str, Any]:
    state = read_state(config)
    state.update(patch)
    write_json(state_path(config), state)
    return state


def set_service_started(config: AppConfig) -> None:
    state = read_state(config)
    if not state.get("service_started_at"):
        state["service_started_at"] = now_text()
    auto = automation_config(config)
    state["automation_enabled"] = auto["enabled"]
    state["mode"] = state.get("mode") or auto["mode"]
    state["interval_minutes"] = auto["interval_minutes"]
    state["paused"] = bool(state.get("paused", not auto["enabled"]))
    write_json(state_path(config), state)


def set_next_run(config: AppConfig, minutes: int) -> None:
    next_run = datetime.now() + timedelta(minutes=minutes)
    write_state(config, {"next_run_at": next_run.strftime("%Y-%m-%d %H:%M:%S")})


def append_run(config: AppConfig, run: dict[str, Any]) -> None:
    runs = read_json(runs_path(config), [])
    if not isinstance(runs, list):
        runs = []
    runs.insert(0, run)
    write_json(runs_path(config), runs[:MAX_RUNS])
    failures = []
    for row in run.get("results", []):
        if row.get("status") == "failed":
            failures.append(
                {
                    "run_id": run.get("run_id"),
                    "item_id": row.get("id"),
                    "source_path": row.get("source_path"),
                    "stage": row.get("stage") or "unknown",
                    "error": compact_text(row.get("error") or "处理失败"),
                    "retryable": True,
                    "last_failed_at": run.get("finished_at"),
                }
            )
    if failures:
        write_json(failures_path(config), failures + read_failures(config))


def read_runs(config: AppConfig, limit: int = 20) -> list[dict[str, Any]]:
    runs = read_json(runs_path(config), [])
    return runs[:limit] if isinstance(runs, list) else []


def read_failures(config: AppConfig) -> list[dict[str, Any]]:
    failures = read_json(failures_path(config), [])
    return failures if isinstance(failures, list) else []


def summarize_result(result: dict[str, Any]) -> dict[str, Any]:
    rows = result.get("results", [])
    return {
        "pulled": int(result.get("pulled", 0)),
        "processed": sum(1 for row in rows if row.get("status") == "processed"),
        "failed": sum(1 for row in rows if row.get("status") == "failed"),
        "note_count": sum(len(row.get("note_paths") or []) for row in rows),
        "card_count": sum(int(row.get("card_count") or 0) for row in rows),
    }
