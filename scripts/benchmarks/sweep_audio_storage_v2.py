#!/usr/bin/env python3
"""Benchmark sweep de storage de audio (DESCUBRIR)."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List

from bot_neutro.audio_storage import FileAudioSessionRepository

DEFAULT_SESSIONS_LIST = "100,500,1000,2000,5000,10000,20000"
DEFAULT_PAYLOAD_BYTES_LIST = "0,256,1024"


def _percentile(sorted_values: List[float], percent: float) -> float:
    if not sorted_values:
        return 0.0
    if percent <= 0:
        return sorted_values[0]
    if percent >= 100:
        return sorted_values[-1]
    rank = (len(sorted_values) - 1) * (percent / 100)
    lower_index = int(rank)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]
    if upper_index == lower_index:
        return lower_value
    weight = rank - lower_index
    return lower_value + (upper_value - lower_value) * weight


def _configure_env() -> None:
    os.environ["AUDIO_SESSION_RETENTION_DAYS"] = "30"
    os.environ["AUDIO_SESSION_PURGE_ENABLED"] = "1"
    os.environ["AUDIO_SESSION_PERSIST_TRANSCRIPT"] = "0"
    os.environ["AUDIO_SESSION_PERSIST_REPLY_TEXT"] = "0"


def _parse_int_list(raw: str) -> List[int]:
    values: List[int] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        values.append(int(chunk))
    return values


def _build_payload(payload_bytes: int) -> Dict[str, str]:
    if payload_bytes <= 0:
        return {}
    return {"context": "x" * payload_bytes}


def _format_ms(seconds: float) -> float:
    return seconds * 1000


def _avg(values: Iterable[float]) -> float:
    values = list(values)
    return statistics.mean(values) if values else 0.0


def _run_once(
    sessions: int,
    payload_bytes: int,
    tmp_dir: Path,
    run_index: int,
) -> Dict[str, float]:
    storage_path = tmp_dir / f"audio_sessions_{sessions}_{payload_bytes}_run_{run_index}.json"
    if storage_path.exists():
        storage_path.unlink()
    repository = FileAudioSessionRepository(
        track_session_metrics=False,
        storage_path=str(storage_path),
    )
    durations_ms: List[float] = []
    payload = _build_payload(payload_bytes)

    start_total = time.perf_counter()
    for i in range(sessions):
        started = time.perf_counter()
        repository.create(
            {
                "id": f"session-{run_index}-{i}",
                "api_key_id": "bench-api-key",
                "user_external_id": "bench-user",
                "request_duration_seconds": 1.23,
                "client_meta": payload,
            }
        )
        durations_ms.append(_format_ms(time.perf_counter() - started))
    total_ms = _format_ms(time.perf_counter() - start_total)

    durations_ms.sort()
    p50_ms = _percentile(durations_ms, 50)
    p95_ms = _percentile(durations_ms, 95)
    file_size = storage_path.stat().st_size if storage_path.exists() else 0
    throughput = sessions / (total_ms / 1000) if total_ms > 0 else 0.0

    return {
        "run_index": float(run_index),
        "total_ms": total_ms,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "throughput_sessions_per_s": throughput,
        "storage_file_bytes": float(file_size),
    }


def _summarize_runs(runs: List[Dict[str, float]]) -> Dict[str, float]:
    return {
        "avg_total_ms": _avg([run["total_ms"] for run in runs]),
        "avg_p50_ms": _avg([run["p50_ms"] for run in runs]),
        "avg_p95_ms": _avg([run["p95_ms"] for run in runs]),
        "avg_throughput_sessions_per_s": _avg(
            [run["throughput_sessions_per_s"] for run in runs]
        ),
        "avg_storage_file_bytes": _avg([run["storage_file_bytes"] for run in runs]),
    }


def _build_budget_summary(
    budget_ms: float,
    avg_p95_ms: float,
) -> Dict[str, float | bool]:
    headroom = budget_ms - avg_p95_ms
    ratio = avg_p95_ms / budget_ms if budget_ms else 0.0
    return {
        "budget_ms": budget_ms,
        "p95_avg_ms": avg_p95_ms,
        "headroom_ms": headroom,
        "budget_ratio": ratio,
        "pass_budget": avg_p95_ms <= budget_ms if budget_ms else False,
    }


def _render_markdown(
    results: List[Dict[str, object]],
    output_path: Path,
    budget_ms: float,
    slo_ms: float,
    command: str,
) -> None:
    grouped: Dict[int, List[Dict[str, object]]] = {}
    for item in results:
        payload = int(item["payload_bytes"])
        grouped.setdefault(payload, []).append(item)

    lines: List[str] = []
    lines.append("# Storage sweep v2 (DESCUBRIR)")
    lines.append("")
    lines.append(f"- Command: `{command}`")
    lines.append(f"- SLO (audio_p95_ms): {slo_ms:.0f} ms")
    lines.append(f"- Budget p95 storage: {budget_ms:.0f} ms")
    lines.append("")

    for payload_bytes in sorted(grouped.keys()):
        lines.append(f"## Payload: {payload_bytes} bytes")
        lines.append("")
        lines.append(
            "| sessions | avg_p95_ms | avg_p50_ms | avg_throughput | file_size_mb | pass_budget | headroom_ms |"
        )
        lines.append(
            "| --- | --- | --- | --- | --- | --- | --- |"
        )
        failure_at: str | None = None
        for item in sorted(grouped[payload_bytes], key=lambda row: int(row["sessions"])):
            summary = item["summary"]
            budget = item["budget"]
            avg_p95_ms = float(summary["avg_p95_ms"])
            headroom_ms = float(budget["headroom_ms"])
            pass_budget = bool(budget["pass_budget"])
            if failure_at is None and not pass_budget:
                failure_at = str(int(item["sessions"]))
            file_size_mb = float(summary["avg_storage_file_bytes"]) / (1024 * 1024)
            lines.append(
                "| {sessions} | {avg_p95:.2f} | {avg_p50:.2f} | {throughput:.2f} | {file_size:.2f} | {pass_budget} | {headroom:.2f} |".format(
                    sessions=int(item["sessions"]),
                    avg_p95=avg_p95_ms,
                    avg_p50=float(summary["avg_p50_ms"]),
                    throughput=float(summary["avg_throughput_sessions_per_s"]),
                    file_size=file_size_mb,
                    pass_budget="✅" if pass_budget else "❌",
                    headroom=headroom_ms,
                )
            )
        if failure_at:
            lines.append("")
            lines.append(f"- Primer N donde falla presupuesto: {failure_at}")
        else:
            lines.append("")
            lines.append("- Presupuesto cumplido en todos los N.")
        lines.append("")

    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Sweep benchmark audio storage v2")
    parser.add_argument("--sessions-list", type=str, default=DEFAULT_SESSIONS_LIST)
    parser.add_argument("--payload-bytes-list", type=str, default=DEFAULT_PAYLOAD_BYTES_LIST)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--tmp-dir", type=str, default="./.tmp_bench/work")
    parser.add_argument("--keep-tmp", action="store_true")
    parser.add_argument(
        "--output-json",
        type=str,
        default="./.tmp_bench/out/storage_sweep_v2.json",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default="./.tmp_bench/out/storage_sweep_v2.md",
    )
    parser.add_argument("--slo-ms", type=float, default=1500)
    parser.add_argument("--budget-ms", type=float, default=250)
    parser.add_argument("--budget-ratio", type=float, default=None)

    args = parser.parse_args()

    _configure_env()

    sessions_list = _parse_int_list(args.sessions_list)
    payload_list = _parse_int_list(args.payload_bytes_list)

    budget_ms = args.budget_ms
    if args.budget_ratio is not None:
        budget_ms = args.slo_ms * args.budget_ratio

    command = " ".join(sys.argv)
    tmp_dir = Path(args.tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    results: List[Dict[str, object]] = []
    for payload_bytes in payload_list:
        for sessions in sessions_list:
            runs: List[Dict[str, float]] = []
            for run_index in range(1, args.runs + 1):
                runs.append(
                    _run_once(
                        sessions=sessions,
                        payload_bytes=payload_bytes,
                        tmp_dir=tmp_dir,
                        run_index=run_index,
                    )
                )
            summary = _summarize_runs(runs)
            budget = _build_budget_summary(budget_ms, summary["avg_p95_ms"])
            results.append(
                {
                    "sessions": sessions,
                    "payload_bytes": payload_bytes,
                    "runs": runs,
                    "summary": summary,
                    "budget": budget,
                }
            )

    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        git_sha = "unknown"

    output = {
        "benchmark": "audio_storage_sweep_v2",
        "timestamp_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "environment": {
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
        },
        "parameters": {
            "sessions_list": sessions_list,
            "payload_bytes_list": payload_list,
            "runs": args.runs,
            "tmp_dir": str(tmp_dir),
            "keep_tmp": args.keep_tmp,
            "slo_ms": args.slo_ms,
            "budget_ms": budget_ms,
            "budget_ratio": args.budget_ratio,
        },
        "git_sha": git_sha,
        "command": command,
        "results": results,
    }

    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if args.output_md:
        _render_markdown(
            results=results,
            output_path=Path(args.output_md),
            budget_ms=budget_ms,
            slo_ms=args.slo_ms,
            command=command,
        )

    if not args.keep_tmp:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
