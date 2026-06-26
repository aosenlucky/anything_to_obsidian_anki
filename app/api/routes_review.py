from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import load_config
from app.services.dashboard_generator import generate_dashboards
from app.services.review_generator import generate_monthly_review, generate_weekly_review


router = APIRouter(prefix="/api/review", tags=["review"])


@router.post("/weekly")
def weekly() -> dict[str, str]:
    try:
        path, content = generate_weekly_review(load_config())
        return {"path": path, "content": content}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/monthly")
def monthly() -> dict[str, str]:
    try:
        path, content = generate_monthly_review(load_config())
        return {"path": path, "content": content}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/dashboards")
def dashboards() -> dict[str, list[str]]:
    try:
        return {"paths": generate_dashboards(load_config())}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
