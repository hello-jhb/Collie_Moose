"""Small file-hash cache and timing helpers for Moose pipeline stages."""

from __future__ import annotations

import hashlib
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, TypeVar


CACHE_VERSION = "moose_pipeline_v6"
CACHE_DIR = Path("cache/moose")

T = TypeVar("T")


def file_sha256(file_path: str | Path, chunk_size: int = 65_536) -> str:
    h = hashlib.sha256()
    with Path(file_path).open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def cache_key(file_hash: str, stage: str, options: dict[str, Any] | None = None) -> str:
    payload = {
        "version": CACHE_VERSION,
        "file_hash": file_hash,
        "stage": stage,
        "options": options or {},
    }
    encoded = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_stage(file_hash: str, stage: str, options: dict[str, Any] | None = None) -> dict[str, Any] | None:
    path = CACHE_DIR / stage / f"{cache_key(file_hash, stage, options)}.json"
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None


def save_stage(
    file_hash: str,
    stage: str,
    payload: Any,
    options: dict[str, Any] | None = None,
) -> None:
    stage_dir = CACHE_DIR / stage
    stage_dir.mkdir(parents=True, exist_ok=True)
    path = stage_dir / f"{cache_key(file_hash, stage, options)}.json"
    entry = {
        "version": CACHE_VERSION,
        "stage": stage,
        "file_hash": file_hash,
        "options": options or {},
        "cached_at": datetime.now(UTC).isoformat(),
        "payload": payload,
    }
    with path.open("w", encoding="utf-8") as handle:
        json.dump(entry, handle, indent=2, default=str)


def timed(label: str, timings: dict[str, dict[str, Any]], fn: Callable[[], T]) -> T:
    start = time.perf_counter()
    try:
        return fn()
    finally:
        timings[label] = {
            "seconds": round(time.perf_counter() - start, 4),
            "cache": "miss",
        }


def cached_stage(
    file_hash: str,
    stage: str,
    options: dict[str, Any] | None,
    timings: dict[str, dict[str, Any]],
    fn: Callable[[], T],
) -> T:
    start = time.perf_counter()
    cached = load_stage(file_hash, stage, options)
    if cached is not None:
        timings[stage] = {
            "seconds": round(time.perf_counter() - start, 4),
            "cache": "hit",
        }
        return cached["payload"]

    payload = fn()
    save_stage(file_hash, stage, payload, options)
    timings[stage] = {
        "seconds": round(time.perf_counter() - start, 4),
        "cache": "miss",
    }
    return payload
