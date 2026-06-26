from __future__ import annotations

from pathlib import Path

from app.config import AppConfig

from .file_utils import ensure_dir


DASHBOARDS = {
    "All Active Notes.md": """# All Active Notes

```dataview
TABLE domain, knowledge_type, priority, created, review_method
FROM "20_Notes"
WHERE status = "active"
SORT created DESC
```
""",
    "Anki Required.md": """# Anki Required

```dataview
TABLE domain, priority, anki_sync_status, anki_card_count, created
FROM "20_Notes"
WHERE anki_required = true
SORT anki_sync_status ASC, created DESC
```
""",
    "Case Library.md": """# Case Library

```dataview
TABLE domain, priority, created, review_method
FROM "20_Notes"
WHERE knowledge_type = "案例型"
SORT created DESC
```
""",
    "Expression Library.md": """# Expression Library

```dataview
TABLE domain, priority, created, review_method
FROM "20_Notes"
WHERE knowledge_type = "表达型"
SORT created DESC
```
""",
    "Weekly Output Candidates.md": """# Weekly Output Candidates

```dataview
TABLE domain, priority, created, review_method
FROM "20_Notes"
WHERE knowledge_type = "输出型" OR priority = "high"
SORT created DESC
```
""",
}


VAULT_DIRS = [
    "00_Inbox",
    "10_Sources/Books",
    "10_Sources/Articles",
    "10_Sources/Videos",
    "10_Sources/Courses",
    "10_Sources/Conversations",
    "10_Sources/Manual",
    "20_Notes/Cloud",
    "20_Notes/AI",
    "20_Notes/English",
    "20_Notes/History",
    "20_Notes/General",
    "20_Notes/Parenting",
    "20_Notes/Travel",
    "20_Notes/Wealth",
    "30_Life",
    "40_Actions/Output_Tasks",
    "40_Actions/Learning_Tasks",
    "50_Reviews/Weekly",
    "50_Reviews/Monthly",
    "50_Reviews/Dashboards",
    "90_System/Templates",
    "90_System/Prompts",
    "90_System/Scripts",
    "90_System/Configs",
    "99_Attachments",
]


def initialize_vault(config: AppConfig) -> list[str]:
    vault = config.vault_path
    if not vault.exists():
        raise FileNotFoundError(f"Obsidian Vault 路径不存在：{vault}")
    created: list[str] = []
    for relative in VAULT_DIRS:
        path = ensure_dir(vault / relative)
        created.append(path.as_posix())
    created.extend(generate_dashboards(config))
    return created


def generate_dashboards(config: AppConfig) -> list[str]:
    if not config.vault_path.exists():
        raise FileNotFoundError(f"Obsidian Vault 路径不存在：{config.vault_path}")
    dashboard_dir = ensure_dir(config.vault_path / "50_Reviews" / "Dashboards")
    written: list[str] = []
    for filename, content in DASHBOARDS.items():
        path = dashboard_dir / filename
        if not path.exists():
            path.write_text(content, encoding="utf-8", newline="\n")
        written.append(path.as_posix())
    return written
