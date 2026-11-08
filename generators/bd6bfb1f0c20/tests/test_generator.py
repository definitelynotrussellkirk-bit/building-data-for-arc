"""Focused regression tests for the perimeter-sorted palette-row sampler."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
from typing import Any

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "bd6bfb1f0c20"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _components(grid: list[list[int]]) -> list[tuple[int, list[tuple[int, int]]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, list[tuple[int, int]]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, cells))
    return result


def _perimeter(cells: list[tuple[int, int]]) -> int:
    occupied = set(cells)
    return sum(
        (row + dr, col + dc) not in occupied
        for row, col in occupied
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
    )


def solve_perimeter(grid: list[list[int]]) -> list[list[int]]:
    ranked = sorted(_components(grid), key=lambda item: (-_perimeter(item[1]), item[0]))
    return [[color for color, _ in ranked]]


def solve_area(grid: list[list[int]]) -> list[list[int]]:
    ranked = sorted(_components(grid), key=lambda item: (-len(item[1]), item[0]))
    return [[color for color, _ in ranked]]


def solve_position(grid: list[list[int]]) -> list[list[int]]:
    ranked = sorted(_components(grid), key=lambda item: min(item[1]))
    return [[color for color, _ in ranked]]


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({cell for row in grid for cell in row})


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True),
)
def test_canonical_inputs_are_accepted_and_independent_oracle_matches(pair):
    assert gen.self_check(deepcopy(pair["input"])) == []
    assert solve_perimeter(pair["input"]) == pair["output"]


def test_pins_the_selected_rule_and_declares_the_lesson_contract():
    assert gen.RULE_HASH == "4f629ec7a9de"
    assert gen.EXAMPLES_NEEDED == 4
    assert set(gen.LESSON_COMPETITORS) == {"area_order", "position_order"}
    assert set(gen.SEMANTIC_RIVALS) == {"area_order", "position_order"}
    assert set(gen.SEMANTIC_WITNESSES) == {
        "area_differs_from_perimeter",
        "position_differs_from_perimeter",
    }


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_generated_draw_is_a_lawful_shortcut_counterexample(band):
    for sample_index in range(32):
        grid = gen.generate(1000 + sample_index, sample_index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        components = _components(grid)
        assert sorted(len(cells) for _, cells in components) == [1, 4, 4]
        assert sorted(_perimeter(cells) for _, cells in components) == [4, 8, 10]
        official = solve_perimeter(grid)
        assert official != solve_area(grid)
        assert official != solve_position(grid)
        assert gen.SEMANTIC_RIVALS["area_order"](grid) == solve_area(grid)
        assert gen.SEMANTIC_RIVALS["position_order"](grid) == solve_position(grid)
        assert gen.SEMANTIC_WITNESSES["area_differs_from_perimeter"](grid)
        assert gen.SEMANTIC_WITNESSES["position_differs_from_perimeter"](grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_consecutive_demonstrations_identify_declared_rivals(band):
    for start in range(16):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(7000 + start, sample_index, difficulty=band)
            demos.append({"input": grid, "output": solve_perimeter(grid)})
        assert gen.lesson_identifiable(demos, demos[-1]) == []
        for competitor in gen.LESSON_COMPETITORS.values():
            assert any(competitor(pair["input"]) != pair["output"] for pair in demos)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(8, 11), (8, 18), (16, 11), (16, 18)])
def test_exact_dimension_overrides_round_trip_in_every_band(band, height, width):
    grid = gen.generate(17, 9, difficulty=band, grid_h=height, grid_w=width)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"grid_h": height, "grid_w": width}


@pytest.mark.parametrize(
    "kwargs,error",
    [
        ({"seed": True, "sample_index": 0}, TypeError),
        ({"seed": 0, "sample_index": True}, TypeError),
        ({"seed": 0, "sample_index": 1.0}, TypeError),
        ({"seed": 0, "sample_index": -1}, ValueError),
        ({"seed": 0, "sample_index": 0, "difficulty": "expert"}, ValueError),
        ({"seed": 0, "sample_index": 0, "typo_axis": 1}, ValueError),
        ({"seed": 0, "sample_index": 0, "grid_h": 7}, ValueError),
        ({"seed": 0, "sample_index": 0, "grid_h": 17}, ValueError),
        ({"seed": 0, "sample_index": 0, "grid_w": 10}, ValueError),
        ({"seed": 0, "sample_index": 0, "grid_w": 19}, ValueError),
        ({"seed": 0, "sample_index": 0, "grid_h": True}, TypeError),
        ({"seed": 0, "sample_index": 0, "grid_w": 12.0}, TypeError),
    ],
)
def test_rejects_invalid_calls_and_unknown_or_inexact_controls(kwargs: dict[str, Any], error):
    seed = kwargs.pop("seed")
    sample_index = kwargs.pop("sample_index")
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises(error):
        gen.generate(seed, sample_index, difficulty=difficulty, **kwargs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_hits_both_canonical_profiles_in_each_band(band):
    profiles = {
        _profile(gen.generate(31, sample_index, difficulty=band))
        for sample_index in range(8)
    }
    assert (8, 12, 4) in profiles
    assert (9, 13, 4) in profiles


def test_self_check_rejects_shape_color_and_contact_mutations():
    grid = gen.generate(41, 7, grid_h=8, grid_w=11)

    wrong_shape = deepcopy(grid)
    color, cells = max(_components(wrong_shape), key=lambda item: _perimeter(item[1]))
    row, col = cells[0]
    wrong_shape[row][col] = 0
    assert gen.self_check(wrong_shape)

    extra_color = deepcopy(grid)
    empty = next((r, c) for r, row in enumerate(extra_color) for c, value in enumerate(row) if value == 0)
    extra_color[empty[0]][empty[1]] = 9 if 9 not in {c for c, _ in _components(grid)} else 8
    assert gen.self_check(extra_color)

    touching = deepcopy(grid)
    components = _components(touching)
    first = components[0][1][0]
    second_color = components[1][0]
    for nr, nc in ((first[0] - 1, first[1]), (first[0] + 1, first[1]), (first[0], first[1] - 1), (first[0], first[1] + 1)):
        if 0 <= nr < len(touching) and 0 <= nc < len(touching[0]) and touching[nr][nc] == 0:
            touching[nr][nc] = second_color
            break
    assert gen.self_check(touching)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(8)]])
def test_malformed_grid_returns_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)


def test_metadata_does_not_advertise_undeclared_texture_controls():
    assert not getattr(gen, "HELPFUL_TEXTURES", ())
    assert not getattr(gen, "DEGENERATE_TEXTURES", ())
    assert not getattr(gen, "LAWFUL_DEGENERATE_TEXTURES", ())


def test_pinned_semantic_census_draw_refutes_position_order():
    grid = gen.generate(146393197081358, 1981, difficulty="easy")
    assert solve_position(grid) != solve_perimeter(grid)
