from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

from app.config import AppConfig
from app.models import AnkiCard, SyncResult

from .hash_utils import sha256_text
from .yaml_utils import update_frontmatter


class AnkiConnectClient:
    def __init__(self, config: AppConfig):
        self.config = config
        self.url = config.section("anki").get("ankiconnect_url", "http://127.0.0.1:8765")

    def request(self, action: str, params: dict[str, Any] | None = None) -> Any:
        payload = {"action": action, "version": 6, "params": params or {}}
        session = requests.Session()
        session.trust_env = False
        response = session.post(self.url, json=payload, timeout=8)
        response.raise_for_status()
        data = response.json()
        if data.get("error"):
            raise RuntimeError(data["error"])
        return data.get("result")

    def is_available(self) -> bool:
        try:
            return int(self.request("version")) >= 6
        except Exception:
            return False

    def deck_names(self) -> list[str]:
        return list(self.request("deckNames") or [])

    def model_field_names(self, model_name: str) -> list[str]:
        return list(self.request("modelFieldNames", {"modelName": model_name}) or [])

    def ensure_deck(self, deck: str) -> None:
        if deck not in self.deck_names():
            self.request("createDeck", {"deck": deck})

    def add_basic_card(self, card: AnkiCard) -> int:
        self.ensure_deck(card.deck)
        model_fields = set(self.model_field_names(card.note_type))
        fields = {
            "Front": _format_front(card.front),
            "Back": _format_back(card.back),
        }
        if "Source" in model_fields:
            fields["Source"] = html.escape(_short_source(card.source_note or card.source))
        if "Section" in model_fields:
            fields["Section"] = ""
        payload = {
            "note": {
                "deckName": card.deck,
                "modelName": card.note_type,
                "fields": fields,
                "tags": card.tags,
                "options": {"allowDuplicate": False},
            }
        }
        return int(self.request("addNote", payload))


def sync_cards(config: AppConfig, cards: list[AnkiCard], dry_run: bool = False) -> SyncResult:
    selected = [card for card in cards if card.selected]
    if dry_run:
        return SyncResult(anki_available=False, synced=0, skipped_duplicates=0, failed=0)

    client = AnkiConnectClient(config)
    if not client.is_available():
        return SyncResult(anki_available=False, errors=["AnkiConnect 未连接，请确认 Anki 已启动并安装 AnkiConnect。"])

    db_path = config.storage_dir / "card_db.json"
    db = _load_db(db_path)
    synced = 0
    skipped = 0
    failed = 0
    errors: list[str] = []
    synced_by_note: dict[str, int] = {}
    for card in selected:
        card_hash = card.card_hash or sha256_text(card.front + card.back + card.source_note)
        if card_hash in db:
            skipped += 1
            continue
        try:
            note_id = client.add_basic_card(card)
            db[card_hash] = {
                "anki_note_id": note_id,
                "front": card.front,
                "source_note": card.source_note,
                "synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            synced += 1
            if card.source_note:
                synced_by_note[card.source_note] = synced_by_note.get(card.source_note, 0) + 1
        except Exception as exc:
            failed += 1
            errors.append(f"{card.front}: {exc}")

    _save_db(db_path, db)
    for note_path, count in synced_by_note.items():
        try:
            update_frontmatter(
                config.resolve_vault_path(note_path),
                {
                    "anki_required": True,
                    "anki_sync_status": "synced",
                    "anki_synced_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "anki_card_count": count,
                },
            )
        except Exception as exc:
            errors.append(f"更新 Note YAML 失败 {note_path}: {exc}")

    return SyncResult(
        anki_available=True,
        synced=synced,
        skipped_duplicates=skipped,
        failed=failed,
        errors=errors,
    )


def _load_db(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _save_db(path: Path, db: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


def _format_front(value: str) -> str:
    text = html.escape(value.strip())
    return f'<div class="lap-front">{text}</div>'


def _format_back(value: str) -> str:
    paragraphs = [part.strip() for part in value.splitlines() if part.strip()]
    if not paragraphs:
        paragraphs = [value.strip()]
    body = "".join(f"<p>{html.escape(part)}</p>" for part in paragraphs)
    return f'<div class="lap-answer">{body}</div>'


def _short_source(value: str) -> str:
    if not value:
        return ""
    stem = Path(value).stem
    return stem[:72]
