from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from app.config import AppConfig

from .file_utils import ensure_dir, unique_path
from .yaml_utils import read_markdown_with_frontmatter


def _iter_notes(config: AppConfig) -> list[tuple[Path, dict[str, Any]]]:
    notes_root = config.vault_path / config.section("obsidian").get("notes_path", "20_Notes")
    if not notes_root.exists():
        return []
    records: list[tuple[Path, dict[str, Any]]] = []
    for path in notes_root.rglob("*.md"):
        metadata, _ = read_markdown_with_frontmatter(path)
        records.append((path, metadata))
    return records


def _is_this_week(value: Any) -> bool:
    try:
        dt = datetime.fromisoformat(str(value)).date()
        return dt.isocalendar()[:2] == date.today().isocalendar()[:2]
    except ValueError:
        return False


def _is_this_month(value: Any) -> bool:
    try:
        dt = datetime.fromisoformat(str(value)).date()
        today = date.today()
        return dt.year == today.year and dt.month == today.month
    except ValueError:
        return False


def generate_weekly_review(config: AppConfig, dry_run: bool = False) -> tuple[str, str]:
    if not config.vault_path.exists():
        raise FileNotFoundError(f"Obsidian Vault 路径不存在：{config.vault_path}")
    year, week, _ = date.today().isocalendar()
    filename = f"{year}-{week:02d}.md"
    target = config.vault_path / "50_Reviews" / "Weekly" / filename
    notes = [(p, m) for p, m in _iter_notes(config) if _is_this_week(m.get("created"))]
    high_value = [m.get("title", p.stem) for p, m in notes if m.get("priority") == "high"]
    questions = []
    for _, metadata in notes:
        questions.append(f"请复述：{metadata.get('title', '本周知识资产')} 的核心价值是什么？")
    content = f"""# Weekly Review - {year}-{week:02d}

## 1. AI 自动汇总

### 本周新增 Notes

{_lines([m.get("title", p.stem) for p, m in notes])}

### 本周新增 Anki 卡

{sum(int(m.get("anki_card_count") or 0) for _, m in notes)} 张

### 本周高价值知识

{_lines(high_value)}

### AI 推荐复习重点

{_lines(questions[:5])}

---

## 2. 主动回忆任务

请先不要打开对应笔记，尝试回答：

{_numbered(questions[:5])}

---

## 3. 我的复述记录

### 复述 1：


### 复述 2：


### 复述 3：


---

## 4. 本周输出任务

AI 推荐主题：

我的选择：

最终输出：

---

## 5. 下周行动

- [ ]
"""
    path = unique_path(target)
    if not dry_run:
        ensure_dir(path.parent)
        path.write_text(content, encoding="utf-8", newline="\n")
    return path.as_posix(), content


def generate_monthly_review(config: AppConfig, dry_run: bool = False) -> tuple[str, str]:
    if not config.vault_path.exists():
        raise FileNotFoundError(f"Obsidian Vault 路径不存在：{config.vault_path}")
    today = date.today()
    filename = f"{today:%Y-%m}.md"
    target = config.vault_path / "50_Reviews" / "Monthly" / filename
    notes = [(p, m) for p, m in _iter_notes(config) if _is_this_month(m.get("created"))]
    domains = Counter(str(m.get("domain", "General")) for _, m in notes)
    knowledge_types = Counter(str(m.get("knowledge_type", "概念型")) for _, m in notes)
    content = f"""# Monthly Review - {today:%Y-%m}

## 1. AI 自动汇总

### 本月新增知识资产

{_lines([m.get("title", p.stem) for p, m in notes])}

### 本月高频主题

{_lines([f"{name}: {count}" for name, count in domains.most_common()])}

### 本月重要案例

{_lines([m.get("title", p.stem) for p, m in notes if m.get("knowledge_type") == "案例型"])}

### 本月重要表达

{_lines([m.get("title", p.stem) for p, m in notes if m.get("knowledge_type") == "表达型"])}

### AI 推荐整合主题

{_lines([f"{name}: {count}" for name, count in knowledge_types.most_common(3)])}

---

## 2. 我的判断

本月最有价值的主题是：

本月应该删除或归档的内容：

本月真正形成能力的内容：

---

## 3. 月度体系化输出

主题：

结构：

关联 Notes：

最终输出：

---

## 4. 下月学习重点

1. 
2. 
3.
"""
    path = unique_path(target)
    if not dry_run:
        ensure_dir(path.parent)
        path.write_text(content, encoding="utf-8", newline="\n")
    return path.as_posix(), content


def _lines(items: list[Any]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- 暂无"


def _numbered(items: list[Any]) -> str:
    return "\n".join(f"{i}. {item}" for i, item in enumerate(items, 1)) if items else "1. 暂无"
