from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import load_config
from app.models import ProcessRequest, ProcessResult, WriteNotesRequest
from app.services.ai_processor import analyze_source_file
from app.services.anki_card_generator import cards_from_analysis, save_pending_cards
from app.services.note_generator import write_notes_from_analysis


router = APIRouter(prefix="/api/process", tags=["process"])


@router.post("", response_model=ProcessResult)
def process_source(request: ProcessRequest) -> ProcessResult:
    config = load_config()
    try:
        analysis = analyze_source_file(config, request.source_path)
        note_paths: list[str] = []
        if request.write_notes:
            note_paths = write_notes_from_analysis(config, request.source_path, analysis, dry_run=request.dry_run)
        cards = cards_from_analysis(config, analysis, request.source_path, note_paths)
        if note_paths and not request.dry_run:
            save_pending_cards(config, cards)
        return ProcessResult(
            analysis=analysis,
            note_paths=note_paths,
            cards=cards,
            needs_user_review=bool(analysis.get("needs_user_review", False)),
            missing_information=analysis.get("missing_information", []),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/write", response_model=ProcessResult)
def write_notes(request: WriteNotesRequest) -> ProcessResult:
    config = load_config()
    try:
        note_paths = write_notes_from_analysis(config, request.source_path, request.analysis, dry_run=request.dry_run)
        cards = cards_from_analysis(config, request.analysis, request.source_path, note_paths)
        if note_paths and not request.dry_run:
            save_pending_cards(config, cards)
        return ProcessResult(
            analysis=request.analysis,
            note_paths=note_paths,
            cards=cards,
            needs_user_review=bool(request.analysis.get("needs_user_review", False)),
            missing_information=request.analysis.get("missing_information", []),
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
