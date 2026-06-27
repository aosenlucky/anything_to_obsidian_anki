from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from app.config import load_config
from app.models import CloudPullRequest
from app.services.cloud_inbox_processor import pull_cloud_inbox


router = APIRouter(prefix="/api/cloud", tags=["cloud"])


@router.post("/pull")
def pull(request: CloudPullRequest) -> dict[str, Any]:
    try:
        return pull_cloud_inbox(
            load_config(),
            limit=request.limit,
            process_ai=request.process_ai,
            sync_anki=request.sync_anki,
            dry_run=request.dry_run,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
