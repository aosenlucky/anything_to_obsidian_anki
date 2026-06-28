from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


SourceType = Literal["book", "article", "video", "course", "conversation", "manual"]


class CaptureRequest(BaseModel):
    source_type: SourceType
    raw_input: str = Field(min_length=1)
    my_intent: str = ""
    domain_hint: str | None = None
    title: str | None = None
    dry_run: bool = False


class CaptureResult(BaseModel):
    source_path: str
    absolute_path: str
    title: str
    source_url: str | None = None
    dry_run: bool = False
    markdown: str | None = None


class ProcessRequest(BaseModel):
    source_path: str
    write_notes: bool = False
    dry_run: bool = False


class WriteNotesRequest(BaseModel):
    source_path: str
    analysis: dict[str, Any]
    dry_run: bool = False


class AnkiCard(BaseModel):
    deck: str
    note_type: str = "Basic"
    front: str
    back: str
    tags: list[str] = Field(default_factory=list)
    source_note: str = ""
    source: str = ""
    card_hash: str | None = None
    selected: bool = True


class ProcessResult(BaseModel):
    analysis: dict[str, Any]
    note_paths: list[str] = Field(default_factory=list)
    cards: list[AnkiCard] = Field(default_factory=list)
    needs_user_review: bool = False
    missing_information: list[str] = Field(default_factory=list)


class SyncRequest(BaseModel):
    cards: list[AnkiCard] = Field(default_factory=list)
    all_pending: bool = False
    dry_run: bool = False


class SyncResult(BaseModel):
    anki_available: bool
    synced: int = 0
    skipped_duplicates: int = 0
    failed: int = 0
    errors: list[str] = Field(default_factory=list)


class CloudPullRequest(BaseModel):
    process_ai: bool = False
    sync_anki: bool = False
    limit: int | None = None
    dry_run: bool = False


class AutomationRunRequest(BaseModel):
    mode: str | None = None
    trigger: str = "manual"


class AutomationSettingsRequest(BaseModel):
    enabled: bool | None = None
    mode: str | None = None


class StatusResult(BaseModel):
    deepseek: str
    anki: str
    obsidian: str
    config_path: str
    vault_path: str
