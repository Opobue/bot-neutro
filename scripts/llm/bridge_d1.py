#!/usr/bin/env python3
"""
BRIDGE D1: Traductor de evidencia humana (texto) a evidencia criptográfica (hash).
Convierte (EVIDENCIA_TXT: ...) -> (EVIDENCIA: ...#SHA256:...)
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# Grupo 1: path
# Grupo 2: comilla de apertura (para backref)
# Grupo 3: snippet
PATTERN_TXT = re.compile(r"\(EVIDENCIA_TXT:\s*([^\s\)]+)\s*([\"'])(.*?)\2\)")


@dataclass(frozen=True)
class EvidenceMatch:
    full_text: str
    path: str
    snippet: str


def sha256_line(line: str) -> str:
    normalized = line.strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def parse_evidences(markdown: str, strict: bool) -> list[EvidenceMatch]:
    matches: list[EvidenceMatch] = []
    for m in PATTERN_TXT.finditer(markdown):
        matches.append(EvidenceMatch(full_text=m.group(0), path=m.group(1), snippet=m.group(3)))

    if strict:
        # Si aparece "EVIDENCIA_TXT" pero no matcheó el patrón completo → sintaxis mal formada
        for occ in re.finditer(r"EVIDENCIA_TXT", markdown):
            if not any(occ.start() >= m.start() and occ.start() < m.end() for m in PATTERN_TXT.finditer(markdown)):
                raise ValueError(f"EVIDENCIA_TXT mal formada cerca de índice {occ.start()}")

    return matches


def hash_from_file(repo_root: Path, rel_path: str, snippet: str, require_unique: bool) -> str:
    target = repo_root / rel_path
    if not target.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {rel_path}")

    try:
        lines = target.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()

    needle = snippet.strip()
    hits = [ln for ln in lines if ln.strip() == needle]

    if not hits:
        partial = any(needle in ln for ln in lines)
        msg = f"Snippet no encontrado como línea exacta (strip match) en {rel_path}: '{needle}'"
        if partial:
            msg += " (existe parcial, pero Bridge exige coincidencia exacta por línea)"
        raise ValueError(msg)

    if require_unique and len(hits) != 1:
        raise ValueError(f"Snippet no es único en {rel_path} (matches={len(hits)}): '{needle}'")

    return sha256_line(hits[0])


def convert(markdown: str, repo_root: Path, require_unique: bool, strict: bool) -> str:
    evidences = parse_evidences(markdown, strict)
    if not evidences:
        return markdown

    converted = markdown
    for ev in evidences:
        h = hash_from_file(repo_root, ev.path, ev.snippet, require_unique)
        converted = converted.replace(ev.full_text, f"(EVIDENCIA: {ev.path}#SHA256:{h})")
    return converted


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_md")
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", required=True)
    ap.add_argument("--require-unique", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--strict", action=argparse.BooleanOptionalAction, default=True)
    args = ap.parse_args()

    in_path = Path(args.input_md)
    out_path = Path(args.out)
    root = Path(args.root)

    if not in_path.exists():
        print(f"Archivo no encontrado: {in_path}", file=sys.stderr)
        return 1

    try:
        md = in_path.read_text(encoding="utf-8")
        bridged = convert(md, root, args.require_unique, args.strict)
        out_path.write_text(bridged, encoding="utf-8")
    except Exception as e:
        print(f"FATAL: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
