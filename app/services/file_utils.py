from __future__ import annotations

import re
from pathlib import Path


WINDOWS_RESERVED = r'<>:"/\|?*'


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def sanitize_filename(value: str, fallback: str = "未命名材料") -> str:
    cleaned = re.sub(f"[{re.escape(WINDOWS_RESERVED)}]", " ", value).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip(". ")
    return cleaned[:90] or fallback


def unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    index = 2
    while True:
        candidate = parent / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text_safe(path: Path, content: str, dry_run: bool = False) -> Path:
    ensure_dir(path.parent)
    target = unique_path(path)
    if not dry_run:
        target.write_text(content, encoding="utf-8", newline="\n")
    return target
