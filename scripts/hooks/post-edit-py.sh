#!/usr/bin/env bash
# PostToolUse hook: run ruff on edited Python files
# Receives tool input JSON on stdin
FILE_PATH=$(cat | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))")
[[ "$FILE_PATH" == *.py ]] || exit 0
echo "--- ruff: $FILE_PATH ---"
uvx ruff check --fix "$FILE_PATH" && uvx ruff format "$FILE_PATH"
