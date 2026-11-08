"""Task-local regressions for the beam/mirror generator repair."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import random
import sys

import pytest

TASK_DIR = Path(__file__).resolve().parents[1]
for candidate in (TASK_DIR, *TASK_DIR.parents):
    if (candidate / "shared/runtime/puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(candidate / "shared/runtime"))
        break
    if (candidate / "puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    raise RuntimeError("no independent puzzle_generators runtime found")
sys.path.insert(0, str(TASK_DIR / "workspace"))

from reference_probe import (  # noqa: E402
    base_authority_path,
    canonical_pairs,
    canonical_row,
    first_two_mirrors_rival,
    intended_output,
    load_generator,
    normalized_rule_hash,
    observed,
    repeat_first_turn_side_rival,
    stop_at_first_obstacle_rival,
    straight_to_edge_rival,
    swapped_mirrors_rival,
    trace,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")
RIVALS = {
    "straight_to_edge": straight_to_edge_rival,
    "stop_at_first_obstacle": stop_at_first_obstacle_rival,
    "swapped_mirrors": swapped_mirrors_rival,
    "first_two_mirrors_only": first_two_mirrors_rival,
    "repeat_first_turn_side": repeat_first_turn_side_rival,
}
ALWAYS_REFUTED_RIVALS = {
    name: rival for name, rival in RIVALS.items()
    if name not in {"first_two_mirrors_only", "repeat_first_turn_side"}
}


def test_rule_pin_and_selected_authority_are_exact():
    canonical = canonical_row()["program_solution"]
    record = json.loads(base_authority_path().read_text(encoding="utf-8"))
    assert normalized_rule_hash(canonical) == "b28f2ec65f40"
    assert gen.RULE_HASH == "b28f2ec65f40"
    assert record["racket_target"]["raw_code"] == canonical
    assert record["racket_target"]["target_code"] == canonical


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "train3", "test0"])
def test_canonical_pairs_are_accepted_and_match_independent_oracle(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("direction", ["up", "down", "left", "right"])
@pytest.mark.parametrize("turn_side", ["left", "right"])
def test_exact_boundary_overrides_are_observable_and_interactive(band, direction, turn_side):
    requested = {
        "grid_h": 9,
        "grid_w": 12,
        "n_mirrors": 2,
        "n_walls": 0,
        "direction": direction,
        "turn_side": turn_side,
    }
    grid = gen.generate(1701, 22, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band) == []
    assert gen.strict_canonical_like(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested
    output, report = trace(grid)
    assert len(report["mirrors"]) == 2
    assert {item[2] for item in report["mirrors"]} == {4, 6}
    assert report["stop"] == "edge"
    assert output == gen._intended_output(grid)


@pytest.mark.parametrize("band", BANDS)
def test_maximum_counts_are_exact_and_wall_stops_the_beam(band):
    requested = {
        "grid_h": 18,
        "grid_w": 20,
        "n_mirrors": 6,
        "n_walls": 6,
        "direction": "right",
        "turn_side": "right",
    }
    grid = gen.generate(901, 7, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band) == []
    assert observed(grid) == requested
    _, report = trace(grid)
    assert report["stop"] == "wall"
    assert len(report["mirrors"]) == requested["n_mirrors"]
    assert set(report["turn_sides"]) == {"left", "right"}


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"texture": "default"},
        {"palette_size": 5},
        {"grid_h": 8},
        {"grid_h": 19},
        {"grid_w": 11},
        {"grid_w": 21},
        {"n_mirrors": 1},
        {"n_mirrors": 7},
        {"n_walls": -1},
        {"n_walls": 7},
        {"direction": "diagonal"},
        {"turn_side": "center"},
        {"grid_h": True},
        {"n_mirrors": 2.0},
        {"n_walls": "2"},
    ],
)
def test_unknown_out_of_range_and_wrong_type_overrides_fail_closed(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("difficulty", ["trivial", 0.5, True])
def test_invalid_difficulty_fails_closed(difficulty):
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_deterministic_valid_and_canonical_supported(band):
    random.seed(9917)
    state = random.getstate()
    grids = [gen.generate(5000 + i, i * 7, difficulty=band) for i in range(160)]
    assert random.getstate() == state
    assert all(gen.self_check(grid, difficulty=band) == [] for grid in grids)
    assert all(gen.strict_canonical_like(grid) == [] for grid in grids)
    assert all(grid == gen.generate(5000 + i, i * 7, difficulty=band) for i, grid in enumerate(grids))
    stats = [observed(grid) for grid in grids]
    assert {item["direction"] for item in stats} == {"up", "down", "left", "right"}
    assert {item["turn_side"] for item in stats} == {"left", "right"}
    assert {item["n_mirrors"] for item in stats} == set(range(2, 7))
    assert {item["n_walls"] for item in stats} == set(range(0, 7))
    canonical_profiles = {(9, 12, 5), (9, 13, 6), (10, 12, 6), (10, 13, 6), (11, 12, 5)}
    first_twenty = grids[:20]
    profiles = {
        (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        for grid in first_twenty
    }
    assert profiles & canonical_profiles


def test_declared_shortcuts_fit_every_canonical_pair():
    assert set(gen.CANONICAL_SHORTCUTS) == set(RIVALS)
    for name, rival in RIVALS.items():
        assert all(rival(deepcopy(pair["input"])) == pair["output"] for pair in canonical_pairs()), name
        assert gen.CANONICAL_SHORTCUTS[name](canonical_pairs()[0]["input"]) == canonical_pairs()[0]["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_default_example_uses_all_mirrors_and_refutes_core_rivals(band):
    for index in range(48):
        grid = gen.generate(7300 + index, index, difficulty=band)
        truth, report = trace(grid)
        stats = observed(grid)
        assert gen._intended_output(grid) == truth
        assert len(report["mirrors"]) == stats["n_mirrors"]
        assert all(rival(deepcopy(grid)) != truth for rival in ALWAYS_REFUTED_RIVALS.values())
        assert gen.SEMANTIC_WITNESSES["all_mirrors_interact"](grid)
        if stats["n_mirrors"] >= 3:
            assert set(report["turn_sides"]) == {"left", "right"}
            assert first_two_mirrors_rival(deepcopy(grid)) != truth
            assert repeat_first_turn_side_rival(deepcopy(grid)) != truth
            assert gen.SEMANTIC_WITNESSES["mixed_turn_route"](grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_demo_window_refutes_all_declared_rivals(band):
    assert gen.EXAMPLES_NEEDED == 3
    for start in range(15):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(8800 + start, sample_index, difficulty=band)
            demos.append({"input": grid, "output": intended_output(grid)})
        query_grid = gen.generate(8800 + start, start + gen.EXAMPLES_NEEDED, difficulty=band)
        query = {"input": query_grid, "output": intended_output(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in RIVALS.items():
            assert any(rival(deepcopy(pair["input"])) != pair["output"] for pair in demos), name


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 0]],
        [[True, 0], [0, 1]],
        [[10, 0], [0, 1]],
        [[2, 1]],
        [[2, 0], [0, 1]],
    ],
)
def test_malformed_or_semantically_empty_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)
