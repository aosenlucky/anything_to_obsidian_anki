from __future__ import annotations

from typing import Any

from .yaml_utils import build_markdown


def obsidian_link_from_path(path: str) -> str:
    name = path.replace("\\", "/").split("/")[-1]
    if name.endswith(".md"):
        name = name[:-3]
    return f"[[{name}]]"


def bullet_list(items: list[Any]) -> str:
    if not items:
        return "- 暂无"
    return "\n".join(f"- {item}" for item in items)


def numbered_list(items: list[Any]) -> str:
    if not items:
        return "1. 暂无"
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, 1))


def render_note_markdown(note: dict[str, Any], source_link: str, source_type: str) -> str:
    title = note.get("title") or "未命名知识资产"
    cards = note.get("anki_cards") or []
    card_lines = [
        f"- Q: {card.get('front', '')}\n  A: {card.get('back', '')}" for card in cards
    ]
    frontmatter = {
        "title": title,
        "domain": note.get("domain", "General"),
        "knowledge_type": note.get("knowledge_type", "概念型"),
        "source": source_link,
        "source_type": source_type,
        "priority": note.get("priority", "medium"),
        "created": note.get("created"),
        "last_review": None,
        "next_review": None,
        "anki_required": bool(note.get("anki_required", False)),
        "anki_sync_status": "pending" if note.get("anki_required") else "not_required",
        "anki_synced_at": None,
        "anki_card_count": len(cards),
        "review_method": note.get("review_method", "主动回忆"),
        "status": "active",
        "tags": note.get("tags", []),
    }
    body = f"""# {title}

## 一句话总结

{note.get("one_sentence_summary", "")}

## 核心内容

{note.get("core_content", "")}

## 适用场景

{bullet_list(note.get("use_cases", []))}

## 可复用表达

{bullet_list(note.get("reusable_expressions", []))}

## 主动回忆问题

{numbered_list(note.get("active_recall_questions", []))}

## 推荐 Anki 卡

{chr(10).join(card_lines) if card_lines else "- 暂无"}

## 关联笔记

{bullet_list(note.get("related_notes", []))}
"""
    return build_markdown(frontmatter, body)
