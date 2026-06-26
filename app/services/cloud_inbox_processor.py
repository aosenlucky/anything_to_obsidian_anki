from __future__ import annotations

from typing import Any

from app.config import AppConfig
from app.models import CaptureRequest

from .ai_processor import analyze_source_file
from .anki_card_generator import cards_from_analysis, save_pending_cards
from .ankiconnect_client import sync_cards
from .cloud_inbox_client import CloudInboxClient, CloudInboxItem
from .log_service import append_log
from .note_generator import write_notes_from_analysis
from .source_capture import capture_source


def pull_cloud_inbox(
    config: AppConfig,
    limit: int | None = None,
    process_ai: bool = False,
    sync_anki: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    inbox_config = config.section("cloud_inbox")
    resolved_limit = limit or int(inbox_config.get("poll_limit", 10))
    client = CloudInboxClient(config)
    items = client.list_queued(resolved_limit)
    results: list[dict[str, Any]] = []

    for item in items:
        source_path: str | None = None
        note_paths: list[str] = []
        try:
            if not dry_run:
                client.update_item(item.id, "claimed")
            source_path = _capture_item(config, item, dry_run=dry_run)
            cards = []
            if process_ai:
                analysis = analyze_source_file(config, source_path)
                note_paths = write_notes_from_analysis(config, source_path, analysis, dry_run=dry_run)
                cards = cards_from_analysis(config, analysis, source_path, note_paths)
                if not dry_run:
                    save_pending_cards(config, cards)
                if sync_anki:
                    sync_cards(config, cards, dry_run=dry_run)
            if not dry_run:
                client.update_item(item.id, "processed", source_path=source_path, note_paths=note_paths)
            results.append(
                {
                    "id": item.id,
                    "status": "processed",
                    "source_path": source_path,
                    "note_paths": note_paths,
                    "card_count": len(cards),
                }
            )
        except Exception as exc:
            if not dry_run:
                try:
                    client.update_item(item.id, "failed", source_path=source_path, note_paths=note_paths, error=str(exc))
                except Exception:
                    pass
            results.append({"id": item.id, "status": "failed", "source_path": source_path, "error": str(exc)})

    append_log(
        config.storage_dir,
        "pull_cloud_inbox",
        {
            "pulled": len(items),
            "processed": sum(1 for item in results if item["status"] == "processed"),
            "failed": sum(1 for item in results if item["status"] == "failed"),
            "dry_run": dry_run,
        },
    )
    return {"pulled": len(items), "results": results}


def _capture_item(config: AppConfig, item: CloudInboxItem, dry_run: bool = False) -> str:
    result = capture_source(
        config,
        CaptureRequest(
            source_type=item.source_type,  # type: ignore[arg-type]
            raw_input=item.raw_input,
            my_intent=item.my_intent or "",
            domain_hint=item.domain_hint,
            title=item.title,
            dry_run=dry_run,
        ),
    )
    return result.source_path
