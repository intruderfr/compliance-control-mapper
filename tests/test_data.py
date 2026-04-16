"""Tests for the data loader module."""
import pytest

from compliance_mapper.data import (
    FRAMEWORKS,
    canonical_framework,
    find_control,
    load_all_frameworks,
    load_framework,
    load_mappings,
)


def test_all_frameworks_load():
    """Every framework declared in FRAMEWORKS has a loadable JSON file."""
    loaded = load_all_frameworks()
    assert set(loaded) == set(FRAMEWORKS)
    for key, fw in loaded.items():
        assert "controls" in fw, f"{key} missing 'controls'"
        assert fw["controls"], f"{key} has no controls"
        for ctrl in fw["controls"]:
            assert "id" in ctrl and ctrl["id"]
            assert "name" in ctrl and ctrl["name"]


def test_canonical_framework_aliases():
    assert canonical_framework("iso") == "iso27001"
    assert canonical_framework("ISO27001") == "iso27001"
    assert canonical_framework("nist") == "nist_csf"
    assert canonical_framework("cis_v8") == "cis"
    assert canonical_framework("soc") == "soc2"


def test_canonical_framework_unknown():
    with pytest.raises(KeyError):
        canonical_framework("bogus-framework")


def test_find_control_hits_and_misses():
    ctrl = find_control("iso27001", "A.8.13")
    assert ctrl is not None
    assert "backup" in ctrl["name"].lower() or "backup" in ctrl["summary"].lower()
    assert find_control("iso27001", "A.99.99") is None


def test_mappings_file_integrity():
    """Every ID referenced in mappings.json must resolve to a real control."""
    mappings = load_mappings()
    for topic_id, topic in mappings["topics"].items():
        for fw_key in FRAMEWORKS:
            for cid in topic.get(fw_key, []):
                ctrl = find_control(fw_key, cid)
                assert ctrl is not None, (
                    f"Topic '{topic_id}' references unknown {fw_key} control '{cid}'"
                )
