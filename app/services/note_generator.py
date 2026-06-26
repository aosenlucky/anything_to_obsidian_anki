from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from app.config import AppConfig

from .file_utils import sanitize_filename, write_text_safe
from .markdown_utils import obsidian_link_from_path, render_note_markdown
from .yaml_utils import update_frontmatter


NOTE_DOMAINS = {"Cloud", "AI", "English", "History", "General", "Parenting", "Travel", "Wealth"}


def write_notes_from_analysis(
    config: AppConfig,
    source_path: str | Path,
    analysis: dict[str, Any],
    dry_run: bool = False,
) -> list[str]:
    if not config.vault_path.exists():
        raise FileNotFoundError(f"Obsidian Vault 路径不存在：{config.vault_path}")
    source_abs = config.resolve_vault_path(source_path)
    source_rel = config.relative_to_vault(source_abs)
    source_link = obsidian_link_from_path(source_rel)
    notes_root = config.vault_path / config.section("obsidian").get("notes_path", "20_Notes")
    written: list[str] = []
    for note in analysis.get("notes", []):
        note["created"] = note.get("created") or date.today().isoformat()
        domain = note.get("domain") if note.get("domain") in NOTE_DOMAINS else None
        status = "active" if domain else "need_review"
        note["domain"] = domain or "General"
        target_dir = notes_root / note["domain"] if status == "active" else config.vault_path / "00_Inbox"
        markdown = render_note_markdown(note, source_link, _source_type_from_path(source_rel))
        if status != "active":
            markdown = markdown.replace("status: active", "status: need_review")
        filename = f"{sanitize_filename(note.get('title') or '未命名知识资产')}.md"
        saved = write_text_safe(target_dir / filename, markdown, dry_run=dry_run)
        written.append(config.relative_to_vault(saved))
    if written and not dry_run:
        update_frontmatter(source_abs, {"status": "processed", "processed_to": written})
    return written


def _source_type_from_path(source_rel: str) -> str:
    parts = source_rel.replace("\\", "/").split("/")
    return parts[1] if len(parts) > 1 else ""
