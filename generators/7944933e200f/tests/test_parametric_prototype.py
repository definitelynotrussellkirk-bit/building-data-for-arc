"""Focused tests for the proposed frequency-extreme prototype, not admission."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import json

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location("frequency_prototype", ROOT / "workspace/parametric/prototype.py")
prototype = module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)


def test_explicit_global_count_not_individual_size():
    grid = [[0] * 7 for _ in range(5)]
    grid[0][:2] = [2, 2]
    grid[2][0] = grid[2][2] = grid[2][4] = 3
    assert prototype.python_reference(grid) == [[2, 2]]
    assert prototype.python_reference(grid, "maximum") == [[3]]


def test_tie_keeps_first_row_major_component_for_both_settings():
    grid = [[0] * 5 for _ in range(5)]
    grid[0][3] = grid[0][4] = 8
    grid[3][0] = grid[4][0] = 2
    for setting in prototype.SETTINGS:
        assert prototype.python_reference(grid, setting) == [[8, 8]]


def test_four_connectivity_and_separate_same_color_boxes():
    grid = [[0] * 5 for _ in range(5)]
    grid[0][0] = grid[1][1] = 8
    grid[3][:3] = [2, 2, 2]
    assert prototype.python_reference(grid) == [[8]]
    assert prototype.python_reference(grid, "maximum") == [[2, 2, 2]]


def test_crop_retains_background_and_other_colors():
    grid = [[0] * 8 for _ in range(6)]
    grid[0][:3] = [2, 2, 2]
    grid[1][:3] = [2, 3, 0]
    grid[2][:3] = [2, 2, 2]
    grid[4] = [3] * 8
    assert prototype.python_reference(grid) == [[2, 2, 2], [2, 3, 0], [2, 2, 2]]


@pytest.mark.parametrize("setting", [None, "min", "MAXIMUM", 1, True])
def test_invalid_explicit_setting_rejected(setting):
    with pytest.raises((ValueError, TypeError)):
        prototype.emit_rule(setting)


def test_default_is_exact_canonical_rule_bytes():
    canonical = ROOT.parents[1] / "shared/data/base/solutions/training/d9fac9be__7944933e200f.json"
    assert prototype.emit_rule() == json.loads(canonical.read_text())["racket_target"]["target_code"]


@pytest.mark.parametrize("setting", prototype.SETTINGS)
def test_complete_episode_public_boundary_and_demo_identifiability(setting):
    with prototype.RacketRunner() as runner:
        episode = prototype.generate_episode(41, setting, runner=runner)
    public, private = episode["public"], episode["private"]
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3 and len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert set(public["test"][0]) == {"input"}
    assert private["parameters"] == {"frequency_extreme": setting}
    assert private["demo_consistent_settings"] == [setting]
    assert len(private["query_outputs"]) == 1
    rival = next(value for value in prototype.SETTINGS if value != setting)
    assert private["rival_demo_checks"][rival]["rejected_on_demo_indices"] == [0, 1, 2]
    assert private["phase_order"] == ["execute_demonstrations", "check_parameter_rivals", "execute_query"]
    assert all(receipt["backend"] == "RacketBridge" for receipt in private["executions"])


def test_seed_choice_is_episode_fixed_and_input_stream_shared_across_settings():
    assert prototype.choose_setting(91) == prototype.choose_setting(91)
    with prototype.RacketRunner() as runner:
        left = prototype.generate_episode(91, "minimum", runner=runner)
        right = prototype.generate_episode(91, "maximum", runner=runner)
        repeat = prototype.generate_episode(91, "minimum", runner=runner)
        auto = prototype.generate_episode(91, runner=runner)
    assert left == repeat
    assert auto["private"]["parameters"]["frequency_extreme"] == prototype.choose_setting(91)
    assert [pair["input"] for pair in left["public"]["train"]] == [pair["input"] for pair in right["public"]["train"]]
    assert left["public"]["test"] == right["public"]["test"]
    assert any(a["output"] != b["output"] for a, b in zip(left["public"]["train"], right["public"]["train"]))


def test_racket_agrees_with_explicit_semantic_witnesses():
    cases = prototype.semantic_witnesses()
    assert {case["name"] for case in cases} >= {"global_fragmentation", "row_major_tie", "diagonal_split", "unmasked_intruder"}
    with prototype.RacketRunner() as runner:
        for case in cases:
            for setting in prototype.SETTINGS:
                assert runner.execute(case["input"], setting) == case["expected"][setting]
