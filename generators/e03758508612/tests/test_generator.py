"""Focused repair tests for e03758508612."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "e03758508612"
HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    is_midpoint_grid,
    load_generator,
    midpoint_rival,
    observed,
    priority_output,
)

GEN = load_generator()
CANONICAL_PROFILES = {(8, 10, 5), (9, 9, 5), (9, 11, 5), (10, 12, 5)}


def profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_pin_and_small_exact_contract():
    assert GEN.RULE_HASH == "d93ad16a99ae"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {"grid_h", "grid_w", "layout", "seed_pattern"}
    assert set(GEN.SCHEDULE_PROFILES) == set(range(8))


def test_all_canonical_inputs_are_accepted_and_match_independent_rule():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert priority_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 8, "grid_w": 9, "layout": "horizontal", "seed_pattern": "single"},
        {"grid_h": 10, "grid_w": 12, "layout": "vertical", "seed_pattern": "mixed"},
        {"grid_h": 14, "grid_w": 17, "layout": "grid", "seed_pattern": "double"},
    ],
)
def test_exact_overrides_are_constructive_and_observable(band, kwargs):
    grid = GEN.generate(17, 23, difficulty=band, **kwargs)
    assert GEN.self_check(grid) == []
    assert observed(grid) == kwargs
    assert GEN.observe_overrides(grid) == kwargs
    assert priority_output(grid) != grid


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 7},
        {"grid_h": 15},
        {"grid_w": 8},
        {"grid_w": 18},
        {"layout": "diagonal"},
        {"seed_pattern": "triple"},
        {"grid_h": True},
        {"grid_w": 10.5},
        {"layout": 3},
        {"seed_pattern": None, "unknown_axis": 1},
        {"unknown_axis": 1},
        {"difficulty": "impossible"},
    ],
)
def test_invalid_controls_are_rejected(kwargs):
    values = dict(kwargs)
    difficulty = values.pop("difficulty", None)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty, **values)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", None])
def test_seed_requires_literal_integer(seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", None, -1])
def test_sample_index_requires_nonnegative_literal_integer(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(991, sample_index)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_pinned_profile_floor_has_exact_support_in_every_band(band):
    exact = 0
    for index in range(20):
        digest = hashlib.sha256(
            f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
        ).hexdigest()
        seed = int(digest[:12], 16)
        grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
        assert GEN.self_check(grid) == []
        exact += profile(grid) in CANONICAL_PROFILES
    assert exact >= 1, (band, exact)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_schedule_covers_canonical_shapes_and_real_wall_parsing(band):
    grids = [GEN.generate(991, index, difficulty=band) for index in range(32)]
    profiles = {profile(grid) for grid in grids}
    assert CANONICAL_PROFILES <= profiles
    assert {observed(grid)["layout"] for grid in grids} == {"horizontal", "vertical", "grid"}
    assert {observed(grid)["seed_pattern"] for grid in grids} == {"single", "mixed", "double"}
    assert any(not is_midpoint_grid(grid) for grid in grids if observed(grid)["layout"] == "grid")
    assert any(midpoint_rival(grid) != priority_output(grid) for grid in grids)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_inputs_match_independent_oracle_and_declared_rivals(band):
    wall_witnesses = 0
    priority_witnesses = 0
    for index in range(48):
        grid = GEN.generate(3001 + index, index * 13 + 5, difficulty=band)
        assert GEN.self_check(grid) == []
        assert grid == GEN.generate(3001 + index, index * 13 + 5, difficulty=band)
        truth = priority_output(grid)
        wall = GEN.SEMANTIC_RIVALS["midpoint_partition"](grid)
        low = GEN.SEMANTIC_RIVALS["lowest_priority"](grid)
        assert wall == midpoint_rival(grid)
        assert low == priority_output(grid, reverse=True)
        if GEN.SEMANTIC_WITNESSES["wall_parsing"](grid):
            wall_witnesses += 1
            assert wall != truth
        if GEN.SEMANTIC_WITNESSES["priority_order"](grid):
            priority_witnesses += 1
            assert low != truth
    assert wall_witnesses > 0
    assert priority_witnesses > 0


def test_helpers_are_pure_and_return_fresh_grids():
    grid = GEN.generate(51, 7, layout="horizontal", seed_pattern="mixed")
    original = deepcopy(grid)
    assert GEN.observe_overrides(grid) == observed(grid)
    for helper in list(GEN.SEMANTIC_RIVALS.values()) + list(GEN.SEMANTIC_WITNESSES.values()):
        helper(grid)
        assert grid == original
    again = GEN.generate(51, 7, layout="horizontal", seed_pattern="mixed")
    assert again == grid and again is not grid
    assert all(a is not b for a, b in zip(again, grid))


@pytest.mark.parametrize(
    "bad",
    [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(8)]],
)
def test_self_check_handles_malformed_inputs_without_exception(bad):
    assert GEN.self_check(bad)


def test_self_check_rejects_missing_frame_seed_and_unknown_color():
    grid = GEN.generate(71, 9, layout="grid", seed_pattern="mixed")
    cases = []

    missing_wall = deepcopy(grid)
    missing_wall[1][0] = 0
    cases.append(missing_wall)

    no_seed = deepcopy(grid)
    legend = set(no_seed[0][:3])
    first_room = next(iter(GEN._legend_chambers(no_seed)))
    for row, column in first_room:
        if no_seed[row][column] in legend:
            no_seed[row][column] = 0
    cases.append(no_seed)

    unknown = deepcopy(grid)
    for row in range(2, len(unknown) - 1):
        for column in range(1, len(unknown[0]) - 1):
            if unknown[row][column] == 0:
                unknown[row][column] = 5 if 5 not in legend else 9
                break
        else:
            continue
        break
    cases.append(unknown)

    assert all(GEN.self_check(case) for case in cases)


def test_retained_midpoint_counterexample_replays_against_current_source():
    import json

    path = HOME / "counterexamples" / "midpoint-rival-generated.json"
    assert path.is_file(), f"missing retained counterexample: {path}"
    case = json.loads(path.read_text())
    grid = GEN.generate(
        case["seed"],
        case["sample_index"],
        difficulty=case["difficulty"],
        **case["overrides"],
    )
    assert grid == case["input"]
    assert GEN.self_check(grid) == []
    assert priority_output(grid) == case["racket_output"]
    assert midpoint_rival(grid) == case["midpoint_rival_output"]
    assert case["racket_output"] != case["midpoint_rival_output"]
