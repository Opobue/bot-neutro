#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/llm/validate_llm_d1.sh -r|--repo-root <path> -s|--submission-slug <slug> -i|--llm-output-path <file> [--keep-submission]
USAGE
}

repo_root=""
submission_slug=""
llm_output_path=""
keep_submission="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--repo-root)
      repo_root="${2:-}"
      shift 2
      ;;
    -s|--submission-slug)
      submission_slug="${2:-}"
      shift 2
      ;;
    -i|--llm-output-path)
      llm_output_path="${2:-}"
      shift 2
      ;;
    --keep-submission)
      keep_submission="true"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "$repo_root" || -z "$submission_slug" || -z "$llm_output_path" ]]; then
  usage >&2
  exit 1
fi

run_external() {
  local label="$1"
  shift
  echo "==> ${label}"
  set +e
  local output
  output=$("$@" 2>&1)
  local status=$?
  set -e
  if [[ -n "$output" ]]; then
    printf '%s\n' "$output"
  fi
  if [[ $status -ne 0 ]]; then
    echo "Fallo en '${label}' (exit ${status})" >&2
    exit "$status"
  fi
}

run_external_capture() {
  local label="$1"
  shift
  echo "==> ${label}"
  set +e
  local output
  output=$("$@" 2>&1)
  local status=$?
  set -e
  if [[ -n "$output" ]]; then
    printf '%s\n' "$output"
  fi
  if [[ $status -ne 0 ]]; then
    echo "Fallo en '${label}' (exit ${status})" >&2
    exit "$status"
  fi
  printf '%s' "$output"
}

cd "$repo_root"

git status

if [[ -n "$(git status --porcelain)" ]]; then
  echo "WORKTREE NO LIMPIO: commitea o stash antes de validar. (git status --porcelain no vacío)" >&2
  exit 1
fi

run_external "git fetch" git fetch origin
run_external "git switch" git switch develop
run_external "git pull" git pull --ff-only

repomix_dir="$repo_root/docs/llm/repomix"
evidence_dir="$repo_root/docs/llm/evidence"
submissions_dir="$repo_root/docs/llm/submissions"

mkdir -p "$repomix_dir" "$evidence_dir" "$submissions_dir"

sha="$(git rev-parse HEAD)"
head_path="$repomix_dir/repomix-head.txt"
printf '%s' "$sha" > "$head_path"

rm -f "$repomix_dir"/repomix-output*.xml

run_external "repomix" npx --yes repomix --style xml --parsable-style --include-full-directory-structure \
  --include "docs/**,src/**,tests/**,scripts/**,.github/**,pyproject.toml,.gitignore,README*,LICENSE*" \
  --ignore "**/node_modules/**,**/.venv/**,**/.git/**,**/dist/**,**/build/**,**/.tmp_bench/**,**/__pycache__/**,**/.mypy_cache/**,**/.ruff_cache/**,**/.pytest_cache/**,**/docs/llm/repomix/**,**/docs/llm/evidence/**" \
  --split-output 20mb \
  -o "$repomix_dir/repomix-output.xml"

shopt -s nullglob
repomix_files=("$repomix_dir"/repomix-output*.xml)
shopt -u nullglob
if [[ ${#repomix_files[@]} -eq 0 ]]; then
  echo "Repomix no generó repomix-output*.xml en $repomix_dir" >&2
  exit 1
fi

if ! grep -q ".github/workflows" "${repomix_files[@]}"; then
  echo "FALTA .github/workflows en RepoPack" >&2
  exit 1
fi
if ! grep -q "pyproject.toml" "${repomix_files[@]}"; then
  echo "FALTA pyproject.toml en RepoPack" >&2
  exit 1
fi
if ! grep -q "\.gitignore" "${repomix_files[@]}"; then
  echo "FALTA .gitignore en RepoPack" >&2
  exit 1
fi

raw_evidence=$(run_external_capture "build evidence pack" python scripts/llm/build_evidence_pack.py \
  --repomix "${repomix_files[@]}" \
  --head "$head_path" \
  --out "$evidence_dir")

evidence_path=$(printf '%s\n' "$raw_evidence" | awk 'NF && /\.json$/ {last=$0} END {print last}')
if [[ -z "$evidence_path" ]]; then
  echo "build_evidence_pack.py no devolvió ruta .json. Salida: $raw_evidence" >&2
  exit 1
fi
if [[ ! "$evidence_path" =~ \.json$ ]]; then
  echo "EvidencePath no parece JSON: $evidence_path" >&2
  exit 1
fi
if [[ ! -f "$evidence_path" ]]; then
  echo "EvidencePack no existe en disco: $evidence_path" >&2
  exit 1
fi
printf 'EvidencePack => %s\n' "$evidence_path"

if [[ ! -f "$llm_output_path" ]]; then
  echo "LlmOutputPath no existe: $llm_output_path" >&2
  exit 1
fi

submission_path="$submissions_dir/${submission_slug}.md"
cat "$llm_output_path" > "$submission_path"
printf 'Submission => %s\n' "$submission_path"

run_external "lint D1 output" python scripts/llm/lint_d1_output.py "$submission_path" --evidence "$evidence_path"

echo "LINT OK ✅"
echo "PASS ✅"

if [[ "$keep_submission" != "true" ]]; then
  rm -f "$submission_path"
  echo "Submission removida (KeepSubmission=false)"
fi
