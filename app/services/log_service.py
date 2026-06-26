from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def append_log(storage_dir: Path, action: str, payload: dict[str, Any]) -> None:
    path = storage_dir / "processing_log.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            records = []
    else:
        records = []
    clean_payload = {k: v for k, v in payload.items() if "api_key" not in k.lower()}
    records.append(
        {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            **clean_payload,
        }
    )
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
