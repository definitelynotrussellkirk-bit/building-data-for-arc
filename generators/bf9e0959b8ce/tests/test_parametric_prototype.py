from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root

TASK_ID = "bf9e0959b8ce"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
CANONICAL_PATH = PARAMETRIC / "canonical.rkt"


def _load_prototype():
    assert PROTOTYPE_PATH.exists(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "bf9e0959b8ce_count_relay_prototype", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_has_exact_canonical_default_and_strict_settings():
    proto = _load_prototype()
    assert proto.PARAMETER_NAME == "rule_mode"
    assert proto.ALLOWED_MODES == ("canonical", "near_count_relay")
    assert proto.DEFAULT_MODE == "canonical"
    assert proto.program({"rule_mode": "canonical"}) == CANONICAL_PATH.read_text(
        encoding="utf-8"
    )
    assert proto.program({"rule_mode": "near_count_relay"}).startswith("(rule!")
    assert proto.program({"rule_mode": "near_count_relay"}) != proto.program(
        {"rule_mode": "canonical"}
    )

    for bad in (None, True, 1, "canonical", {}, {"rule_mode": "unknown"}, {"rule_mode": "canonical", "x": 1}):
        with pytest.raises((TypeError, ValueError)):
            proto.program(bad)


def test_generate_supports_independent_counts_and_prefix_stability():
    proto = _load_prototype()
    settings = {"rule_mode": "near_count_relay"}

    one = proto.generate(17, settings, demos=2, queries=1)
    four = proto.generate(17, settings, demos=2, queries=4)
    six = proto.generate(17, settings, demos=6, queries=4)

    assert len(one["train"]) == 2
    assert len(one["test"]) == 1
    assert len(four["train"]) == 2
    assert len(four["test"]) == 4
    assert len(six["train"]) == 6
    assert len(six["test"]) == 4
    assert one["train"] == four["train"] == six["train"][:2]
    assert one["test"] == four["test"][:1] == six["test"][:1]
    assert four["test"] == six["test"]

    inputs = [pair["input"] for pair in six["train"] + six["test"]]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == 10

    for demos in range(2, 7):
        result = proto.generate(123, settings, demos=demos, queries=4)
        assert len(result["train"]) == demos
    for queries in range(1, 5):
        result = proto.generate(123, settings, demos=3, queries=queries)
        assert len(result["test"]) == queries

    for bad in (True, 1.5, "3", None, 1, 7):
        with pytest.raises((TypeError, ValueError)):
            proto.generate(0, settings, demos=bad, queries=4)
    for bad in (True, 1.5, "4", None, 0, 5):
        with pytest.raises((TypeError, ValueError)):
            proto.generate(0, settings, demos=3, queries=bad)


def test_settings_share_inputs_and_each_visible_demo_distinguishes_them():
    proto = _load_prototype()
    canonical = proto.generate(20261024, {"rule_mode": "canonical"}, 6, 4)
    relay = proto.generate(20261024, {"rule_mode": "near_count_relay"}, 6, 4)

    assert [pair["input"] for pair in canonical["train"]] == [
        pair["input"] for pair in relay["train"]
    ]
    assert [pair["input"] for pair in canonical["test"]] == [
        pair["input"] for pair in relay["test"]
    ]
    assert all(
        left["output"] != right["output"]
        for left, right in zip(canonical["train"], relay["train"], strict=True)
    )
    assert all(
        left["output"] != right["output"]
        for left, right in zip(canonical["test"], relay["test"], strict=True)
    )


def test_relay_explanation_names_real_intermediate_and_wrong_count_changes_output():
    proto = _load_prototype()
    episode = proto.generate(0, {"rule_mode": "near_count_relay"}, 6, 4)

    observed_counts = set()
    for pair in episode["train"] + episode["test"]:
        explanation = proto.explain_relay(pair["input"])
        count = explanation["near_count"]
        observed_counts.add(count)
        assert count in (1, 2, 3)
        assert len(explanation["far_candidates"]) >= 3
        assert explanation["selected_far_candidate"] == explanation["far_candidates"][count - 1]
        assert explanation["final"] == pair["output"]
        wrong = 1 if count != 1 else 2
        assert proto.relay_with_forced_count(pair["input"], wrong) != pair["output"]
    assert observed_counts == {1, 2, 3}


def test_profiles_cover_orientations_boundaries_and_substantive_30x30_query():
    proto = _load_prototype()
    episode = proto.generate(999, {"rule_mode": "near_count_relay"}, 6, 4)
    infos = [proto.analyze(pair["input"]) for pair in episode["train"] + episode["test"]]

    assert {info["orientation"] for info in infos[:2]} == {"row", "col"}
    assert {info["orientation"] for info in infos} == {"row", "col"}
    assert all(info["match_count"] in (1, 2, 3) for info in infos)
    assert all(info["nonmatch_count"] >= 3 for info in infos)
    assert all(info["source_line_count"] >= 2 for info in infos)

    large = episode["test"][3]["input"]
    assert len(large) == 30 and len(large[0]) == 30
    large_info = proto.analyze(large)
    assert large_info["n_dots"] >= 6
    assert {coord for coord, _ in large_info["far_candidates"]} & {0, 29}


def test_public_projection_reveals_one_query_without_private_fields_or_count_hint():
    proto = _load_prototype()
    episode = proto.generate(42, {"rule_mode": "near_count_relay"}, 3, 4)
    first = proto.public_challenge(episode, query_index=0)
    second = proto.public_challenge(episode, query_index=1)
    batch = proto.public_batch(episode)

    assert set(first) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    assert len(first["test"]) == len(second["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    assert first["test"][0]["input"] == episode["test"][0]["input"]
    assert second["test"][0]["input"] == episode["test"][1]["input"]
    assert len(batch["test"]) == 4
    assert batch["test"][0] == first["test"][0]
    serialized = json.dumps(first, sort_keys=True)
    assert "rule_mode" not in serialized
    assert "near_count_relay" not in serialized
    assert "program_solution" not in serialized
    assert "near_count" not in serialized
    assert "query_count" not in serialized

    for bad in (True, -1, 4, 1.5, "0"):
        with pytest.raises((TypeError, ValueError, IndexError)):
            proto.public_challenge(episode, query_index=bad)
