from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.config import PROJECT_ROOT, load_config
from app.models import CaptureRequest
from app.services.ai_processor import analyze_source_file
from app.services.anki_card_generator import cards_from_analysis, load_pending_cards, save_pending_cards
from app.services.ankiconnect_client import sync_cards
from app.services.cloud_inbox_processor import pull_cloud_inbox
from app.services.dashboard_generator import initialize_vault
from app.services.note_generator import write_notes_from_analysis
from app.services.review_generator import generate_monthly_review, generate_weekly_review
from app.services.source_capture import capture_source


def create_app():
    from fastapi import FastAPI
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    from app.api import routes_anki, routes_capture, routes_process, routes_review, routes_status

    api = FastAPI(title="Learning Asset Processor", version="0.1.0")
    api.include_router(routes_status.router)
    api.include_router(routes_capture.router)
    api.include_router(routes_process.router)
    api.include_router(routes_anki.router)
    api.include_router(routes_review.router)
    web_dir = PROJECT_ROOT / "app" / "web"
    api.mount("/static", StaticFiles(directory=web_dir), name="static")

    @api.get("/")
    def index() -> FileResponse:
        return FileResponse(web_dir / "index.html")

    return api


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    parser = argparse.ArgumentParser(prog="learning-asset-processor")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")

    serve_parser = sub.add_parser("serve")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)

    capture_parser = sub.add_parser("capture")
    capture_parser.add_argument("--type", required=True, choices=["book", "article", "video", "course", "conversation", "manual"])
    capture_parser.add_argument("--input-file", required=True)
    capture_parser.add_argument("--intent", default="")
    capture_parser.add_argument("--domain", default=None)
    capture_parser.add_argument("--title", default=None)
    capture_parser.add_argument("--dry-run", action="store_true")

    process_parser = sub.add_parser("process")
    process_parser.add_argument("--source", required=True)
    process_parser.add_argument("--dry-run", action="store_true")

    sync_parser = sub.add_parser("sync-anki")
    sync_parser.add_argument("--all", action="store_true")

    review_parser = sub.add_parser("review")
    review_parser.add_argument("--weekly", action="store_true")
    review_parser.add_argument("--monthly", action="store_true")

    run_parser = sub.add_parser("run")
    run_parser.add_argument("--type", required=True, choices=["book", "article", "video", "course", "conversation", "manual"])
    run_parser.add_argument("--input-file", required=True)
    run_parser.add_argument("--intent", default="")
    run_parser.add_argument("--domain", default=None)
    run_parser.add_argument("--title", default=None)
    run_parser.add_argument("--sync-anki", action="store_true")
    run_parser.add_argument("--dry-run", action="store_true")

    pull_parser = sub.add_parser("pull-inbox")
    pull_parser.add_argument("--limit", type=int, default=None)
    pull_parser.add_argument("--process-ai", action="store_true")
    pull_parser.add_argument("--sync-anki", action="store_true")
    pull_parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()
    config = load_config()

    if args.command == "init":
        paths = initialize_vault(config)
        print_json({"status": "ok", "created_or_existing": paths})
    elif args.command == "serve":
        import uvicorn

        uvicorn.run(create_app(), host=args.host, port=args.port, reload=False)
    elif args.command == "capture":
        raw_input = Path(args.input_file).read_text(encoding="utf-8")
        result = capture_source(
            config,
            CaptureRequest(
                source_type=args.type,
                raw_input=raw_input,
                my_intent=args.intent,
                domain_hint=args.domain,
                title=args.title,
                dry_run=args.dry_run,
            ),
        )
        print_json(result.model_dump())
    elif args.command == "process":
        analysis = analyze_source_file(config, args.source)
        note_paths = write_notes_from_analysis(config, args.source, analysis, dry_run=args.dry_run)
        cards = cards_from_analysis(config, analysis, args.source, note_paths)
        if not args.dry_run:
            save_pending_cards(config, cards)
        print_json({"analysis": analysis, "note_paths": note_paths, "cards": [c.model_dump() for c in cards]})
    elif args.command == "sync-anki":
        if not args.all:
            raise SystemExit("请传入 --all，或使用 Web UI 提交已确认卡片。")
        result = sync_cards(config, load_pending_cards(config))
        print_json(result.model_dump())
    elif args.command == "review":
        results = {}
        if args.weekly:
            results["weekly"] = generate_weekly_review(config)[0]
        if args.monthly:
            results["monthly"] = generate_monthly_review(config)[0]
        print_json(results)
    elif args.command == "run":
        raw_input = Path(args.input_file).read_text(encoding="utf-8")
        capture = capture_source(
            config,
            CaptureRequest(
                source_type=args.type,
                raw_input=raw_input,
                my_intent=args.intent,
                domain_hint=args.domain,
                title=args.title,
                dry_run=args.dry_run,
            ),
        )
        analysis = analyze_source_file(config, capture.source_path)
        note_paths = write_notes_from_analysis(config, capture.source_path, analysis, dry_run=args.dry_run)
        cards = cards_from_analysis(config, analysis, capture.source_path, note_paths)
        if not args.dry_run:
            save_pending_cards(config, cards)
        sync = sync_cards(config, cards, dry_run=args.dry_run) if args.sync_anki else None
        print_json(
            {
                "source": capture.model_dump(),
                "note_paths": note_paths,
                "cards": [card.model_dump() for card in cards],
                "sync": sync.model_dump() if sync else None,
            }
        )
    elif args.command == "pull-inbox":
        result = pull_cloud_inbox(
            config,
            limit=args.limit,
            process_ai=args.process_ai,
            sync_anki=args.sync_anki,
            dry_run=args.dry_run,
        )
        print_json(result)


def print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print_json({"status": "error", "error": str(exc)})
        raise SystemExit(1)
