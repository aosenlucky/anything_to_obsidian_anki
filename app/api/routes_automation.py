from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.config import load_config
from app.models import AutomationRunRequest, AutomationSettingsRequest
from app.services.automation_scheduler import get_runner
from app.services.automation_state import (
    automation_config,
    read_failures,
    read_runs,
    read_state,
    write_state,
)


router = APIRouter(prefix="/api/automation", tags=["automation"])


@router.get("/status")
def status() -> dict[str, Any]:
    config = load_config()
    state = read_state(config)
    state["config"] = automation_config(config)
    return state


@router.post("/run")
async def run(request: AutomationRunRequest) -> dict[str, Any]:
    try:
        return await get_runner().run_once(mode=request.mode, trigger=request.trigger)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/pause")
def pause() -> dict[str, Any]:
    return write_state(load_config(), {"paused": True, "automation_enabled": False})


@router.post("/resume")
def resume() -> dict[str, Any]:
    config = load_config()
    auto = automation_config(config)
    return write_state(config, {"paused": False, "automation_enabled": True, "mode": auto["mode"]})


@router.post("/settings")
def settings(request: AutomationSettingsRequest) -> dict[str, Any]:
    patch: dict[str, Any] = {}
    if request.enabled is not None:
        patch["automation_enabled"] = request.enabled
        patch["paused"] = not request.enabled
    if request.mode is not None:
        patch["mode"] = request.mode
    return write_state(load_config(), patch)


@router.get("/runs")
def runs(limit: int = 20) -> dict[str, Any]:
    return {"runs": read_runs(load_config(), limit=limit)}


@router.get("/failures")
def failures() -> dict[str, Any]:
    return {"failures": read_failures(load_config())}
