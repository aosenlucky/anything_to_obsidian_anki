from __future__ import annotations

import asyncio
import uuid
from datetime import datetime
from typing import Any

from app.config import AppConfig, load_config

from .automation_state import (
    append_run,
    automation_config,
    compact_errors,
    compact_text,
    mode_flags,
    now_text,
    read_state,
    set_next_run,
    set_service_started,
    summarize_result,
    write_state,
)
from .anki_card_generator import load_pending_cards
from .ankiconnect_client import sync_cards
from .cloud_inbox_processor import pull_cloud_inbox


_runner: AutomationRunner | None = None


class AutomationRunner:
    def __init__(self, config: AppConfig):
        self.config = config
        self._lock = asyncio.Lock()
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        set_service_started(self.config)
        self._task = asyncio.create_task(self._loop(), name="knowledge-tree-automation")

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            await self._task

    async def _loop(self) -> None:
        auto = automation_config(self.config)
        if auto["enabled"] and auto["run_on_start"]:
            await asyncio.sleep(30)
            await self.run_once(trigger="startup")
        while not self._stop.is_set():
            self.config = load_config()
            auto = automation_config(self.config)
            interval = max(1, int(auto["interval_minutes"]))
            write_state(
                self.config,
                {
                    "automation_enabled": auto["enabled"],
                    "interval_minutes": interval,
                },
            )
            set_next_run(self.config, interval)
            try:
                await asyncio.wait_for(self._stop.wait(), timeout=interval * 60)
            except asyncio.TimeoutError:
                pass
            if self._stop.is_set():
                break
            state = read_state(self.config)
            if state.get("paused") or not state.get("automation_enabled"):
                continue
            await self.run_once(trigger="scheduler")

    async def run_once(self, mode: str | None = None, trigger: str = "manual") -> dict[str, Any]:
        if self._lock.locked():
            state = write_state(
                self.config,
                {
                    "last_status": "skipped",
                    "last_message": "上一轮仍在运行，本轮已跳过",
                },
            )
            return {"status": "skipped", "state": state}

        async with self._lock:
            config = load_config()
            self.config = config
            state = read_state(config)
            configured_mode = str(state.get("mode") or automation_config(config)["mode"])
            selected_mode = mode or configured_mode
            process_ai, sync_anki = mode_flags(selected_mode)
            run_id = datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]
            started = now_text()
            write_state(
                config,
                {
                    "is_running": True,
                    "last_started_at": started,
                    "last_status": "running",
                    "last_message": "自动同步运行中",
                    "mode": configured_mode,
                    "automation_enabled": bool(state.get("automation_enabled", automation_config(config)["enabled"])),
                },
            )
            run: dict[str, Any] = {
                "run_id": run_id,
                "started_at": started,
                "finished_at": None,
                "trigger": trigger,
                "mode": selected_mode,
                "status": "running",
                "pulled": 0,
                "processed": 0,
                "failed": 0,
                "note_count": 0,
                "card_count": 0,
                "errors": [],
                "results": [],
            }
            try:
                result = await asyncio.to_thread(
                    pull_cloud_inbox,
                    config,
                    None,
                    process_ai,
                    sync_anki,
                    False,
                )
                summary = summarize_result(result)
                anki_result = None
                if sync_anki:
                    anki_result = await asyncio.to_thread(sync_cards, config, load_pending_cards(config), False)
                anki_failed = int(getattr(anki_result, "failed", 0) or 0) if anki_result else 0
                anki_errors = compact_errors(list(getattr(anki_result, "errors", []) or [])) if anki_result else []
                if anki_result and not getattr(anki_result, "anki_available", False):
                    anki_errors.append("AnkiConnect 未连接，卡片已保留在待同步队列。")
                status = "success" if summary["failed"] == 0 and not anki_errors and anki_failed == 0 else "partial_failed"
                message = (
                    f"拉取 {summary['pulled']} 条，"
                    f"完成 {summary['processed']} 条，"
                    f"失败 {summary['failed']} 条"
                )
                if anki_result:
                    message += f"，Anki 同步 {anki_result.synced} 张"
                    if anki_errors or anki_failed:
                        message += "，存在待处理卡片"
                run.update(summary)
                if anki_result:
                    run["anki_available"] = anki_result.anki_available
                    run["anki_synced"] = anki_result.synced
                    run["anki_failed"] = anki_result.failed
                    run["anki_skipped"] = anki_result.skipped_duplicates
                    run["errors"] = anki_errors
                run["status"] = status
                run["results"] = result.get("results", [])
                run["finished_at"] = now_text()
                write_state(
                    config,
                    {
                        "is_running": False,
                        "last_finished_at": run["finished_at"],
                        "last_status": status,
                        "last_message": message,
                    },
                )
                append_run(config, run)
                return {"status": status, "result": result, "run": run}
            except Exception as exc:
                finished = now_text()
                error = compact_text(exc)
                run.update(
                    {
                        "finished_at": finished,
                        "status": "failed",
                        "failed": 1,
                        "errors": [error],
                    }
                )
                write_state(
                    config,
                    {
                        "is_running": False,
                        "last_finished_at": finished,
                        "last_status": "failed",
                        "last_message": error,
                    },
                )
                append_run(config, run)
                return {"status": "failed", "error": error, "run": run}


def get_runner() -> AutomationRunner:
    global _runner
    if _runner is None:
        _runner = AutomationRunner(load_config())
    return _runner


def start_runner() -> None:
    get_runner().start()


async def stop_runner() -> None:
    if _runner is not None:
        await _runner.stop()
