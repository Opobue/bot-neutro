#!/usr/bin/env python3
import argparse
import glob
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Tuple

SHA1_PATTERN = re.compile(r"^[a-fA-F0-9]{40}$")
TAG_CANDIDATES = {"file", "document"}
PATH_ATTRIBUTE_CANDIDATES = ("path", "file_path", "filename", "name")
PATH_ELEMENT_CANDIDATES = ("path", "file_path", "filename", "name")
CONTENT_ELEMENT_CANDIDATES = ("content", "text", "body")


def _exit_error(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(2)


def _read_head_sha(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            first_line = handle.readline()
    except FileNotFoundError:
        _exit_error(f"repomix head file not found: {path}")
    token = first_line.strip().split()
    if not token:
        _exit_error(f"repomix head file is empty: {path}")
    sha = token[0]
    if not SHA1_PATTERN.match(sha):
        _exit_error(f"invalid head sha: {sha}")
    return sha.lower()


def _clean_tag(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _first_child_text(element: ET.Element, names: Iterable[str]) -> str | None:
    for child in element:
        if _clean_tag(child.tag) in names:
            if child.text is None:
                return ""
            return child.text
    return None


def _strip_cdata(text: str) -> str:
    if text.startswith("<![CDATA[") and text.endswith("]]>"):
        return text[len("<![CDATA[") : -len("]]>")]
    return text


def _extract_entries_from_root(root: ET.Element) -> List[Tuple[str, str]]:
    entries: List[Tuple[str, str]] = []
    for element in root.iter():
        tag = _clean_tag(element.tag)
        if tag not in TAG_CANDIDATES:
            continue
        path = None
        for attribute in PATH_ATTRIBUTE_CANDIDATES:
            if element.get(attribute):
                path = element.get(attribute)
                break
        if path is None:
            path = _first_child_text(element, PATH_ELEMENT_CANDIDATES)
        if not path:
            continue
        content = _first_child_text(element, CONTENT_ELEMENT_CANDIDATES)
        if content is None:
            content = element.text
        if content is None:
            continue
        entries.append((path, _strip_cdata(content)))
    return entries


def _regex_fallback(content: str) -> List[Tuple[str, str]]:
    entries: List[Tuple[str, str]] = []
    for tag in ("file", "document"):
        pattern = re.compile(
            rf"<{tag}[^>]*?path=\"([^\"]+)\"[^>]*>(.*?)</{tag}>",
            re.DOTALL,
        )
        for match in pattern.findall(content):
            path, inner = match
            inner = re.sub(r"^\s*<content>", "", inner)
            inner = re.sub(r"</content>\s*$", "", inner)
            entries.append((path, _strip_cdata(inner)))
    return entries


def _parse_repomix_files(paths: List[str]) -> Dict[str, str]:
    files: Dict[str, str] = {}
    for path in paths:
        try:
            tree = ET.parse(path)
            entries = _extract_entries_from_root(tree.getroot())
        except ET.ParseError:
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    raw = handle.read()
            except FileNotFoundError:
                _exit_error(f"repomix xml not found: {path}")
            entries = _regex_fallback(raw)
        if not entries:
            _exit_error(f"no file entries found in repomix xml: {path}")
        for file_path, content in entries:
            if file_path in files and files[file_path] != content:
                _exit_error(f"conflicting content for file: {file_path}")
            files[file_path] = content
    return files


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _build_evidence(files: Dict[str, str]) -> Dict[str, Dict[str, object]]:
    evidence: Dict[str, Dict[str, object]] = {}
    for path in sorted(files):
        content = files[path]
        lines = content.splitlines()
        line_hashes = []
        for line in lines:
            normalized = line.rstrip("\r")
            line_hashes.append(_hash_text(normalized))
        evidence[path] = {
            "num_lines": len(lines),
            "file_sha256": _hash_text(content),
            "line_sha256": line_hashes,
        }
    return evidence


def _expand_repomix_patterns(patterns: Iterable[str]) -> List[str]:
    expanded: List[str] = []
    for pattern in patterns:
        matches = glob.glob(pattern)
        if matches:
            expanded.extend(matches)
        elif os.path.exists(pattern):
            expanded.append(pattern)
        else:
            _exit_error(f"repomix path not found: {pattern}")
    if not expanded:
        _exit_error("no repomix xml files resolved")
    return sorted(set(expanded))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build EvidencePack from Repomix XML.")
    parser.add_argument(
        "--repomix",
        nargs="+",
        required=True,
        help="Path(s) to repomix-output*.xml",
    )
    parser.add_argument("--head", required=True, help="Path to repomix-head.txt")
    parser.add_argument("--out", required=True, help="Output directory for evidence pack")
    args = parser.parse_args()

    head_sha = _read_head_sha(args.head)
    repomix_paths = _expand_repomix_patterns(args.repomix)
    files = _parse_repomix_files(repomix_paths)
    if not files:
        _exit_error("no files parsed from repomix xml")

    evidence = _build_evidence(files)
    payload = {
        "repo_head_sha": head_sha,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": evidence,
    }

    out_dir = os.path.join(args.out, head_sha)
    os.makedirs(out_dir, exist_ok=True)
    output_path = os.path.join(out_dir, "evidence_pack.json")
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)

    print(output_path)


if __name__ == "__main__":
    main()
