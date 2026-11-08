"""Prototype-only checks; these do not approve or alter canonical generation."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
SOURCE = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"


def _prototype():
    assert SOURCE.is_file(), "the requested endpoint-threshold prototype is missing"
    spec = importlib.util.spec_from_file_location("endpoint_threshold_prototype", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=15) as live:
        yield live


def test_default_program_reproduces_every_canonical_label(bridge):
    prototype = _prototype()
    pairs = canonical_pairs("832404dc8a5c", root=ROOT)
    assert len(pairs) == 4
    program = prototype.render_program()
    assert program == prototype.canonical_rule(ROOT)
    for pair in pairs:
        assert prototype.execute_program(bridge, program, pair["input"]) == pair["output"]


def test_single_endpoints_change_both_orientations_and_preserve_union(bridge):
    prototype = _prototype()
    grid = [[0 for _ in range(8)] for _ in range(6)]
    grid[1][0] = grid[1][7] = 4
    grid[0][2] = grid[5][2] = 4
    grid[3][0] = grid[0][5] = 4
    grid[1][2] = 7
    grid[3][3] = grid[4][5] = 6
    outputs = {
        threshold: prototype.execute_program(bridge, prototype.render_program(threshold), grid)
        for threshold in (1, 2)
    }
    assert outputs[1][3][3] == outputs[1][4][5] == 7
    assert outputs[2][3][3] == outputs[2][4][5] == 6
    for result in outputs.values():
        assert result[1][2] == 6, "a crossing swaps once, not once per lane"
        assert result[4][4] == 0, "a nonlane cell is unchanged"
        assert result[3][0] == result[0][5] == 4, "single markers are preserved"
        assert result[1][7] == result[5][2] == 4, "paired markers are preserved"


@pytest.mark.parametrize("threshold", [1, 2])
def test_complete_episode_is_deterministic_and_demonstrates_both_roles(bridge, threshold):
    prototype = _prototype()
    first = prototype.generate_episode(23, endpoint_threshold=threshold, bridge=bridge)
    again = prototype.generate_episode(23, endpoint_threshold=threshold, bridge=bridge)
    assert first == again
    assert first["parameters"] == {"endpoint_threshold": threshold}
    assert len(first["train"]) == 3 and len(first["test"]) == 1
    assert first["parameter_rivals"][str(3 - threshold)]["status"] == "refuted_by_demonstrations"
    assert first["parameter_rivals"][str(3 - threshold)]["demo_mismatches"] == [0, 1, 2]
    assert first["profiles"][0] == "rows"
    assert first["profiles"][1] == "columns"
    assert first["profiles"][2:] == ["mixed", "mixed"]
    for check in first["role_rotations"]:
        assert check["consistent_thresholds"] == [threshold]
    program = prototype.render_program(threshold)
    for pair in first["train"] + first["test"]:
        assert prototype.validate_input(pair["input"]) == []
        assert prototype.execute_program(bridge, program, pair["input"]) == pair["output"]


def test_same_inputs_support_both_settings_and_public_export_has_no_secrets(bridge):
    prototype = _prototype()
    episodes = [prototype.generate_episode(41, endpoint_threshold=t, bridge=bridge) for t in (1, 2)]
    assert [p["input"] for p in episodes[0]["train"] + episodes[0]["test"]] == [
        p["input"] for p in episodes[1]["train"] + episodes[1]["test"]
    ]
    for episode in episodes:
        public = prototype.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        public["train"][0]["input"][0][0] = 9
        assert episode["train"][0]["input"][0][0] != 9


def test_seed_selection_and_parameter_validation():
    prototype = _prototype()
    choices = [prototype.select_threshold(seed, "sample") for seed in range(32)]
    assert set(choices) == {1, 2}
    assert choices == [prototype.select_threshold(seed, "sample") for seed in range(32)]
    for invalid in (True, False, 1.0, "1", 0, 3, None):
        with pytest.raises((TypeError, ValueError)):
            prototype.render_program(invalid)
    for invalid in (True, 1.0, "1"):
        with pytest.raises((TypeError, ValueError)):
            prototype.select_threshold(invalid)
