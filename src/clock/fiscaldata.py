from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"


def fetch_json(endpoint: str, params: dict[str, str], cache: Path | None = None) -> dict:
    """Fetch a FiscalData JSON endpoint, optionally caching the raw response."""
    if cache and cache.exists():
        return json.loads(cache.read_text())
    url = f"{BASE}{endpoint}?{urlencode(params)}"
    with urlopen(url, timeout=60) as r:
        payload = json.loads(r.read().decode("utf-8"))
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(payload, indent=2))
    return payload


def fetch_all(endpoint: str, params: dict[str, str], cache_dir: Path | None = None) -> list[dict]:
    """Paginate a FiscalData endpoint without assuming a fixed row count."""
    page = 1
    rows: list[dict] = []
    while True:
        p = dict(params)
        p["page[number]"] = str(page)
        p.setdefault("page[size]", "10000")
        cache = cache_dir / f"page_{page:04d}.json" if cache_dir else None
        payload = fetch_json(endpoint, p, cache)
        batch = payload.get("data", [])
        rows.extend(batch)
        meta = payload.get("meta", {})
        total_pages = int(meta.get("total-pages", meta.get("total_pages", page)))
        if not batch or page >= total_pages:
            break
        page += 1
    return rows
