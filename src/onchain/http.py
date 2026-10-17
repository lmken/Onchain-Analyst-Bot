"""Minimal stdlib HTTP client: JSON GET/POST, retries with backoff, per-host pacing."""
from __future__ import annotations

import json
import random
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from . import __version__

UA = f"onchain-analyst/{__version__} (+https://github.com/lmken/Onchain-Analyst-Bot)"

# Minimum seconds between requests per host (keeps well under public limits).
HOST_MIN_INTERVAL = {
    "api.hyperliquid.xyz": 1.2,          # 1,200 weight/min; most info calls weigh 20 → ≤60/min
    "stats-data.hyperliquid.xyz": 0.2,
    "portal.sqd.dev": 0.6,               # public: 20 req / 10 s
    "gamma-api.polymarket.com": 0.1,
    "clob.polymarket.com": 0.1,
    "data-api.polymarket.com": 0.15,
    "api.llama.fi": 1.0,
    "coins.llama.fi": 1.0,
    "api.coingecko.com": 12.0,
    "api.github.com": 1.0,
}

_last: dict[str, float] = {}
_lock = threading.Lock()


class HTTPError(Exception):
    def __init__(self, status: int, url: str, body: str = ""):
        super().__init__(f"HTTP {status} for {url}: {body[:200]}")
        self.status = status
        self.url = url
        self.body = body


def _pace(host: str) -> None:
    gap = HOST_MIN_INTERVAL.get(host, 0.2)
    with _lock:
        now = time.monotonic()
        wait = _last.get(host, 0) + gap - now
        if wait > 0:
            time.sleep(wait)
        _last[host] = time.monotonic()


def request(method: str, url: str, *, params: dict | None = None, body=None,
            headers: dict | None = None, timeout: float = 60, retries: int = 5,
            retry_statuses=(429, 500, 502, 503, 504, 529)) -> bytes:
    if params:
        q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)
        url = f"{url}{'&' if '?' in url else '?'}{q}"
    data = None
    hdrs = {"User-Agent": UA, "Accept": "*/*"}
    if body is not None:
        data = json.dumps(body).encode() if not isinstance(body, (bytes, str)) else (
            body.encode() if isinstance(body, str) else body)
        hdrs["Content-Type"] = "application/json"
    hdrs.update(headers or {})
    host = urllib.parse.urlparse(url).netloc
    delay = 1.0
    for attempt in range(retries + 1):
        _pace(host)
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                payload = r.read()
            # SQD signals overload inside a 200 body as a JSON error line.
            if payload[:40].lstrip().startswith(b'{"error"') and b"overloaded" in payload[:200]:
                raise HTTPError(503, url, payload[:200].decode(errors="replace"))
            return payload
        except urllib.error.HTTPError as e:
            text = e.read()[:500].decode(errors="replace")
            err = HTTPError(e.code, url, text)
            if e.code not in retry_statuses or attempt == retries:
                raise err from None
            ra = e.headers.get("Retry-After")
            sleep = float(ra) if ra and ra.isdigit() else delay
        except HTTPError as e:
            if attempt == retries:
                raise
            sleep = delay
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == retries:
                raise HTTPError(0, url, str(e)) from None
            sleep = delay
        time.sleep(sleep + random.random() * 0.5)
        delay = min(delay * 2, 30)
    raise HTTPError(0, url, "exhausted retries")


def get_json(url: str, params: dict | None = None, **kw):
    return json.loads(request("GET", url, params=params, **kw))


def post_json(url: str, body, **kw):
    return json.loads(request("POST", url, body=body, **kw))


def get_bytes(url: str, **kw) -> bytes:
    return request("GET", url, **kw)
