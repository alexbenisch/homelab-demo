#!/usr/bin/env bash
# PostToolUse hook: dry-run validate Kubernetes YAML after edits
# Receives tool input JSON on stdin
FILE_PATH=$(cat | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))")
[[ "$FILE_PATH" == *.yaml || "$FILE_PATH" == *.yml ]] || exit 0
[[ "$FILE_PATH" == *apps/* || "$FILE_PATH" == *k8s/* ]] || exit 0
echo "--- kubectl dry-run: $FILE_PATH ---"
kubectl apply --dry-run=client -f "$FILE_PATH" 2>&1
