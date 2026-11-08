from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def _load(name: str):
    path = HOME / name
    spec = importlib.util.spec_from_file_location(f"_test_2e02_{name.replace('.', '_')}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_matched_inputs_and_setting_outputs_are_distinct():
    family = _load("family.py")
    canonical = family.generate(17, {"rule_mode": "all_local_pairs"}, 2, 4)
    relay = family.generate(17, {"rule_mode": "relay_hit_color"}, 2, 4)
    assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
        p["input"] for p in relay["train"] + relay["test"]
    ]
    assert all(
        left["output"] != right["output"]
        for left, right in zip(
            canonical["train"] + canonical["test"],
            relay["train"] + relay["test"],
        )
    )


def test_two_demo_curriculum_hits_both_candidate_roles_and_refutes_rivals():
    family = _load("family.py")
    episode = family.generate(0, {"rule_mode": "relay_hit_color"}, 2, 4)
    roles = [family.observe(pair["input"])["relay_role"] for pair in episode["train"]]
    assert roles == [0, 1]
    audit = family.teaching_audit(episode)
    assert audit["query_disagreeing_survivors"] == []
    assert audit["survivors"] == ["relay_hit_color"]


def test_supported_count_boundaries_and_substantive_30x30_query():
    family = _load("family.py")
    for demos in (2, 6):
        episode = family.generate(29, {"rule_mode": "all_local_pairs"}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        all_inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({repr(grid) for grid in all_inputs}) == len(all_inputs)
    large = episode["test"][-1]["input"]
    assert (len(large), len(large[0])) == (30, 30)
    state = family.observe(large)
    assert len(state["target_frames"]) == 3
    assert sum(cell != 0 for row in large for cell in row) >= 150


def test_invalid_contract_values_are_rejected():
    family = _load("family.py")
    with pytest.raises(ValueError):
        family.generate(True, {"rule_mode": "all_local_pairs"}, 2, 4)
    with pytest.raises(ValueError):
        family.generate(0, {"rule_mode": "unknown"}, 2, 4)
    with pytest.raises(ValueError):
        family.generate(0, {"rule_mode": "all_local_pairs"}, 1, 4)
    with pytest.raises(ValueError):
        family.generate(0, {"rule_mode": "all_local_pairs"}, 2, 5)
