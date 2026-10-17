"""Render rows as a text table, JSON, CSV or Markdown, plus the sources/coverage footer."""
from __future__ import annotations

import csv
import io
import json
import sys


def _fmt(v):
    if isinstance(v, float):
        if abs(v) >= 1000:
            return f"{v:,.0f}"
        if abs(v) >= 1:
            return f"{v:,.2f}"
        return f"{v:.4g}"
    if isinstance(v, (list, dict)):
        return json.dumps(v)[:60]
    return "" if v is None else str(v)


def render(rows: list[dict], fmt: str = "table", footer: dict | None = None, out=None) -> str:
    out = out or sys.stdout
    if fmt == "json":
        s = json.dumps({"rows": rows, "meta": footer or {}}, indent=2, default=str)
    elif fmt == "csv":
        buf = io.StringIO()
        cols = list(dict.fromkeys(k for r in rows for k in r))
        w = csv.DictWriter(buf, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in cols})
        s = buf.getvalue()
    else:
        cols = list(dict.fromkeys(k for r in rows for k in r))
        cells = [[_fmt(r.get(c)) for c in cols] for r in rows]
        if fmt == "md":
            lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
            lines += ["| " + " | ".join(c) + " |" for c in cells]
        else:
            wid = [max(len(c), *(len(x[i]) for x in cells)) if cells else len(c) for i, c in enumerate(cols)]
            lines = ["  ".join(c.ljust(wid[i]) for i, c in enumerate(cols)),
                     "  ".join("-" * w for w in wid)]
            lines += ["  ".join(x[i].rjust(wid[i]) if _num(x[i]) else x[i].ljust(wid[i])
                                for i in range(len(cols))) for x in cells]
        if footer:
            lines.append("")
            lines += [f"{k}: {v}" for k, v in footer.items()]
        s = "\n".join(lines) + "\n"
    out.write(s)
    return s


def _num(s: str) -> bool:
    return bool(s) and s.replace(",", "").replace(".", "").replace("-", "").replace("%", "").isdigit()
