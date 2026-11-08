"""Regression, override-contract, and teaching tests for 7b0c20fe6f33."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "7b0c20fe6f33"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
OLD_NARROW_VECTORS = {(1, 2), (2, 1), (-1, 2), (2, -1)}


def _cells(grid, color):
    return {
        (row_index, column_index)
        for row_index, row in enumerate(grid)
        for column_index, value in enumerate(row)
        if value == color
    }


def _marker_vector(grid):
    blue = next(iter(_cells(grid, 1)))
    red = next(iter(_cells(grid, 2)))
    return red[0] - blue[0], red[1] - blue[1]


def _independent_rule(grid):
    blue = next(iter(_cells(grid, 1)))
    red = next(iter(_cells(grid, 2)))
    dr, dc = red[0] - blue[0], red[1] - blue[1]
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        for column in range(width):
            value = grid[row][column]
            source_row, source_column = row - dr, column - dc
            source_value = (
                grid[source_row][source_column]
                if 0 <= source_row < height and 0 <= source_column < width
                else 0
            )
            if value in (1, 2):
                output[row][column] = value
            elif source_value == 3:
                output[row][column] = 8
            elif value != 0:
                output[row][column] = value
    return output


def _pair(grid):
    return {"input": grid, "output": _independent_rule(grid)}


def test_rule_pin_and_small_exact_axis_contract():
    assert GEN.RULE_HASH == "6f9c816ac7aa"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.SCHEDULE_PROFILES == (
        "canonical",
        "extended",
        "legacy_bridge",
        "cardinal",
    )
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "vector_choice",
        "motif_choice",
    }


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK_ID, root=find_root(__file__)),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_accepted_and_python_mirror_matches(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert GEN.rule_mirror(pair["input"]) == pair["output"]
    assert _independent_rule(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h,grid_w", [(9, 9), (10, 12), (16, 16)])
@pytest.mark.parametrize("vector_choice", range(16))
@pytest.mark.parametrize("motif_choice", range(11))
def test_every_exact_override_combination_is_constructive_and_observable(
    difficulty, grid_h, grid_w, vector_choice, motif_choice
):
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "vector_choice": vector_choice,
        "motif_choice": motif_choice,
    }
    grid = GEN.generate(
        7919 + vector_choice,
        motif_choice,
        difficulty=difficulty,
        **requested,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert GEN.rule_mirror(grid) == _independent_rule(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 8},
        {"grid_h": 17},
        {"grid_w": 8},
        {"grid_w": 17},
        {"vector_choice": -1},
        {"vector_choice": 16},
        {"motif_choice": -1},
        {"motif_choice": 11},
        {"grid_h": True},
        {"grid_w": 10.5},
        {"vector_choice": "3"},
        {"motif_choice": None},
        {"unknown_axis": 1},
        {"difficulty": "impossible"},
    ],
)
def test_invalid_controls_fail_loudly(kwargs):
    kwargs = dict(kwargs)
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty, **kwargs)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_four_profile_schedule_survives_every_query_rotation(difficulty):
    for start in range(12):
        grids = [
            GEN.generate(20_000 + start, start + offset, difficulty=difficulty)
            for offset in range(4)
        ]
        assert [
            GEN.schedule_profile(0, start + offset, difficulty=difficulty)
            for offset in range(4)
        ] == [
            GEN.SCHEDULE_PROFILES[(start + offset) % 4]
            for offset in range(4)
        ]
        pairs = [_pair(grid) for grid in grids]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                    difficulty,
                    start,
                    query_index,
                    name,
                )


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_distribution_covers_canonical_profiles_and_broad_domain(difficulty):
    grids = [GEN.generate(30_000 + index, index, difficulty=difficulty) for index in range(80)]
    assert all(GEN.self_check(grid) == [] for grid in grids)

    profiles = {
        (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        for grid in grids[:20]
    }
    assert profiles & {(10, 10, 4), (11, 11, 4), (12, 12, 4)}

    vectors = {_marker_vector(grid) for grid in grids}
    motif_sizes = {len(_cells(grid, 3)) for grid in grids}
    assert vectors & OLD_NARROW_VECTORS
    assert any(vector not in OLD_NARROW_VECTORS for vector in vectors)
    assert any(dr == 0 or dc == 0 for dr, dc in vectors)
    assert any(dr < 0 for dr, _ in vectors)
    assert any(dc < 0 for _, dc in vectors)
    assert motif_sizes == {3, 4, 5}

    for name, witness in GEN.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), name
    assert len({tuple(map(tuple, grid)) for grid in grids}) >= 76


def test_declared_witnesses_are_real_counterexamples_to_named_rivals():
    grids = [GEN.generate(40_000 + index, index, difficulty="medium") for index in range(24)]
    assert set(GEN.WITNESS_RIVALS) == set(GEN.SEMANTIC_WITNESSES)
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        matching = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert matching, witness_name
        assert set(rival_names) <= set(GEN.SEMANTIC_RIVALS)
        for grid in matching:
            truth = GEN.rule_mirror(grid)
            assert any(GEN.SEMANTIC_RIVALS[name](grid) != truth for name in rival_names)


def test_copy_first_three_is_a_real_canonical_shortcut_and_generated_counterexample_exists():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    shortcut = GEN.CANONICAL_SHORTCUTS["copy_first_three"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs)
    generated = [GEN.generate(50_000 + index, index) for index in range(12)]
    assert any(shortcut(grid) != GEN.rule_mirror(grid) for grid in generated)


def test_generation_and_semantic_helpers_are_deterministic_fresh_and_pure():
    for difficulty in (None, "easy", "medium", "hard"):
        for index in range(16):
            first = GEN.generate(61, index, difficulty=difficulty)
            second = GEN.generate(61, index, difficulty=difficulty)
            assert first == second
            assert first is not second
            assert all(left is not right for left, right in zip(first, second))
            before = deepcopy(first)
            assert GEN.rule_mirror(first) == _independent_rule(first)
            for rival in GEN.SEMANTIC_RIVALS.values():
                rival(first)
                assert first == before
            for witness in GEN.SEMANTIC_WITNESSES.values():
                witness(first)
                assert first == before


def test_self_check_rejects_near_miss_inputs():
    good = GEN.generate(72, 1, grid_h=12, grid_w=12, vector_choice=8, motif_choice=0)
    assert GEN.self_check(good) == []

    fixtures = {}
    fixtures["ragged"] = deepcopy(good)
    fixtures["ragged"][0].pop()
    fixtures["boolean"] = deepcopy(good)
    fixtures["boolean"][0][0] = True
    fixtures["extra_marker"] = deepcopy(good)
    empty = next(
        (r, c)
        for r, row in enumerate(good)
        for c, value in enumerate(row)
        if value == 0
    )
    fixtures["extra_marker"][empty[0]][empty[1]] = 1
    fixtures["foreign_color"] = deepcopy(good)
    fixtures["foreign_color"][empty[0]][empty[1]] = 9
    fixtures["disconnected_motif"] = deepcopy(good)
    green = sorted(_cells(good, 3))
    removed = green[-1]
    retained = set(green[:-1])
    disconnected = next(
        (r, c)
        for r, row in enumerate(good)
        for c, value in enumerate(row)
        if value == 0
        and all(abs(r - gr) + abs(c - gc) > 1 for gr, gc in retained)
    )
    fixtures["disconnected_motif"][removed[0]][removed[1]] = 0
    fixtures["disconnected_motif"][disconnected[0]][disconnected[1]] = 3

    for name, malformed in fixtures.items():
        assert GEN.self_check(malformed), name
