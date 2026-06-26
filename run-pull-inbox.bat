@echo off
setlocal
cd /d "%~dp0"
call ".\.venv\Scripts\activate.bat"
python -m app.main pull-inbox --process-ai --sync-anki
