"""Source-bound regression tests for the defba1ab4f90 stream generator.

The parser, oracle, observed-axis recovery, and semantic rivals come from the
independent workspace probe rather than production helpers.
"""
from __future__ import annotations

from copy import deepcopy
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    analyze,
    canonical_pairs,
    ignore_bar_color_output,
    load_generator,
    no_left_chirality_flip_output,
    observed,
    racket_outputs,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

EXPECTED_AXES = {
    "orientation", "flow_length", "lane_width", "n_turns", "n_distractors"
}
ORIENTATIONS = ("top", "left")


def _pair(seed: int, index: int, band):
    grid = gen.generate(seed, index, difficulty=band)
    return {"input": grid, "output": rule_output(grid)}


def test_public_contract_is_rule_pinned_and_axes_are_exact():
    assert gen.RULE_HASH == "c58d2da3a0e5"
    assert gen.VERSION == "2.0.0"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "top_canonical_a", "left_short", "top_canonical_b", "left_tall"
    )


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"v{pair['variant']}-{pair['split']}-{pair['pair_index']}",
)
def test_all_canonical_pairs_are_accepted_and_match_independent_oracle(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_boundary_overrides_are_constructive_exact_and_observable(band):
    cases = itertools.product(
        ORIENTATIONS,
        (19, 29),
        (10, 15),
        (4, 8),
        (0, 6),
    )
    for index, values in enumerate(cases):
        requested = dict(zip(sorted(EXPECTED_AXES), values))
        # zip(sorted(...)) is intentionally avoided below: semantic names matter.
        requested = {
            "orientation": values[0],
            "flow_length": values[1],
            "lane_width": values[2],
            "n_turns": values[3],
            "n_distractors": values[4],
        }
        grid = gen.generate(100_000 + index, index, difficulty=band, **requested)
        assert gen.self_check(grid) == [], requested
        assert observed(grid) == requested
        assert gen.observe_overrides(grid) == requested
        assert gen.rule_mirror(grid) == rule_output(grid)


@pytest.mark.parametrize("overrides", [
    {"typo_axis": 1},
    {"orientation": "bottom"},
    {"orientation": 1},
    {"flow_length": 18},
    {"flow_length": 30},
    {"flow_length": True},
    {"lane_width": 9},
    {"lane_width": 16},
    {"lane_width": 12.0},
    {"n_turns": 3},
    {"n_turns": 9},
    {"n_turns": "4"},
    {"n_distractors": -1},
    {"n_distractors": 7},
    {"n_distractors": False},
])
def test_invalid_and_unknown_overrides_fail_closed(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_invalid_difficulty_fails_closed():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty="impossible")


@pytest.mark.parametrize("grid", [
    None,
    [],
    [[]],
    [[0], [0, 1]],
    [[True, 0], [0, 0]],
    [[2, 0, 0], [0, 0, 0], [0, 0, 0]],  # corner marker
    [[0, 2, 0], [0, 4, 0], [0, 0, 0]],  # illegal color
    [[0, 2, 0], [0, 0, 0], [0, 2, 0]],  # two markers
    [[0, 2, 0, 0], [0, 1, 1, 1], [0, 0, 0, 0]],  # one color / one turn
    [[0, 2, 0, 0], [1, 1, 1, 0], [0, 0, 0, 0]],  # stream steered off edge
])
def test_validator_rejects_malformed_or_semantically_incomplete_grids(grid):
    assert gen.self_check(grid)


def test_default_schedule_has_both_orientations_in_every_three_demo_window():
    for band in (None, "easy", "medium", "hard"):
        for start in range(24):
            profiles = [
                gen.schedule_profile(7, start + offset, band)
                for offset in range(4)
            ]
            assert profiles == [
                gen.SCHEDULE_PROFILES[
                    (start + offset + gen.DIFFICULTY_OFFSETS[band]) % 4
                ]
                for offset in range(4)
            ]
            grids = [
                gen.generate(700_000 + start, start + offset, difficulty=band)
                for offset in range(4)
            ]
            assert {observed(grid)["orientation"] for grid in grids[:3]} == {
                "top", "left"
            }
            for query_index in range(4):
                demos = [
                    {"input": deepcopy(grid), "output": rule_output(grid)}
                    for index, grid in enumerate(grids)
                    if index != query_index
                ]
                query = {"input": deepcopy(grids[query_index])}
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(
                        rival(demo["input"]) != demo["output"] for demo in demos
                    ), name


def test_each_scheduled_grid_refutes_color_blindness_and_left_grids_refute_no_flip():
    for index in range(40):
        grid = gen.generate(810_000 + index, index)
        expected = rule_output(grid)
        assert ignore_bar_color_output(grid) != expected
        assert gen.SEMANTIC_RIVALS["ignore_bar_color"](grid) != expected
        if observed(grid)["orientation"] == "left":
            assert no_left_chirality_flip_output(grid) != expected
            assert gen.SEMANTIC_RIVALS["no_left_chirality_flip"](grid) != expected


def test_generated_distribution_is_lawful_varied_and_oracle_exact():
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        seen = {axis: set() for axis in EXPECTED_AXES}
        inputs = set()
        for index in range(180):
            seed = 900_000 + band_index * 10_000 + index
            grid = gen.generate(seed, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.rule_mirror(grid) == rule_output(grid)
            values = observed(grid)
            for axis, value in values.items():
                seen[axis].add(value)
            inputs.add(json.dumps(grid, separators=(",", ":")))
        assert seen["orientation"] == {"top", "left"}
        assert seen["flow_length"] >= {19, 22, 29}
        assert seen["lane_width"] >= {12, 13}
        assert seen["n_turns"] == {4, 5, 6, 7, 8}
        assert seen["n_distractors"] == {0, 1, 2, 3, 4, 5, 6}
        assert len(inputs) >= 150


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261007)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_python_hashseed_does_not_change_generation():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
            env=env,
            text=True,
        ))
    assert results[0] == results[1]


def test_real_racket_authority_matches_independent_oracle_on_generated_cases():
    grids = [gen.generate(990_000 + index, index) for index in range(12)]
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]


def test_validator_and_mirror_are_input_pure():
    grid = gen.generate(
        44, 7, orientation="left", flow_length=29, lane_width=15,
        n_turns=8, n_distractors=6,
    )
    original = deepcopy(grid)
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == rule_output(grid)
    assert analyze(grid)["n_turns"] == 8
    assert grid == original
