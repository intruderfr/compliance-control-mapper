"""Keyword search across all loaded frameworks."""
from __future__ import annotations

from typing import Dict, Iterable, List

from .data import FRAMEWORKS, load_all_frameworks


def _haystack(control: Dict) -> str:
    """Return a lowercased haystack string for matching against a control."""
    parts = [control.get("id", ""), control.get("name", ""), control.get("summary", "")]
    return " ".join(str(p).lower() for p in parts)


def search_controls(
    query: str,
    frameworks: Iterable[str] | None = None,
) -> List[Dict]:
    """Return a list of matching controls across the requested frameworks.

    Each returned dict has the original control keys plus `framework` (canonical
    short key) and `framework_name` (human display name). Matching uses a
    case-insensitive substring match on id, name, and summary.
    """
    query_norm = query.strip().lower()
    if not query_norm:
        return []

    keys = list(frameworks) if frameworks else list(FRAMEWORKS)
    results: List[Dict] = []
    loaded = load_all_frameworks()

    for key in keys:
        if key not in loaded:
            continue
        fw = loaded[key]
        for control in fw["controls"]:
            if query_norm in _haystack(control):
                enriched = dict(control)
                enriched["framework"] = key
                enriched["framework_name"] = fw.get("framework", key)
                results.append(enriched)
    return results
