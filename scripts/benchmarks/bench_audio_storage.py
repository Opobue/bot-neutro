#!/usr/bin/env python3
"""Benchmark reproducible para audio_storage (DESCUBRIR).

Hipótesis de complejidad:
- FileAudioSessionRepository.create() invoca purge_expired() y _persist() en cada sesión.
- _persist() re-serializa y reescribe el JSON completo con todas las sesiones.
- Complejidad esperada: O(N) por sesión (y O(N^2) total al insertar N sesiones).

Puntos de persistencia (ver src/bot_neutro/audio_storage.py):
- FileAudioSessionRepository.create() -> self._persist()
- FileAudioSessionRepository._persist() escribe el archivo completo.
"""

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
from typing import Dict, List

ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT_DIR / "src"))

from bot_neutro.audio_storage import FileAudioSessionRepository  # noqa: E402


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


def _build_payload(payload_bytes: int) -> Dict[str, str]:
    if payload_bytes <= 0:
        return {}
    return {"context": "x" * payload_bytes}


def _format_ms(seconds: float) -> float:
    return seconds * 1000


def _run_once(
    sessions: int,
    payload_bytes: int,
    tmp_dir: Path,
    run_index: int,
) -> Dict[str, float]:
    storage_path = tmp_dir / f"audio_sessions_run_{run_index}.json"
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
        "total_ms": total_ms,
        "p50_ms": p50_ms,
        "p95_ms": p95_ms,
        "throughput_sessions_per_s": throughput,
        "storage_file_bytes": float(file_size),
    }


def _summarize_runs(runs: List[Dict[str, float]]) -> Dict[str, float]:
    def avg(values: List[float]) -> float:
        return statistics.mean(values) if values else 0.0

    return {
        "avg_total_ms": avg([run["total_ms"] for run in runs]),
        "avg_p50_ms": avg([run["p50_ms"] for run in runs]),
        "avg_p95_ms": avg([run["p95_ms"] for run in runs]),
        "avg_throughput_sessions_per_s": avg(
            [run["throughput_sessions_per_s"] for run in runs]
        ),
        "avg_storage_file_bytes": avg([run["storage_file_bytes"] for run in runs]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark audio session storage")
    parser.add_argument("--sessions", type=int, default=5000)
    parser.add_argument("--payload-bytes", type=int, default=1024)
    parser.add_argument("--tmp-dir", type=str, default="./.tmp_bench")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--keep-tmp", action="store_true")
    parser.add_argument(
        "--output",
        type=str,
        default="docs/benchmarks/storage_baseline.json",
    )

    args = parser.parse_args()
    command = " ".join(sys.argv)

    _configure_env()

    tmp_dir = Path(args.tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    runs: List[Dict[str, float]] = []
    for run_index in range(1, args.runs + 1):
        runs.append(
            _run_once(
                sessions=args.sessions,
                payload_bytes=args.payload_bytes,
                tmp_dir=tmp_dir,
                run_index=run_index,
            )
        )

    summary = _summarize_runs(runs)
    try:
        git_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT_DIR,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        git_sha = "unknown"
    output = {
        "benchmark": "audio_storage",
        "timestamp_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "environment": {
            "python_version": sys.version.split()[0],
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
        },
        "parameters": {
            "sessions": args.sessions,
            "payload_bytes": args.payload_bytes,
            "runs": args.runs,
            "tmp_dir": str(tmp_dir),
        },
        "git_sha": git_sha,
        "command": command,
        "runs": runs,
        "summary": summary,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if not args.keep_tmp:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
