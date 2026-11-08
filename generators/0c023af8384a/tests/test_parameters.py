"""Behavioral tests for the repaired base and proposed composed mirror family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from arcpuzzles import Catalog


HOME = Path(__file__).resolve().parents[1]
GENERATOR = HOME / "generator.py"
PROTOTYPE = HOME / "workspace/parametric/prototype.py"


def load_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def base():
    return load_path("mirror_base_subject", GENERATOR)


@pytest.fixture(scope="module")
def p():
    assert PROTOTYPE.is_file(), "parametric prototype is missing"
    return load_path("mirror_parametric_subject", PROTOTYPE)


def test_exact_size_overrides_take_precedence_over_difficulty(base):
    grid = base.generate(
        0,
        0,
        difficulty="easy",
        grid_h=16,
        grid_w=7,
        marks=2,
        texture="plain",
    )
    assert (len(grid), len(grid[0])) == (16, 7)


def test_even_on_axis_override_is_not_silently_resized(base):
    grid = base.generate(1, 0, grid_h=8, grid_w=7, marks=2, texture="on_axis")
    assert (len(grid), len(grid[0])) == (8, 7)
    # An even board has no self-mirroring row.  The texture therefore places
    # an effective source touching the central seam without changing the pin.
    upper, lower = 3, 4
    assert any(grid[row][c] != 0 for row in (upper, lower) for c in range(7))
    assert base._mirror(grid) != grid


def test_dense_texture_respects_an_exact_marks_pin(base):
    grid = base.generate(2, 0, grid_h=8, grid_w=9, marks=2, texture="dense")
    assert sum(cell != 0 for row in grid for cell in row) == 2


def test_default_program_is_exact_catalog_source(p):
    catalog = Catalog(Path(__file__).resolve().parents[3])
    programs = {
        row["program_solution"]
        for row in catalog.get("0c023af8384a")["variants"]
        if isinstance(row.get("program_solution"), str)
    }
    assert programs == {p.program({"completion": "vertical"})}


def test_inputs_are_setting_independent_and_query_prefix_stable(p):
    canonical = p.generate(17, {"completion": "vertical"}, 3, 4)
    composed = p.generate(17, {"completion": "vertical_then_selected_horizontal"}, 3, 4)
    one = p.generate(17, {"completion": "vertical"}, 3, 1)
    for split in ("train", "test"):
        assert [pair["input"] for pair in canonical[split]] == [pair["input"] for pair in composed[split]]
    assert canonical["train"] != composed["train"]
    assert canonical["train"] == one["train"]
    assert canonical["test"][0] == one["test"][0]


@pytest.mark.parametrize("completion", ["vertical", "vertical_then_selected_horizontal"])
def test_counts_labels_and_distinct_inputs(p, completion):
    episode = p.generate(23, {"completion": completion}, 6, 4)
    assert len(episode["train"]) == 6
    assert len(episode["test"]) == 4
    inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    assert len({p.digest(grid) for grid in inputs}) == 10
    for split in ("train", "test"):
        for pair in episode[split]:
            assert pair["output"] == p.transform(pair["input"], {"completion": completion})


def test_each_demonstration_distinguishes_the_two_programs(p):
    episode = p.generate(31, {"completion": "vertical_then_selected_horizontal"}, 3, 4)
    for pair in episode["train"]:
        assert p.transform(pair["input"], {"completion": "vertical"}) != pair["output"]


def test_fourth_query_is_substantive_30_square(p):
    episode = p.generate(7, {"completion": "vertical"}, 3, 4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    for r0 in (0, 15):
        for c0 in (0, 15):
            assert sum(cell != 0 for row in grid[r0 : r0 + 15] for cell in row[c0 : c0 + 15]) >= 4


@pytest.mark.parametrize(
    "case",
    [
        {"seed": True, "settings": {"completion": "vertical"}, "demos": 3, "queries": 4},
        {"seed": 0, "settings": {"completion": "wrong"}, "demos": 3, "queries": 4},
        {"seed": 0, "settings": {"completion": "vertical"}, "demos": 2, "queries": 4},
        {"seed": 0, "settings": {"completion": "vertical"}, "demos": 3, "queries": 5},
    ],
)
def test_invalid_requests_are_rejected(p, case):
    with pytest.raises(ValueError):
        p.generate(**case)


def test_unknown_base_override_is_rejected(base):
    with pytest.raises(ValueError, match="unknown override"):
        base.generate(0, 0, not_a_real_axis=1)


@pytest.mark.parametrize("height", [8, 9])
def test_single_mark_on_axis_request_stays_exact_and_effective(base, height):
    grid = base.generate(
        13,
        0,
        grid_h=height,
        grid_w=7,
        marks=1,
        texture="on_axis",
    )
    assert (len(grid), len(grid[0])) == (height, 7)
    assert sum(cell != 0 for row in grid for cell in row) == 1
    assert base._mirror(grid) != grid


def test_observed_base_axes_match_returned_grid(base):
    grid = base.generate(19, 0, difficulty="medium", texture="dense")
    observed = base.observe_overrides(grid)
    assert observed["grid_h"] == len(grid)
    assert observed["grid_w"] == len(grid[0])
    assert observed["marks"] == sum(cell != 0 for row in grid for cell in row)
    assert 8 <= observed["marks"] <= 14

@pytest.mark.parametrize(
    ("seed", "sample_index", "difficulty"),
    [(0, 3, "medium"), (1, 0, "easy")],
)
def test_short_exact_height_never_returns_an_identity_lesson(
    base, seed, sample_index, difficulty
):
    grid = base.generate(
        seed,
        sample_index,
        difficulty=difficulty,
        grid_h=5,
    )
    assert len(grid) == 5
    assert base._mirror(grid) != grid

def _fixed_side_completion(p, grid, side):
    intermediate = p.vertical_intermediate(grid)
    h, w = len(intermediate), len(intermediate[0])
    columns = range(0, w // 2) if side == "left" else range((w + 1) // 2, w)
    counts = {
        color: sum(intermediate[r][c] == color for r in range(h) for c in columns)
        for color in range(1, 10)
    }
    selected = min(range(1, 10), key=lambda color: (-counts[color], color))
    out = [row[:] for row in intermediate]
    for r in range(h):
        for c in range(w):
            if intermediate[r][c] == selected:
                out[r][w - 1 - c] = selected
    return out


def test_composed_lessons_defeat_fixed_side_selection_shortcuts(p):
    episode = p.generate(0, {"completion": "vertical_then_selected_horizontal"}, 6, 4)
    sides = set()
    left_matches = []
    right_matches = []
    for pair in episode["train"]:
        grid = pair["input"]
        intermediate = p.vertical_intermediate(grid)
        selected = p.selected_color(intermediate)
        selected_columns = [
            c for row in grid for c, cell in enumerate(row) if cell == selected
        ]
        assert selected_columns
        midpoint = len(grid[0]) / 2
        sides.add("left" if sum(selected_columns) / len(selected_columns) < midpoint else "right")
        left_matches.append(_fixed_side_completion(p, grid, "left") == pair["output"])
        right_matches.append(_fixed_side_completion(p, grid, "right") == pair["output"])

    assert sides == {"left", "right"}
    assert not all(left_matches)
    assert not all(right_matches)


def _original_rank_completion(p, grid, rank):
    counts = {
        color: sum(cell == color for row in grid for cell in row)
        for color in range(1, 10)
    }
    ordered = sorted(range(1, 10), key=lambda color: (-counts[color], color))
    selected = ordered[rank - 1]
    intermediate = p.vertical_intermediate(grid)
    h, w = len(intermediate), len(intermediate[0])
    out = [row[:] for row in intermediate]
    for r in range(h):
        for c in range(w):
            if intermediate[r][c] == selected:
                out[r][w - 1 - c] = selected
    return out


def test_composed_lessons_vary_selected_raw_frequency_rank(p):
    episode = p.generate(0, {"completion": "vertical_then_selected_horizontal"}, 3, 4)
    ranks = set()
    rank_two_matches = []
    rank_three_matches = []
    for pair in episode["train"]:
        grid = pair["input"]
        selected = p.selected_color(p.vertical_intermediate(grid))
        counts = {
            color: sum(cell == color for row in grid for cell in row)
            for color in range(1, 10)
        }
        ordered = sorted(range(1, 10), key=lambda color: (-counts[color], color))
        ranks.add(ordered.index(selected) + 1)
        rank_two_matches.append(_original_rank_completion(p, grid, 2) == pair["output"])
        rank_three_matches.append(_original_rank_completion(p, grid, 3) == pair["output"])

    assert ranks == {2, 3}
    assert not all(rank_two_matches)
    assert not all(rank_three_matches)

