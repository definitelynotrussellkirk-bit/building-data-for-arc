"""Portable regressions for the scan-order bounding-box fill generator."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import pytest

TASK_ID = "021fb6acf24f"
HOME = Path(__file__).resolve().parents[1]
LIBRARY = next(
    (path for path in Path(__file__).resolve().parents if (path / "shared/runtime").is_dir()),
    None,
)
if LIBRARY is not None:
    sys.path.insert(0, str(LIBRARY / "shared/runtime"))
sys.path.insert(0, str(HOME / "workspace"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402
from reference_probe import (  # noqa: E402
    has_order_contest,
    identity,
    late_overwrite,
    load_generator,
    scan_color_order,
    observed,
    profile,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
CANONICAL_PROFILES = {profile(pair["input"]) for pair in PAIRS}


def labeled(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": deepcopy(grid), "output": rule_output(grid)}


def test_metadata_pins_authority_and_keeps_only_exact_observable_axes():
    assert gen.GENERATOR_ID == gen.TASK_ID == TASK_ID
    assert gen.RULE_HASH == "9a7f76b1ea86"
    assert gen.VERSION == "3.0.1"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 5
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_colors"}
    assert tuple(gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_accepts_every_canonical_input_and_independent_oracle_matches(pair):
    frozen = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]
    assert pair["input"] == frozen


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 6, "grid_w": 8, "n_colors": 1},
        {"grid_h": 10, "grid_w": 11, "n_colors": 2},
        {"grid_h": 8, "grid_w": 9, "n_colors": 2},
    ],
)
def test_exact_overrides_are_constructive_observable_and_band_independent(band, requested):
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
    assert gen.observe_overrides(grid) == requested
    assert observed(grid) == requested
    assert rule_output(grid) != grid
    if requested["n_colors"] == 2:
        assert has_order_contest(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 5}, {"grid_h": 11}, {"grid_h": True}, {"grid_h": 8.0},
        {"grid_w": 7}, {"grid_w": 12}, {"grid_w": False}, {"grid_w": "9"},
        {"n_colors": 0}, {"n_colors": 3}, {"n_colors": True}, {"n_colors": 2.0},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_schedule_exactly_cycles_all_canonical_profiles_and_teaches_order(band):
    seen_profiles = set()
    for start in range(10):
        cycle = [gen.generate(900 + start, start + offset, difficulty=band) for offset in range(5)]
        assert [gen.schedule_profile(900 + start, start + offset, band)
                for offset in range(5)] == [
                    gen.schedule_profile(0, start + offset, band) for offset in range(5)
                ]
        seen_profiles.update(profile(grid) for grid in cycle)
        assert all(gen.self_check(grid) == [] for grid in cycle)
        assert sum(has_order_contest(grid) for grid in cycle) == 3
    assert seen_profiles == CANONICAL_PROFILES
    assert set(gen.SCHEDULE_PROFILES) == {
        gen.schedule_profile(0, index, band) for index in range(gen.LESSON_SCHEDULE_PERIOD)
    }


def test_declared_shortcuts_fit_all_canonical_labels_and_counterexample_refutes_them():
    assert all(scan_color_order(pair["input"]) == pair["output"] for pair in PAIRS)
    assert all(late_overwrite(pair["input"]) == pair["output"] for pair in PAIRS)
    evidence = json.loads((HOME / "counterexamples" / "scan-order-overlap.json").read_text())
    grid = evidence["input"]
    assert gen.self_check(grid) == []
    assert rule_output(grid) == evidence["intended_output"]
    assert scan_color_order(grid) == evidence["scan_color_order_output"]
    assert late_overwrite(grid) == evidence["late_overwrite_output"]
    assert rule_output(grid) != scan_color_order(grid)
    assert rule_output(grid) != late_overwrite(grid)
    assert gen.CANONICAL_SHORTCUTS["scan_color_order"](grid) == scan_color_order(grid)
    assert gen.CANONICAL_SHORTCUTS["late_overwrite"](grid) == late_overwrite(grid)
    assert gen.SEMANTIC_WITNESSES["scan_order_overlap"](grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_consecutive_four_pair_lesson_and_rotation_identifies_rule(band):
    for start in range(20):
        pairs = [labeled(gen.generate(1300 + start, start + offset, difficulty=band))
                 for offset in range(4)]
        assert sum(has_order_contest(pair["input"]) for pair in pairs) >= 2
        for held_out in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != held_out]
            assert any(has_order_contest(pair["input"]) for pair in demos)
            assert gen.lesson_identifiable(demos, pairs[held_out]) == []


@pytest.mark.parametrize(
    "mutation",
    ["third_color", "third_anchor", "one_anchor", "collinear", "bad_color", "ragged", "bool_cell"],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(41, 6, n_colors=2)
    colors = [value for row in grid for value in row if value]
    first = colors[0]
    if mutation == "third_color":
        occupied = set(colors)
        replacement = next(value for value in range(1, 10) if value not in occupied)
        grid[0][0] = replacement
    elif mutation == "third_anchor":
        grid[0][0] = first
    elif mutation == "one_anchor":
        removed = False
        for row in grid:
            for col, value in enumerate(row):
                if value == first and not removed:
                    row[col] = 0
                    removed = True
    elif mutation == "collinear":
        points = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == first]
        (r0, c0), (r1, c1) = points
        grid[r1][c1] = 0
        target_col = c0 + 1 if c0 + 1 < len(grid[0]) else c0 - 1
        grid[r0][target_col] = first
    elif mutation == "bad_color":
        grid[0][0] = 10
    elif mutation == "ragged":
        grid[0].pop()
    elif mutation == "bool_cell":
        grid[0][0] = True
    assert gen.self_check(grid)



def test_difficulty_bands_change_geometry_without_changing_the_public_profile():
    for index in range(gen.LESSON_SCHEDULE_PERIOD):
        grids = {band: gen.generate(606, index, difficulty=band)
                 for band in ("easy", "medium", "hard")}
        assert len({json.dumps(grid, separators=(",", ":")) for grid in grids.values()}) == 3
        assert len({profile(grid) for grid in grids.values()}) == 1
        assert all(gen.self_check(grid) == [] for grid in grids.values())

def test_generation_is_deterministic_and_semantic_helpers_do_not_mutate_inputs():
    for band in (None, "easy", "medium", "hard"):
        for index in range(12):
            first = gen.generate(8128, index, difficulty=band)
            assert first == gen.generate(8128, index, difficulty=band)
            frozen = deepcopy(first)
            assert gen.observe_overrides(first) == observed(first)
            _ = rule_output(first)
            _ = gen.strict_canonical_like(first)
            for rival in gen.LESSON_COMPETITORS.values():
                _ = rival(first)
            assert first == frozen



def test_every_generated_output_retains_background():
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            output = rule_output(gen.generate(71, index, difficulty=band))
            assert any(value == 0 for row in output for value in row)

def test_identity_is_refuted_by_every_generated_demo():
    for index in range(20):
        grid = gen.generate(52, index)
        assert identity(grid) != rule_output(grid)
        assert gen.LESSON_COMPETITORS["identity"](grid) == identity(grid)
