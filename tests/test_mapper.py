"""Tests for cross-framework mapping."""
import pytest

from compliance_mapper.mapper import (
    coverage_stats,
    map_control,
    map_topic,
    topics_for_control,
)


def test_topics_for_control_backup():
    topics = topics_for_control("iso27001", "A.8.13")
    assert any(t["topic_id"] == "backup_recovery" for t in topics)


def test_map_control_resolves_equivalents():
    mapping = map_control("iso27001", "A.8.13")
    assert mapping["source"]["control"]["id"] == "A.8.13"
    assert mapping["topics"], "A.8.13 should appear in at least one topic"

    topic = next(t for t in mapping["topics"] if t["topic_id"] == "backup_recovery")
    cis_ids = [c["id"] for c in topic["resolved"]["cis"]]
    assert "CIS-11" in cis_ids

    # The source itself must not appear in its own resolved list
    iso_ids = [c["id"] for c in topic["resolved"]["iso27001"]]
    assert "A.8.13" not in iso_ids


def test_map_control_unknown_raises():
    with pytest.raises(LookupError):
        map_control("iso27001", "A.99.99")


def test_map_topic_returns_all_frameworks():
    topic = map_topic("access_control")
    assert set(topic["resolved"]) == {"iso27001", "nist_csf", "cis", "soc2"}
    assert topic["resolved"]["soc2"]


def test_map_topic_unknown_raises():
    with pytest.raises(LookupError):
        map_topic("no_such_topic")


def test_coverage_stats_shape():
    stats = coverage_stats()
    for key in ("iso27001", "nist_csf", "cis", "soc2"):
        s = stats[key]
        assert s["total_controls"] > 0
        assert 0 <= s["coverage_percent"] <= 100
    assert stats["_topics"]["count"] > 0
