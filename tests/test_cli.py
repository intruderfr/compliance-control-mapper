"""Tests for the CLI entry point."""
import json

import pytest

from compliance_mapper.cli import main


def test_cli_list(capsys):
    rc = main(["list", "iso27001"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "ISO/IEC 27001:2022" in out
    assert "A.8.13" in out


def test_cli_show_auto_infers_framework(capsys):
    rc = main(["show", "A.8.13"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "A.8.13" in out
    assert "backup" in out.lower()


def test_cli_search(capsys):
    rc = main(["search", "malware"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "malware" in out.lower()


def test_cli_map_json(capsys):
    rc = main(["map", "A.8.13", "--json"])
    out = capsys.readouterr().out
    assert rc == 0
    payload = json.loads(out)
    assert payload["source"]["control"]["id"] == "A.8.13"
    assert payload["topics"]


def test_cli_topic(capsys):
    rc = main(["topic", "access_control"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "access_control" in out.lower() or "access control" in out.lower()


def test_cli_topics_list(capsys):
    rc = main(["topics"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "backup_recovery" in out


def test_cli_stats(capsys):
    rc = main(["stats"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Coverage" in out


def test_cli_export_markdown(capsys):
    rc = main(["export", "markdown"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "# Security Control Crosswalk" in out


def test_cli_unknown_control_exits_nonzero(capsys):
    rc = main(["show", "A.99.99"])
    err = capsys.readouterr().err
    assert rc == 2
    assert "not found" in err.lower()
