from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import load_config
from app.models import CaptureRequest, CaptureResult
from app.services.source_capture import capture_source


router = APIRouter(prefix="/api/capture", tags=["capture"])


@router.post("", response_model=CaptureResult)
def capture(request: CaptureRequest) -> CaptureResult:
    try:
        return capture_source(load_config(), request)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
