from __future__ import annotations

import re
from datetime import date
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.config import AppConfig
from app.models import CaptureRequest, CaptureResult

from .file_utils import sanitize_filename, write_text_safe
from .yaml_utils import build_markdown


SOURCE_DIRS = {
    "book": ("Books", "书籍"),
    "article": ("Articles", "文章"),
    "video": ("Videos", "视频"),
    "course": ("Courses", "课程"),
    "conversation": ("Conversations", "对话"),
    "manual": ("Manual", "手动"),
}


URL_RE = re.compile(r"https?://[^\s)）>]+", re.IGNORECASE)


def extract_first_url(raw_input: str) -> str | None:
    match = URL_RE.search(raw_input)
    return match.group(0) if match else None


def _fetch_title(url: str) -> str | None:
    try:
        response = requests.get(url, timeout=8, headers={"User-Agent": "LearningAssetProcessor/1.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.find("title")
        if title and title.text.strip():
            return title.text.strip()
    except requests.RequestException:
        return None
    return None


def infer_title(request: CaptureRequest, source_url: str | None) -> str:
    if request.title and request.title.strip():
        return request.title.strip()
    if source_url:
        fetched = _fetch_title(source_url)
        if fetched:
            return fetched
        host = urlparse(source_url).netloc
        if host:
            return host
    first_line = next((line.strip() for line in request.raw_input.splitlines() if line.strip()), "")
    return first_line[:40] or "未命名材料"


def build_source_markdown(request: CaptureRequest, title: str, source_url: str | None) -> str:
    source_dir, source_name = SOURCE_DIRS[request.source_type]
    _ = source_dir
    metadata = {
        "title": title,
        "source_type": request.source_type,
        "source_url": source_url or "",
        "source_name": source_name,
        "created": date.today().isoformat(),
        "status": "unprocessed",
        "domain_hint": request.domain_hint or "",
        "my_intent": request.my_intent or "",
        "processed_to": [],
        "tags": [],
    }
    body = f"""# 原始内容

{request.raw_input.strip()}

# 我的初步想法

{request.my_intent.strip()}
"""
    return build_markdown(metadata, body)


def capture_source(config: AppConfig, request: CaptureRequest) -> CaptureResult:
    if not config.vault_path.exists():
        raise FileNotFoundError(f"Obsidian Vault 路径不存在：{config.vault_path}")
    source_url = extract_first_url(request.raw_input)
    title = infer_title(request, source_url)
    source_dir, source_name = SOURCE_DIRS[request.source_type]
    filename = f"{date.today().isoformat()}｜{sanitize_filename(title)}｜{source_name}.md"
    relative_dir = config.section("obsidian").get("sources_path", "10_Sources")
    target = config.vault_path / relative_dir / source_dir / filename
    markdown = build_source_markdown(request, title, source_url)
    saved = write_text_safe(target, markdown, dry_run=request.dry_run)
    return CaptureResult(
        source_path=config.relative_to_vault(saved),
        absolute_path=saved.as_posix(),
        title=title,
        source_url=source_url,
        dry_run=request.dry_run,
        markdown=markdown if request.dry_run else None,
    )
