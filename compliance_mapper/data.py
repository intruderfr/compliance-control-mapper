"""Loaders for the bundled compliance framework JSON files."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

# Short framework keys used throughout the CLI. The value is (filename, display name).
FRAMEWORKS: Dict[str, tuple] = {
    "iso27001": ("iso27001_2022.json", "ISO/IEC 27001:2022"),
    "nist_csf": ("nist_csf_2.json", "NIST CSF 2.0"),
    "cis": ("cis_v8.json", "CIS Controls v8"),
    "soc2": ("soc2_tsc.json", "SOC 2 TSC"),
}

# Internal alias -> canonical key so `iso`, `nist`, `cis_v8`, `soc` all work.
_ALIASES = {
    "iso": "iso27001",
    "iso27001_2022": "iso27001",
    "nist": "nist_csf",
    "nist_csf_2": "nist_csf",
    "csf": "nist_csf",
    "cis_v8": "cis",
    "soc": "soc2",
    "soc2_tsc": "soc2",
}


def _data_dir() -> Path:
    """Return the absolute path to the packaged data directory."""
    return Path(__file__).resolve().parent.parent / "data"


def canonical_framework(name: str) -> str:
    """Normalize a user-supplied framework alias to its canonical key.

    Raises KeyError if the name is not recognized.
    """
    key = name.strip().lower().replace("-", "_")
    if key in FRAMEWORKS:
        return key
    if key in _ALIASES:
        return _ALIASES[key]
    raise KeyError(
        f"Unknown framework '{name}'. Valid: {', '.join(sorted(FRAMEWORKS))}."
    )


@lru_cache(maxsize=None)
def load_framework(name: str) -> Dict[str, Any]:
    """Load a single framework JSON file by name (or alias)."""
    key = canonical_framework(name)
    filename, _display = FRAMEWORKS[key]
    path = _data_dir() / filename
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    # Attach the canonical short key so downstream code doesn't have to guess.
    data["_key"] = key
    return data


@lru_cache(maxsize=1)
def load_mappings() -> Dict[str, Any]:
    """Load the cross-framework crosswalk topics file."""
    path = _data_dir() / "mappings.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_all_frameworks() -> Dict[str, Dict[str, Any]]:
    """Load every framework into a dict keyed by canonical name."""
    return {key: load_framework(key) for key in FRAMEWORKS}


def find_control(framework: str, control_id: str) -> Dict[str, Any] | None:
    """Return the control dict matching control_id within a framework, or None.

    Matching is case-insensitive and tolerates an optional leading 'A.' on ISO.
    """
    fw = load_framework(framework)
    target = control_id.strip().upper()
    for control in fw["controls"]:
        if control["id"].upper() == target:
            return control
    return None
