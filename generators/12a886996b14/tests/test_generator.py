"""Task-linked regressions for generator 12a886996b14."""
from __future__ import annotations

import copy
import importlib.util
import os
import random
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "12a886996b14"
ROOT = find_root(__file__)


def _load_generator():
    explicit = os.environ.get("GENERATOR_UNDER_TEST")
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.extend((
        Path(__file__).resolve().parents[1] / "generator.py",
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    ))
    path = next((candidate for candidate in candidates if candidate.is_file()), None)
    if path is None:
        raise RuntimeError(f"could not locate generator under test; tried {candidates!r}")
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
BANDS = ("easy", "medium", "hard")


def _pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def _components(grid, color):
    cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    result = []
    while cells:
        seed = min(cells)
        cells.remove(seed)
        stack = [seed]
        component = {seed}
        while stack:
            row, col = stack.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in cells:
                    cells.remove(neighbor)
                    component.add(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def test_rule_pin_and_all_canonical_pairs():
    assert GEN.RULE_HASH == "8de52d1da0e7"
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


@pytest.mark.parametrize("band", BANDS)
def test_exact_axes_round_trip_in_every_band(band):
    requested = {
        "grid_h": 9,
        "grid_w": 12,
        "marker_size": 6,
        "yellow_size": 8,
        "occlusion": "partial",
        "vector_direction": "up_left",
    }
    grid = GEN.generate(7100, 17, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert len(_components(grid, 4)) == 1
    assert GEN.rule_mirror(grid) != grid


@pytest.mark.parametrize("direction", (
    "up_left", "up", "up_right", "left",
    "right", "down_left", "down", "down_right",
))
def test_every_direction_override_is_real(direction):
    grid = GEN.generate(
        8100,
        9,
        difficulty="medium",
        grid_h=11,
        grid_w=15,
        marker_size=5,
        yellow_size=6,
        occlusion="none",
        vector_direction=direction,
    )
    observed = GEN.observe_overrides(grid)
    assert observed["vector_direction"] == direction
    assert observed["marker_size"] == 5
    assert observed["yellow_size"] == 6


def test_partial_occlusion_reconstructs_the_hidden_source_template():
    grid = GEN.generate(
        9001,
        1,
        grid_h=10,
        grid_w=14,
        marker_size=5,
        yellow_size=6,
        occlusion="partial",
        vector_direction="up_right",
    )
    profile = GEN.semantic_profile(grid)
    assert profile["valid"]
    assert profile["occlusion"] == "partial"
    assert profile["occluded_marker_cells"] >= 1
    assert len([value for row in grid for value in row if value == 3]) == 5
    assert len([value for row in grid for value in row if value == 2]) < 5
    assert GEN.self_check(grid) == []


def test_schedule_survives_every_query_rotation_against_declared_competitors():
    period = GEN.LESSON_SCHEDULE_PERIOD
    assert period == len(GEN.SCHEDULE_PROFILES)
    for start in range(period):
        grids = [GEN.generate(12000, start + offset, difficulty="medium") for offset in range(3)]
        assert sum(GEN.SEMANTIC_WITNESSES["upward_translation"](grid) for grid in grids) >= 2
        assert sum(GEN.SEMANTIC_WITNESSES["partial_source_occlusion"](grid) for grid in grids) >= 2
        pairs = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]
        for query_index in range(3):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, pairs[query_index]) == [], (start, query_index)


def test_always_down_shortcut_fits_canonical_but_generated_upward_witness_refutes_it():
    shortcut = GEN.CANONICAL_SHORTCUTS["always_down"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in _pairs())
    grid = GEN.generate(
        14001,
        1,
        grid_h=10,
        grid_w=14,
        marker_size=4,
        yellow_size=5,
        occlusion="partial",
        vector_direction="up_left",
    )
    assert GEN.SEMANTIC_WITNESSES["upward_translation"](grid)
    assert shortcut(grid) != GEN.rule_mirror(grid)


@pytest.mark.parametrize("mutation", (
    "missing_red",
    "missing_green",
    "wrong_green_shape",
    "disconnected_yellow",
    "out_of_bounds_translation",
    "unknown_color",
))
def test_validator_rejects_task_semantic_mutations(mutation):
    grid = GEN.generate(
        15000,
        5,
        grid_h=10,
        grid_w=14,
        marker_size=5,
        yellow_size=6,
        occlusion="none",
        vector_direction="down_right",
    )
    if mutation == "missing_red":
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if grid[row][col] == 2:
                    grid[row][col] = 0
    elif mutation == "missing_green":
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if grid[row][col] == 3:
                    grid[row][col] = 0
    elif mutation == "wrong_green_shape":
        row, col = next(
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == 3
        )
        grid[row][col] = 0
    elif mutation == "disconnected_yellow":
        yellow = sorted(
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == 4
        )
        for row, col in yellow:
            grid[row][col] = 0
        grid[0][0] = 4
        grid[-1][-1] = 4
        grid[0][1] = 4
    elif mutation == "out_of_bounds_translation":
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if grid[row][col] == 4:
                    grid[row][col] = 0
        grid[-1][-1] = 4
        grid[-1][-2] = 4
        grid[-2][-1] = 4
    elif mutation == "unknown_color":
        grid[0][0] = 9
    assert GEN.self_check(grid), mutation


def test_unknown_invalid_overrides_and_difficulty_fail_closed():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 0, marker_szie=4)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, marker_size=True)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, occlusion="total")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, vector_direction="diagonal-ish")
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="expert")


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(20261011)
    state = random.getstate()
    first = GEN.generate(987654, 77, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(987654, 77, difficulty="hard")
    assert state == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == GEN.generate(987654, 77, difficulty="hard")
