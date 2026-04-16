"""Tests for keyword search."""
from compliance_mapper.search import search_controls


def test_search_finds_recovery_across_frameworks():
    results = search_controls("recovery")
    frameworks = {r["framework"] for r in results}
    # "Recovery" language appears in ISO, NIST CSF, CIS, and SOC 2 controls
    assert "iso27001" in frameworks or "cis" in frameworks
    assert "nist_csf" in frameworks
    assert len(results) >= 2


def test_search_finds_backup_in_iso():
    results = search_controls("backup")
    frameworks = {r["framework"] for r in results}
    assert "iso27001" in frameworks


def test_search_is_case_insensitive():
    assert search_controls("MALWARE")
    assert search_controls("malware")


def test_search_scoped_to_framework():
    results = search_controls("access", frameworks=["soc2"])
    assert results
    assert all(r["framework"] == "soc2" for r in results)


def test_search_empty_query_returns_empty():
    assert search_controls("   ") == []
    assert search_controls("") == []


def test_search_no_match():
    assert search_controls("zzz-no-such-concept") == []
