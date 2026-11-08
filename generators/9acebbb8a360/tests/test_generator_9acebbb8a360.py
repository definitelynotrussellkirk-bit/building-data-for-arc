"""Regressions for the two-room seed-fill generator."""
from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import sys

import pytest

from puzzle_generators.helpers.selfcheck import (
    components,
    interior_cells,
    is_full_frame_component,
)

TASK_DIR = Path(__file__).resolve().parents[1]
SOURCE = TASK_DIR / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_9acebbb8a360", SOURCE)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _room_markers(grid: list[list[int]]) -> list[int]:
    frames = sorted(
        (
            comp
            for comp in components(grid, colors={5})
            if is_full_frame_component(comp, color=5)
        ),
        key=lambda comp: comp["bbox"],
    )
    markers: list[int] = []
    for frame in frames:
        values = [
            grid[r][c]
            for r, c in interior_cells(frame["bbox"])
            if grid[r][c] not in (0, 5)
        ]
        assert len(values) == 1
        markers.append(values[0])
    return markers


def test_known_regression_uses_distinct_seed_colors():
    grid = GEN.generate(1, 0)
    markers = _room_markers(grid)
    assert len(markers) == 2
    assert len(set(markers)) == 2, markers


def test_self_check_rejects_equal_seed_colors_across_rooms():
    grid = GEN.generate(19, 4)
    frames = sorted(
        (
            comp
            for comp in components(grid, colors={5})
            if is_full_frame_component(comp, color=5)
        ),
        key=lambda comp: comp["bbox"],
    )
    assert len(frames) == 2
    mutated = copy.deepcopy(grid)
    first_marker = _room_markers(mutated)[0]
    second_cells = [
        (r, c)
        for r, c in interior_cells(frames[1]["bbox"])
        if mutated[r][c] not in (0, 5)
    ]
    assert len(second_cells) == 1
    r, c = second_cells[0]
    mutated[r][c] = first_marker
    errors = GEN.self_check(mutated)
    assert any("distinct" in error for error in errors), errors



def test_self_check_accepts_canonical_three_cell_wide_room():
    grid = [[0 for _ in range(10)] for _ in range(9)]
    for r in range(1, 7):
        for c in range(1, 4):
            if r in (1, 6) or c in (1, 3):
                grid[r][c] = 5
    grid[3][2] = 4
    for r in range(2, 6):
        for c in range(5, 9):
            if r in (2, 5) or c in (5, 8):
                grid[r][c] = 5
    grid[3][6] = 7
    assert GEN.self_check(grid) == []

def test_n_frames_override_cannot_silently_change_the_exact_two_room_contract():
    with pytest.raises(ValueError, match="n_frames"):
        GEN.generate(7, 11, n_frames=1)
    with pytest.raises(ValueError, match="n_frames"):
        GEN.generate(7, 11, n_frames=3)


def test_declared_axes_only_advertise_live_non_singleton_knobs():
    assert set(GEN.AXES) == {"grid_h", "grid_w"}
    assert GEN.AXES["grid_h"]["valid"] == "8..13"
    assert GEN.AXES["grid_w"]["valid"] == "10..16"


@pytest.mark.parametrize("height,width", [(8, 10), (13, 16)])
def test_declared_dimension_boundaries_are_accepted_and_observable(height, width):
    grid = GEN.generate(31, 7, grid_h=height, grid_w=width)
    assert (len(grid), len(grid[0])) == (height, width)
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize(
    "override",
    [
        {"palette_kind": "warm"},
        {"palette_size": 4},
        {"position_bias": "two_separated_rooms"},
        {"n_distinct_colors": 2},
        {"density": "sparse"},
        {"texture": "warm"},
    ],
)
def test_stale_or_unknown_overrides_are_rejected(override):
    with pytest.raises(ValueError, match="override|texture"):
        GEN.generate(3, 5, **override)


@pytest.mark.parametrize("texture", GEN.DEGENERATE_TEXTURES)
def test_retained_negative_fixtures_remain_explicitly_available(texture):
    grid = GEN.generate(3, 5, texture=texture)
    assert GEN.self_check(grid), texture


def test_invalid_difficulty_is_rejected():
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(3, 5, difficulty="extreme")


def test_semantic_contract_refutes_identity_and_single_global_color_rivals():
    grid = GEN.generate(1, 0)
    expected = GEN.rule_mirror(grid)
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.SEMANTIC_WITNESSES["nontrivial_room_fill"](grid)
    assert GEN.SEMANTIC_WITNESSES["distinct_room_colors"](grid)
    assert GEN.SEMANTIC_RIVALS["identity"](grid) != expected
    assert GEN.SEMANTIC_RIVALS["single_global_seed_color"](grid) != expected


def test_generated_lesson_is_identifiable_against_declared_rivals():
    pairs = []
    for sample_index in range(3):
        grid = GEN.generate(73, sample_index)
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
    assert GEN.lesson_identifiable(pairs[:2], pairs[2]) == []
