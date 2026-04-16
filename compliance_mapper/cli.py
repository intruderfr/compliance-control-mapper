"""Command-line interface for compliance-control-mapper."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from . import __version__
from .data import FRAMEWORKS, canonical_framework, find_control, load_framework
from .mapper import coverage_stats, map_control, map_topic
from .report import (
    export_csv,
    export_json,
    export_markdown,
    format_control,
    format_list,
    format_mapping,
    format_search,
    format_stats,
    format_topic,
)
from .search import search_controls


def _framework_choices() -> List[str]:
    return sorted(FRAMEWORKS)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="compliance-mapper",
        description=(
            "Crosswalk tool mapping controls across ISO 27001:2022, NIST CSF 2.0, "
            "CIS Controls v8, and SOC 2 TSC."
        ),
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")

    # list
    p_list = sub.add_parser("list", help="List all controls in a framework")
    p_list.add_argument("framework", choices=_framework_choices(),
                        help="Framework short name")

    # show
    p_show = sub.add_parser("show", help="Show the full detail of a single control")
    p_show.add_argument("control_id",
                        help="Control ID (e.g. A.8.13, PR.DS, CIS-11, CC6.1)")
    p_show.add_argument("-f", "--framework", choices=_framework_choices(),
                        help="Disambiguate if the ID exists in multiple frameworks")

    # search
    p_search = sub.add_parser("search", help="Search controls by keyword")
    p_search.add_argument("query", help="Case-insensitive substring to match")
    p_search.add_argument("-f", "--framework", choices=_framework_choices(),
                          action="append",
                          help="Limit search to these frameworks (repeatable)")
    p_search.add_argument("--json", action="store_true", help="Emit JSON output")

    # map
    p_map = sub.add_parser("map",
                           help="Show cross-framework equivalents for a control")
    p_map.add_argument("control_id",
                       help="Control ID to map (e.g. A.8.13, CIS-11)")
    p_map.add_argument("-f", "--framework", choices=_framework_choices(),
                       help="Disambiguate if the ID exists in multiple frameworks")
    p_map.add_argument("--json", action="store_true", help="Emit JSON output")

    # topic
    p_topic = sub.add_parser("topic",
                             help="Show every control mapped to a crosswalk topic")
    p_topic.add_argument("topic_id",
                         help="Topic key from the crosswalk (e.g. backup_recovery)")
    p_topic.add_argument("--json", action="store_true", help="Emit JSON output")

    # topics (list all topics)
    sub.add_parser("topics", help="List every crosswalk topic key")

    # stats
    sub.add_parser("stats", help="Show crosswalk coverage per framework")

    # export
    p_export = sub.add_parser("export",
                              help="Export the full dataset (json|csv|markdown)")
    p_export.add_argument("format", choices=["json", "csv", "markdown"])

    return parser


def _infer_framework(control_id: str,
                     explicit: Optional[str]) -> str:
    """If the user didn't pass -f, figure out which framework the ID belongs to."""
    if explicit:
        return canonical_framework(explicit)
    hits = []
    for fw_key in FRAMEWORKS:
        if find_control(fw_key, control_id) is not None:
            hits.append(fw_key)
    if not hits:
        raise LookupError(
            f"Control '{control_id}' not found in any bundled framework."
        )
    if len(hits) > 1:
        raise LookupError(
            f"Control '{control_id}' exists in multiple frameworks "
            f"({', '.join(hits)}). Pass -f to disambiguate."
        )
    return hits[0]


def cmd_list(args: argparse.Namespace) -> int:
    fw = load_framework(args.framework)
    print(f"{fw['framework']} - {len(fw['controls'])} controls\n")
    print(format_list(args.framework, fw["controls"]))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    try:
        fw_key = _infer_framework(args.control_id, args.framework)
    except LookupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    fw = load_framework(fw_key)
    ctrl = find_control(fw_key, args.control_id)
    if ctrl is None:
        print(f"Error: control '{args.control_id}' not found.", file=sys.stderr)
        return 2
    print(format_control(ctrl, fw["framework"]))
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    results = search_controls(args.query, frameworks=args.framework)
    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(format_search(results, args.query))
    return 0 if results else 1


def cmd_map(args: argparse.Namespace) -> int:
    try:
        fw_key = _infer_framework(args.control_id, args.framework)
        mapping = map_control(fw_key, args.control_id)
    except LookupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(mapping, indent=2, ensure_ascii=False))
    else:
        print(format_mapping(mapping))
    return 0


def cmd_topic(args: argparse.Namespace) -> int:
    try:
        resolved = map_topic(args.topic_id)
    except LookupError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(resolved, indent=2, ensure_ascii=False))
    else:
        print(format_topic(resolved))
    return 0


def cmd_topics(_args: argparse.Namespace) -> int:
    from .data import load_mappings
    topics = load_mappings()["topics"]
    print(f"{len(topics)} crosswalk topics:\n")
    for tid, topic in topics.items():
        print(f"  {tid:<24}  {topic['name']}")
    return 0


def cmd_stats(_args: argparse.Namespace) -> int:
    print(format_stats(coverage_stats()))
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    dispatch = {"json": export_json, "csv": export_csv, "markdown": export_markdown}
    print(dispatch[args.format]())
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "list": cmd_list,
        "show": cmd_show,
        "search": cmd_search,
        "map": cmd_map,
        "topic": cmd_topic,
        "topics": cmd_topics,
        "stats": cmd_stats,
        "export": cmd_export,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
