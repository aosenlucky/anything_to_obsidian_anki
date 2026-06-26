from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import load_config
from app.models import SyncRequest, SyncResult
from app.services.anki_card_generator import load_pending_cards
from app.services.ankiconnect_client import sync_cards


router = APIRouter(prefix="/api/anki", tags=["anki"])


@router.post("/sync", response_model=SyncResult)
def sync(request: SyncRequest) -> SyncResult:
    try:
        config = load_config()
        cards = load_pending_cards(config) if request.all_pending else request.cards
        return sync_cards(config, cards, dry_run=request.dry_run)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
