#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Uso: $0 <submission_md> [--bridge]" >&2
}

bridge=false
args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --bridge)
      bridge=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      args+=("$1")
      shift
      ;;
  esac
done

if [[ ${#args[@]} -lt 1 ]]; then
  usage
  exit 1
fi

submission_path="${args[0]}"

repo_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
bridge_script="$repo_root/scripts/llm/bridge_d1.py"
lint_script="$repo_root/scripts/llm/lint_d1_output.py"
evidence_dir="$repo_root/docs/llm/evidence"
evidence_file=$(find "$evidence_dir" -type f -name "*.json" -print0 2>/dev/null | xargs -0 ls -t 2>/dev/null | head -n 1 || true)

if [[ -z "$evidence_file" ]]; then
  echo "❌ No se encontró EvidencePack en $evidence_dir" >&2
  exit 1
fi

if [[ "$bridge" == "true" ]]; then
  bridged_path="${submission_path}.bridge.md"
  python "$bridge_script" "$submission_path" --root "$repo_root" --out "$bridged_path"
  python "$lint_script" "$bridged_path" --evidence "$evidence_file"
else
  python "$lint_script" "$submission_path" --evidence "$evidence_file"
fi
