"""Local cache under ~/.onchain (override with ONCHAIN_HOME). Nothing is hosted anywhere else."""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path


def home() -> Path:
    p = Path(os.environ.get("ONCHAIN_HOME", Path.home() / ".onchain"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def path(*parts: str) -> Path:
    p = home().joinpath(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def read_json(p: Path, ttl: float | None = None):
    if not p.exists():
        return None
    if ttl is not None and time.time() - p.stat().st_mtime > ttl:
        return None
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def write_json(p: Path, obj) -> None:
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, separators=(",", ":")))
    tmp.replace(p)


def cached(key: str, ttl: float, fn):
    """Generic TTL cache for small JSON responses."""
    h = hashlib.sha256(key.encode()).hexdigest()[:24]
    p = path("http", f"{h}.json")
    if not os.environ.get("ONCHAIN_REFRESH"):
        hit = read_json(p, ttl)
        if hit is not None:
            return hit["v"]
    if os.environ.get("ONCHAIN_OFFLINE"):
        hit = read_json(p)
        if hit is not None:
            return hit["v"]
        raise RuntimeError(f"offline and not cached: {key}")
    v = fn()
    write_json(p, {"k": key, "t": time.time(), "v": v})
    return v
