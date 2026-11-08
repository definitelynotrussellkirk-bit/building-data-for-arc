"""Focused regression tests for 382eb0e592eb."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import sys

TASK_ID = "382eb0e592eb"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"reviewed_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def test_rule_pin_and_public_surface_are_narrow_and_exact():
    assert GEN.RULE_HASH == "03fbcf596117"
    assert GEN.VERSION == "3.0.0"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert set(GEN.AXES) == {"scene_profile"}
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "canonical_4x5",
        "semantic_3x6",
        "canonical_3x6",
        "semantic_4x5",
    )

from copy import deepcopy
import pytest
from reviewer_support import canonical_pairs, find_root


def _intended_output(grid):
    output = deepcopy(grid)
    height = len(grid)
    width = len(grid[0])
    for row in range(height - 1):
        for col in range(width - 1):
            value = grid[row][col]
            if value != 0 and grid[row][col + 1] == value:
                output[row + 1][col] = value
                output[row + 1][col + 1] = value
    return output


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


@pytest.mark.parametrize(
    "pair",
    _canonical_pairs(),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_accepted_and_original_input_oracle_matches(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert _intended_output(pair["input"]) == pair["output"]
    assert GEN.rule_mirror(pair["input"]) == pair["output"]

BANDS = (None, "easy", "medium", "hard")
PROFILE_DIMS = {
    "canonical_4x5": (4, 5),
    "semantic_3x6": (3, 6),
    "canonical_3x6": (3, 6),
    "semantic_4x5": (4, 5),
}


@pytest.mark.parametrize("band", BANDS)
def test_scheduled_profiles_are_exact_observable_and_deterministic(band):
    for index in range(8):
        expected = GEN.SCHEDULE_PROFILES[index % 4]
        assert GEN.schedule_profile(901, index, difficulty=band) == expected
        grid = GEN.generate(901, index, difficulty=band)
        assert grid == GEN.generate(901, index, difficulty=band)
        assert (len(grid), len(grid[0])) == PROFILE_DIMS[expected]
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.observe_overrides(grid) == {"scene_profile": expected}

    for profile in GEN.SCHEDULE_PROFILES:
        grid = GEN.generate(17, 99, difficulty=band, scene_profile=profile)
        assert GEN.observe_overrides(grid) == {"scene_profile": profile}


def _pair(grid):
    return {"input": grid, "output": _intended_output(grid)}


def test_executable_witnesses_reject_every_named_canonical_shortcut():
    expected_rivals = {
        "exact_domino_only",
        "copy_all_nonzero_down",
        "blank_below_only",
        "bottom_pair_upwards",
    }
    assert set(GEN.SEMANTIC_RIVALS) == expected_rivals
    assert set(GEN.CANONICAL_SHORTCUTS) == expected_rivals
    assert set(GEN.LESSON_COMPETITORS) == expected_rivals
    assert set(GEN.SEMANTIC_WITNESSES) == {
        "overlapping_pair_run",
        "nontrigger_vertical",
        "overwrite_nonzero_below",
        "bottom_row_pair",
    }

    for pair in _canonical_pairs():
        for rival in GEN.CANONICAL_SHORTCUTS.values():
            assert rival(pair["input"]) == pair["output"]

    for profile in ("semantic_3x6", "semantic_4x5"):
        for seed in range(12):
            grid = GEN.generate(seed, seed + 5, scene_profile=profile)
            expected = _intended_output(grid)
            assert all(witness(grid) for witness in GEN.SEMANTIC_WITNESSES.values())
            assert all(rival(grid) != expected for rival in GEN.SEMANTIC_RIVALS.values())


@pytest.mark.parametrize("band", BANDS)
def test_every_cyclic_four_pair_window_is_identifiable_under_all_query_rotations(band):
    for start in range(8):
        pairs = [_pair(GEN.generate(7331, start + offset, difficulty=band)) for offset in range(4)]
        assert {
            GEN.observe_overrides(pair["input"])["scene_profile"] for pair in pairs
        } == set(GEN.SCHEDULE_PROFILES)
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, pairs[query_index]) == []


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_non_integer_seed_is_rejected(bad_seed):
    with pytest.raises(ValueError):
        GEN.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_invalid_sample_index_is_rejected(bad_index):
    with pytest.raises(ValueError):
        GEN.generate(1, bad_index)


def test_self_check_rejects_minimal_single_color_impostors():
    short_line = [[0] * 5 for _ in range(4)]
    short_line[0][0:2] = [3, 3]
    solid_square = [[0] * 5 for _ in range(4)]
    solid_square[0][0:2] = [3, 3]
    solid_square[1][0:2] = [3, 3]
    assert GEN.self_check(short_line)
    assert GEN.self_check(solid_square)


def test_difficulty_bands_are_behaviorally_distinct_but_remain_exact_profiles():
    for index in range(8):
        grids = [GEN.generate(991, index, difficulty=band) for band in ("easy", "medium", "hard")]
        assert len({repr(grid) for grid in grids}) == 3
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)


def test_retained_racket_counterexample_refutes_every_declared_rival():
    import json

    record = json.loads(
        (HOME / "counterexamples" / "semantic_3x6_all_rivals.json").read_text()
    )
    grid = record["input"]
    expected = record["actual_racket_output"]
    assert record["rule_hash"] == GEN.RULE_HASH
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == expected
    assert all(witness(grid) for witness in GEN.SEMANTIC_WITNESSES.values())
    assert set(record["rival_outputs"]) == set(GEN.SEMANTIC_RIVALS)
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert rival(grid) == record["rival_outputs"][name]
        assert rival(grid) != expected
