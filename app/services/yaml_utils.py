from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def dump_frontmatter(data: dict[str, Any]) -> str:
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).strip()


def split_frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    if not markdown.startswith("---\n"):
        return {}, markdown
    end = markdown.find("\n---", 4)
    if end == -1:
        return {}, markdown
    raw_yaml = markdown[4:end]
    body = markdown[end + 4 :].lstrip("\n")
    return yaml.safe_load(raw_yaml) or {}, body


def read_markdown_with_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    return split_frontmatter(path.read_text(encoding="utf-8"))


def build_markdown(frontmatter: dict[str, Any], body: str) -> str:
    return f"---\n{dump_frontmatter(frontmatter)}\n---\n\n{body.strip()}\n"


def update_frontmatter(path: Path, updates: dict[str, Any]) -> None:
    metadata, body = read_markdown_with_frontmatter(path)
    metadata.update(updates)
    path.write_text(build_markdown(metadata, body), encoding="utf-8", newline="\n")
