"""Cross-framework mapping logic built on top of the curated crosswalk topics."""
from __future__ import annotations

from typing import Dict, List

from .data import (
    FRAMEWORKS,
    canonical_framework,
    find_control,
    load_framework,
    load_mappings,
)


def topics_for_control(framework: str, control_id: str) -> List[Dict]:
    """Return every crosswalk topic that references (framework, control_id)."""
    key = canonical_framework(framework)
    target = control_id.strip().upper()
    hits: List[Dict] = []
    for topic_id, topic in load_mappings()["topics"].items():
        ids = [c.upper() for c in topic.get(key, [])]
        if target in ids:
            hits.append({"topic_id": topic_id, **topic})
    return hits


def map_control(framework: str, control_id: str) -> Dict:
    """Given a control, return the full mapping across all frameworks.

    Output structure:
        {
          "source": {"framework": "iso27001", "control": {...full control dict...}},
          "topics": [
            {
              "topic_id": "backup_recovery",
              "name": "Backup & Recovery",
              "iso27001": ["A.8.13", ...],
              "nist_csf": [...],
              "cis": [...],
              "soc2": [...],
              "resolved": {  # id -> control dict (excludes the source control)
                "iso27001": [{...}, ...],
                ...
              }
            },
            ...
          ]
        }
    """
    key = canonical_framework(framework)
    source_ctrl = find_control(key, control_id)
    if source_ctrl is None:
        raise LookupError(
            f"Control '{control_id}' not found in framework '{FRAMEWORKS[key][1]}'."
        )

    topics = topics_for_control(key, control_id)
    enriched_topics: List[Dict] = []
    for topic in topics:
        resolved: Dict[str, List[Dict]] = {}
        for fw_key in FRAMEWORKS:
            ctrls = []
            for cid in topic.get(fw_key, []):
                if fw_key == key and cid.upper() == control_id.strip().upper():
                    continue  # skip the source itself
                c = find_control(fw_key, cid)
                if c is not None:
                    ctrls.append(c)
            resolved[fw_key] = ctrls
        enriched = {**topic, "resolved": resolved}
        enriched_topics.append(enriched)

    return {
        "source": {"framework": key, "control": source_ctrl},
        "topics": enriched_topics,
    }


def map_topic(topic_id: str) -> Dict:
    """Return a full resolved view of a single crosswalk topic."""
    topics = load_mappings()["topics"]
    if topic_id not in topics:
        raise LookupError(
            f"Unknown topic '{topic_id}'. Valid: {', '.join(sorted(topics))}."
        )
    topic = topics[topic_id]
    resolved: Dict[str, List[Dict]] = {}
    for fw_key in FRAMEWORKS:
        ctrls = []
        for cid in topic.get(fw_key, []):
            c = find_control(fw_key, cid)
            if c is not None:
                ctrls.append(c)
        resolved[fw_key] = ctrls
    return {"topic_id": topic_id, **topic, "resolved": resolved}


def coverage_stats() -> Dict:
    """Report how many controls from each framework appear in the crosswalk."""
    topics = load_mappings()["topics"]
    stats: Dict[str, Dict] = {}
    for fw_key in FRAMEWORKS:
        fw = load_framework(fw_key)
        total = len(fw["controls"])
        mapped_ids = set()
        for topic in topics.values():
            for cid in topic.get(fw_key, []):
                mapped_ids.add(cid.upper())
        stats[fw_key] = {
            "framework": fw.get("framework", fw_key),
            "total_controls": total,
            "controls_in_crosswalk": len(mapped_ids),
            "coverage_percent": round(100 * len(mapped_ids) / total, 1) if total else 0.0,
        }
    stats["_topics"] = {"count": len(topics)}
    return stats
