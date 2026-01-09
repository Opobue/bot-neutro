#!/usr/bin/env python3
import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

HEADER_PATTERN = re.compile(r"^TIPO=DESCUBRIR · OBJ=.+ · ALCANCE=.+$")
REQUIRED_SECTIONS = [
    "## 1. CONTEXTO Y ALCANCE",
    "## 2. HALLAZGOS (HECHOS)",
    "## 3. INCERTIDUMBRES Y PREGUNTAS",
    "## 4. RIESGOS Y OPORTUNIDADES (PRELIMINAR)",
    "## 5. GATE D1→D2",
]
GATE_SECTION = "## 5. GATE D1→D2"
GATE_SUBSECTIONS = [
    "### TOP 3 Bloqueos",
    "### TOP 3 Riesgos Antigravity",
    "### TOP 3 Oportunidades",
    "### Siguiente Acción Recomendada",
    "### Listo para D2",
]
TOP3_HEADINGS = {
    "### TOP 3 Bloqueos": "bloqueos",
    "### TOP 3 Riesgos Antigravity": "riesgos antigravity",
    "### TOP 3 Oportunidades": "oportunidades",
}
OPPORTUNITY_LABELS = {"[HECHO]", "[INFERENCIA]", "[HIPÓTESIS]", "[DESCONOCIDO]"}
PROHIBITED_PHRASES = ["Sin evidencia"]
LIST_ITEM_PATTERN = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+(.+)$")
EVIDENCE_RANGE_PATTERN = re.compile(r"EVIDENCIA:\s*([^\s#)]+):L(\d+)-L(\d+)")
EVIDENCE_HASH_PATTERN = re.compile(r"EVIDENCIA:\s*([^\s#)]+)#SHA256:([a-fA-F0-9]{64})")
READY_PATTERN = re.compile(r"^Listo para D2:\s*(Sí|No)\s*(?:—|-).+")


@dataclass(frozen=True)
class EvidenceFile:
    num_lines: int
    file_sha256: str
    line_sha256: set[str]


@dataclass
class LintError:
    path: Path
    line: int
    message: str


def _exit_with_errors(errors: Iterable[LintError]) -> None:
    for error in errors:
        print(f"{error.path}:{error.line}: {error.message}", file=sys.stderr)
    raise SystemExit(2)


def _load_evidence(path: Path) -> Dict[str, EvidenceFile]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"evidence pack not found: {path}") from exc
    files = data.get("files")
    if not isinstance(files, dict):
        raise SystemExit("evidence pack missing files map")
    evidence: Dict[str, EvidenceFile] = {}
    for file_path, payload in files.items():
        if not isinstance(payload, dict):
            continue
        num_lines = int(payload.get("num_lines", 0))
        file_sha = str(payload.get("file_sha256", ""))
        line_hashes = payload.get("line_sha256", [])
        evidence[file_path] = EvidenceFile(
            num_lines=num_lines,
            file_sha256=file_sha,
            line_sha256=set(map(str, line_hashes)),
        )
    return evidence


def _first_non_empty_line(lines: List[str]) -> Tuple[int, str] | None:
    for idx, line in enumerate(lines, start=1):
        if line.strip():
            return idx, line.rstrip("\n")
    return None


def _find_section_indices(lines: List[str], sections: List[str]) -> Dict[str, int]:
    indices: Dict[str, int] = {}
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped in sections and stripped not in indices:
            indices[stripped] = idx
    return indices


def _collect_section_block(lines: List[str], start_idx: int) -> List[Tuple[int, str]]:
    block: List[Tuple[int, str]] = []
    for idx in range(start_idx, len(lines) + 1):
        if idx != start_idx and lines[idx - 1].strip().startswith("## "):
            break
        block.append((idx, lines[idx - 1]))
    return block


def _validate_header(lines: List[str], path: Path, errors: List[LintError]) -> None:
    header = _first_non_empty_line(lines)
    if header is None:
        errors.append(LintError(path, 1, "archivo vacío"))
        return
    line_number, line = header
    if not HEADER_PATTERN.match(line.strip()):
        errors.append(
            LintError(
                path,
                line_number,
                "encabezado inválido; se espera 'TIPO=DESCUBRIR · OBJ=... · ALCANCE=...'",
            )
        )


def _validate_sections(lines: List[str], path: Path, errors: List[LintError]) -> Dict[str, int]:
    indices = _find_section_indices(lines, REQUIRED_SECTIONS)
    for section in REQUIRED_SECTIONS:
        if section not in indices:
            errors.append(LintError(path, 1, f"falta sección obligatoria: {section}"))
    positions = [indices.get(section, 0) for section in REQUIRED_SECTIONS]
    if all(positions):
        if positions != sorted(positions):
            errors.append(LintError(path, positions[0], "secciones fuera de orden"))
    return indices


def _validate_prohibitions(lines: List[str], path: Path, errors: List[LintError]) -> None:
    for idx, line in enumerate(lines, start=1):
        for phrase in PROHIBITED_PHRASES:
            if phrase in line:
                errors.append(LintError(path, idx, f"frase prohibida: {phrase}"))


def _collect_heading_block(
    lines: List[str],
    start_line: int,
    heading_prefix: str = "### ",
) -> List[Tuple[int, str]]:
    block: List[Tuple[int, str]] = []
    for idx in range(start_line, len(lines) + 1):
        line = lines[idx - 1]
        if idx != start_line and line.strip().startswith(heading_prefix):
            break
        if idx != start_line and line.strip().startswith("## "):
            break
        block.append((idx, line))
    return block


def _count_list_items(block: Iterable[Tuple[int, str]]) -> List[Tuple[int, str]]:
    items = []
    for idx, line in block:
        match = LIST_ITEM_PATTERN.match(line)
        if match:
            items.append((idx, match.group(1).strip()))
    return items


def _validate_gate(
    lines: List[str],
    path: Path,
    indices: Dict[str, int],
    errors: List[LintError],
) -> None:
    gate_start = indices.get(GATE_SECTION)
    if not gate_start:
        return
    gate_block = _collect_section_block(lines, gate_start)
    gate_indices = _find_section_indices([line for _, line in gate_block], GATE_SUBSECTIONS)
    for subsection in GATE_SUBSECTIONS:
        if subsection not in gate_indices:
            errors.append(LintError(path, gate_start, f"falta subsección en Gate: {subsection}"))

    for idx, line in gate_block:
        if "Ninguno probado" in line:
            errors.append(LintError(path, idx, "'Ninguno probado' no permitido en Gate"))

    if "### Listo para D2" in gate_indices:
        block_start = gate_start + gate_indices["### Listo para D2"] - 1
        ready_block = _collect_heading_block(lines, block_start)
        if not any(READY_PATTERN.match(line.strip()) for _, line in ready_block):
            errors.append(LintError(path, block_start, "falta 'Listo para D2: Sí/No — razón'"))

    for heading in TOP3_HEADINGS:
        if heading not in gate_indices:
            continue
        block_start = gate_start + gate_indices[heading] - 1
        items = _count_list_items(_collect_heading_block(lines, block_start))
        if len(items) < 3:
            errors.append(
                LintError(
                    path,
                    block_start,
                    f"{heading} requiere al menos 3 ítems",
                )
            )
        if heading == "### TOP 3 Oportunidades":
            for item_line, item_text in items:
                if not any(item_text.startswith(label) for label in OPPORTUNITY_LABELS):
                    errors.append(
                        LintError(
                            path,
                            item_line,
                            "cada oportunidad debe iniciar con [HECHO]/[INFERENCIA]/"
                            "[HIPÓTESIS]/[DESCONOCIDO]",
                        )
                    )


def _validate_hechos(
    lines: List[str],
    path: Path,
    evidence: Dict[str, EvidenceFile],
    errors: List[LintError],
) -> None:
    for idx, line in enumerate(lines, start=1):
        if not line.lstrip().startswith("HECHO:"):
            continue
        range_matches = EVIDENCE_RANGE_PATTERN.findall(line)
        hash_matches = EVIDENCE_HASH_PATTERN.findall(line)
        if not range_matches and not hash_matches:
            errors.append(LintError(path, idx, "HECHO sin evidencia válida"))
            continue
        for file_path, start, end in range_matches:
            if file_path not in evidence:
                errors.append(
                    LintError(path, idx, f"archivo no encontrado en evidencia: {file_path}")
                )
                continue
            start_line = int(start)
            end_line = int(end)
            file_info = evidence[file_path]
            if start_line < 1 or end_line < 1 or start_line > end_line:
                errors.append(LintError(path, idx, "rango de evidencia inválido"))
                continue
            if end_line > file_info.num_lines:
                errors.append(LintError(path, idx, "rango de evidencia fuera de límites"))
        for file_path, hash_value in hash_matches:
            if file_path not in evidence:
                errors.append(
                    LintError(path, idx, f"archivo no encontrado en evidencia: {file_path}")
                )
                continue
            file_info = evidence[file_path]
            if hash_value not in file_info.line_sha256 and hash_value != file_info.file_sha256:
                errors.append(LintError(path, idx, "hash de evidencia no encontrado"))


def _lint_file(path: Path, evidence: Dict[str, EvidenceFile]) -> List[LintError]:
    lines = path.read_text(encoding="utf-8").splitlines()
    errors: List[LintError] = []
    _validate_header(lines, path, errors)
    indices = _validate_sections(lines, path, errors)
    _validate_prohibitions(lines, path, errors)
    _validate_gate(lines, path, indices, errors)
    _validate_hechos(lines, path, evidence, errors)
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Lint D1 outputs against EvidencePack.")
    parser.add_argument("md_files", nargs="+", help="Markdown submissions to validate")
    parser.add_argument("--evidence", required=True, help="Path to evidence_pack.json")
    args = parser.parse_args()

    evidence = _load_evidence(Path(args.evidence))
    all_errors: List[LintError] = []
    for md_file in args.md_files:
        path = Path(md_file)
        if not path.exists():
            all_errors.append(LintError(path, 1, "archivo no encontrado"))
            continue
        all_errors.extend(_lint_file(path, evidence))

    if all_errors:
        _exit_with_errors(all_errors)


if __name__ == "__main__":
    main()
