from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import AppConfig
from app.models import AnkiCard

from .hash_utils import sha256_text


CARD_LIMITS = {
    "事实型": 5,
    "概念型": 4,
    "方法型": 3,
    "案例型": 4,
    "表达型": 5,
    "输出型": 2,
}


def cards_from_analysis(
    config: AppConfig,
    analysis: dict[str, Any],
    source_path: str | Path,
    note_paths: list[str] | None = None,
) -> list[AnkiCard]:
    anki_config = config.section("anki")
    deck_prefix = anki_config.get("default_deck_prefix", "Learning")
    note_type = anki_config.get("note_type", "Basic")
    source_rel = config.relative_to_vault(config.resolve_vault_path(source_path))
    cards: list[AnkiCard] = []
    note_paths = note_paths or []
    for index, note in enumerate(analysis.get("notes", [])):
        knowledge_type = note.get("knowledge_type", analysis.get("knowledge_type", "概念型"))
        limit = min(CARD_LIMITS.get(knowledge_type, 3), int(config.section("processing").get("max_cards_per_note", 5)))
        domain = note.get("domain", analysis.get("domain", "General"))
        deck = f"{deck_prefix}::{domain}"
        source_note = note_paths[index] if index < len(note_paths) else ""
        for raw_card in (note.get("anki_cards") or [])[:limit]:
            front = str(raw_card.get("front", "")).strip()
            back = str(raw_card.get("back", "")).strip()
            if not front or not back:
                continue
            card_hash = sha256_text(front + back + source_note)
            tags = [str(tag).replace(" ", "_") for tag in raw_card.get("tags", [])]
            cards.append(
                AnkiCard(
                    deck=deck,
                    note_type=note_type,
                    front=front,
                    back=back,
                    tags=tags,
                    source_note=source_note,
                    source=source_rel,
                    card_hash=card_hash,
                )
            )
    return cards


def save_pending_cards(config: AppConfig, cards: list[AnkiCard]) -> None:
    path = config.storage_dir / "pending_cards.json"
    existing = load_pending_cards(config)
    by_hash = {card.card_hash: card for card in existing if card.card_hash}
    for card in cards:
        by_hash[card.card_hash or sha256_text(card.front + card.back + card.source_note)] = card
    path.write_text(
        json.dumps([card.model_dump() for card in by_hash.values()], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_pending_cards(config: AppConfig) -> list[AnkiCard]:
    path = config.storage_dir / "pending_cards.json"
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [AnkiCard(**item) for item in raw if isinstance(item, dict)]
