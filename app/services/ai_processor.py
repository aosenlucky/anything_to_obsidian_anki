from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from app.config import AppConfig
from app.prompts.source_analysis_prompt import build_source_analysis_prompt

from .ai_client import AIClientError, DeepSeekClient
from .log_service import append_log
from .yaml_utils import read_markdown_with_frontmatter, update_frontmatter


def analyze_source_file(config: AppConfig, source_path: str | Path) -> dict[str, Any]:
    path = config.resolve_vault_path(source_path)
    if not path.exists():
        raise FileNotFoundError(f"Source 文件不存在：{path}")
    source_markdown = path.read_text(encoding="utf-8")
    max_notes = int(config.section("processing").get("max_notes_per_source", 3))
    max_cards = int(config.section("processing").get("max_cards_per_note", 5))
    prompt = build_source_analysis_prompt(source_markdown, config.domains(), max_notes, max_cards)
    try:
        analysis = DeepSeekClient(config).analyze_source(prompt)
        _normalize_analysis(analysis, max_notes, max_cards)
        update_frontmatter(path, {"status": "processed_preview"})
        append_log(
            config.storage_dir,
            "process_source",
            {
                "source_file": config.relative_to_vault(path),
                "generated_notes": [n.get("title") for n in analysis.get("notes", [])],
                "generated_cards": sum(len(n.get("anki_cards", [])) for n in analysis.get("notes", [])),
                "status": "success",
            },
        )
        return analysis
    except AIClientError as exc:
        update_frontmatter(path, {"status": "need_review", "ai_error": str(exc)})
        append_log(
            config.storage_dir,
            "process_source",
            {"source_file": config.relative_to_vault(path), "status": "failed", "error": str(exc)},
        )
        raise


def load_source_metadata(config: AppConfig, source_path: str | Path) -> tuple[dict[str, Any], str]:
    return read_markdown_with_frontmatter(config.resolve_vault_path(source_path))


def _normalize_analysis(analysis: dict[str, Any], max_notes: int, max_cards: int) -> None:
    analysis.setdefault("needs_user_review", False)
    analysis.setdefault("missing_information", [])
    analysis.setdefault("notes", [])
    analysis["notes"] = analysis["notes"][:max_notes]
    for note in analysis["notes"]:
        note.setdefault("domain", analysis.get("domain", "General"))
        note.setdefault("knowledge_type", analysis.get("knowledge_type", "概念型"))
        note.setdefault("priority", analysis.get("priority", "medium"))
        note.setdefault("review_method", analysis.get("review_method", "主动回忆"))
        note.setdefault("tags", [])
        note.setdefault("created", date.today().isoformat())
        note["anki_cards"] = (note.get("anki_cards") or [])[:max_cards]
