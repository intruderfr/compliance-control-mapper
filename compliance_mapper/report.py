"""Output formatters: plain text (table), JSON, CSV, Markdown."""
from __future__ import annotations

import csv
import io
import json
from typing import Dict, List

from .data import FRAMEWORKS, load_all_frameworks


# ---------- helpers ----------------------------------------------------------

def _wrap(text: str, width: int = 60) -> List[str]:
    """Very small hand-rolled word wrapper (no textwrap dependency needed)."""
    if not text:
        return [""]
    words = str(text).split()
    lines: List[str] = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 <= width:
            current = f"{current} {word}".strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _table(rows: List[List[str]], headers: List[str], wrap_col: int | None = None) -> str:
    """Render a basic text table. rows/headers are lists of strings."""
    if wrap_col is not None:
        expanded: List[List[str]] = []
        for row in rows:
            wrapped_cells = [
                _wrap(cell, width=60) if i == wrap_col else [str(cell)]
                for i, cell in enumerate(row)
            ]
            height = max(len(cell) for cell in wrapped_cells)
            for i in range(height):
                expanded.append([
                    cell[i] if i < len(cell) else "" for cell in wrapped_cells
                ])
            expanded.append([""] * len(headers))  # blank separator between rows
        rows = expanded[:-1] if expanded else expanded

    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"

    def fmt(row: List[str]) -> str:
        return "| " + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row)) + " |"

    lines = [sep, fmt(headers), sep]
    for row in rows:
        lines.append(fmt(row))
    lines.append(sep)
    return "\n".join(lines)


# ---------- formatters -------------------------------------------------------

def format_list(framework: str, controls: List[Dict]) -> str:
    """Table of controls for a single framework."""
    rows = [[c["id"], c["name"]] for c in controls]
    return _table(rows, headers=["ID", "Name"])


def format_control(control: Dict, framework_name: str) -> str:
    """Detailed view of a single control."""
    out = [
        f"Framework : {framework_name}",
        f"ID        : {control['id']}",
        f"Name      : {control['name']}",
    ]
    for extra_key in ("theme", "function", "category"):
        if extra_key in control:
            out.append(f"{extra_key.capitalize():<10}: {control[extra_key]}")
    out.append("")
    out.append("Summary:")
    out.extend(f"  {line}" for line in _wrap(control.get("summary", ""), width=72))
    return "\n".join(out)


def format_search(results: List[Dict], query: str) -> str:
    """Search results as a table."""
    if not results:
        return f"No matches for '{query}'."
    rows = [
        [r["framework"], r["id"], r["name"][:80]]
        for r in results
    ]
    return (
        f"Search results for '{query}' ({len(results)} match"
        f"{'es' if len(results) != 1 else ''}):\n\n"
        + _table(rows, headers=["Framework", "ID", "Name"])
    )


def format_mapping(mapping: Dict) -> str:
    """Human-friendly mapping view for a single source control."""
    source = mapping["source"]
    fw_display = FRAMEWORKS[source["framework"]][1]
    ctrl = source["control"]
    out = [
        "=" * 70,
        f"{fw_display}  {ctrl['id']} - {ctrl['name']}",
        "=" * 70,
        "",
        f"Summary: {ctrl.get('summary', '')}",
        "",
    ]
    if not mapping["topics"]:
        out.append("  (No crosswalk topic covers this control yet.)")
        return "\n".join(out)

    for topic in mapping["topics"]:
        out.append(f"Crosswalk topic: {topic['name']} ({topic['topic_id']})")
        out.append("-" * 70)
        for fw_key, (_, display) in FRAMEWORKS.items():
            matches = topic["resolved"].get(fw_key, [])
            if not matches:
                continue
            out.append(f"  {display}:")
            for m in matches:
                out.append(f"    - {m['id']}: {m['name']}")
        out.append("")
    return "\n".join(out)


def format_topic(topic: Dict) -> str:
    """Render a crosswalk topic across all frameworks."""
    out = [
        "=" * 70,
        f"Topic: {topic['name']} ({topic['topic_id']})",
        "=" * 70,
        "",
    ]
    for fw_key, (_, display) in FRAMEWORKS.items():
        matches = topic["resolved"].get(fw_key, [])
        out.append(f"{display} ({len(matches)}):")
        if matches:
            for m in matches:
                out.append(f"  - {m['id']}: {m['name']}")
        else:
            out.append("  (none mapped)")
        out.append("")
    return "\n".join(out)


def format_stats(stats: Dict) -> str:
    """Render coverage statistics."""
    rows = []
    for key in FRAMEWORKS:
        s = stats[key]
        rows.append([
            s["framework"],
            str(s["total_controls"]),
            str(s["controls_in_crosswalk"]),
            f"{s['coverage_percent']}%",
        ])
    out = [
        f"Crosswalk topics defined: {stats['_topics']['count']}",
        "",
        _table(
            rows,
            headers=["Framework", "Total", "In crosswalk", "Coverage"],
        ),
    ]
    return "\n".join(out)


# ---------- exports ----------------------------------------------------------

def export_json() -> str:
    """Dump every framework and the crosswalk as pretty-printed JSON."""
    from .data import load_mappings  # local import to avoid cycle at load time
    payload = {
        "frameworks": load_all_frameworks(),
        "mappings": load_mappings(),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def export_csv() -> str:
    """CSV of all crosswalk topics, one row per topic."""
    from .data import load_mappings
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["topic_id", "topic_name"] + list(FRAMEWORKS))
    for tid, topic in load_mappings()["topics"].items():
        row = [tid, topic["name"]]
        for fw_key in FRAMEWORKS:
            row.append(", ".join(topic.get(fw_key, [])))
        writer.writerow(row)
    return buf.getvalue()


def export_markdown() -> str:
    """Full crosswalk as a Markdown document suitable for GitHub/Confluence."""
    from .data import load_mappings
    mappings = load_mappings()
    out: List[str] = [
        "# Security Control Crosswalk",
        "",
        mappings["description"],
        "",
        f"_Version {mappings['version']} - last updated {mappings['last_updated']}_",
        "",
        "## Frameworks covered",
        "",
    ]
    for fw_key, (_, display) in FRAMEWORKS.items():
        out.append(f"- **{display}** (`{fw_key}`)")
    out.append("")
    out.append("## Crosswalk topics")
    out.append("")
    header = "| Topic | " + " | ".join(d for _, d in FRAMEWORKS.values()) + " |"
    divider = "|---|" + "|".join(["---"] * len(FRAMEWORKS)) + "|"
    out.extend([header, divider])
    for tid, topic in mappings["topics"].items():
        cells = [f"**{topic['name']}** (`{tid}`)"]
        for fw_key in FRAMEWORKS:
            ids = topic.get(fw_key, [])
            cells.append(", ".join(ids) if ids else "_(none)_")
        out.append("| " + " | ".join(cells) + " |")
    out.append("")
    return "\n".join(out)
