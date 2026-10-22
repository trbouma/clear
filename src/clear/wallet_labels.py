"""Optional public labels for local treasury balances; never alter wallet proofs."""
import json
import urllib.request
from urllib.parse import urlsplit


def fetch_keysets(mint):
    parsed = urlsplit(mint)
    if (parsed.scheme not in {"http", "https"} or not parsed.hostname
            or parsed.username is not None or parsed.password is not None
            or parsed.query or parsed.fragment):
        raise ValueError("Invalid mint URL")
    request = urllib.request.Request(mint.rstrip("/") + "/v1/keysets",
                                     headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=3) as response:
        body = response.read(262145)
    if len(body) > 262144:
        raise ValueError("Mint labels too large")
    payload = json.loads(body)
    rows = payload.get("keysets") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("Invalid mint keysets")
    return [row for row in rows if isinstance(row, dict)]


def with_friendly_labels(summary):
    cache = {}
    for balance in summary["balances"]:
        mint, unit = balance["mint"], balance["unit"]
        if mint not in cache:
            try:
                cache[mint] = fetch_keysets(mint)
            except (ValueError, OSError):
                cache[mint] = []
        candidates = [row for row in cache[mint] if row.get("unit") == unit]
        selected = next((row for row in candidates if row.get("active") is True),
                        candidates[0] if candidates else {})
        for field, value, limit in (
            ("friendly_alias", selected.get("friendly_alias") or selected.get("friendly_name"), 120),
            ("friendly_unit_alias", selected.get("friendly_unit_alias"), 40),
        ):
            balance[field] = value.strip() if isinstance(value, str) and 0 < len(value.strip()) <= limit else unit
    return summary
