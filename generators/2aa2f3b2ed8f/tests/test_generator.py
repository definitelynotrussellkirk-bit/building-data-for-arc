"""Portable regressions for the tailed-rectangle slide generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "2aa2f3b2ed8f"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    candidate = os.environ.get("GENERATOR_UNDER_TEST")
    path = Path(candidate) if candidate else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
CANONICAL_PROFILES = {
    (
        len(pair["input"]),
        len(pair["input"][0]),
        len({value for row in pair["input"] for value in row}),
    )
    for pair in PAIRS
}


def _bbox(cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _components_by_color(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = set()
            while stack:
                current = stack.pop()
                cells.add(current)
                r, c = current
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components


def _is_rectangle(cells):
    r1, c1, r2, c2 = _bbox(cells)
    return len(cells) == (r2 - r1 + 1) * (c2 - c1 + 1)


def _largest_rectangle(cells):
    """Independent brute-force reconstruction used only by tests."""
    r1, c1, r2, c2 = _bbox(cells)
    best = None
    for top in range(r1, r2 + 1):
        for bottom in range(top, r2 + 1):
            for left in range(c1, c2 + 1):
                for right in range(left, c2 + 1):
                    rectangle = {
                        (row, col)
                        for row in range(top, bottom + 1)
                        for col in range(left, right + 1)
                    }
                    if rectangle <= cells and (best is None or len(rectangle) > len(best)):
                        best = rectangle
    assert best
    return best


def _oracle(grid):
    """Independent Python implementation of the selected Racket rule."""
    components = _components_by_color(grid)
    rectangles = [(color, cells) for color, cells in components if _is_rectangle(cells)]
    movers = [(color, cells) for color, cells in components if not _is_rectangle(cells)]
    assert len(rectangles) == len(movers) == 1
    _, target = rectangles[0]
    moving_color, moving = movers[0]
    body = _largest_rectangle(moving)
    tail = moving - body
    assert tail

    br1, bc1, br2, bc2 = _bbox(body)
    tr1, tc1, tr2, tc2 = _bbox(target)
    if all(row < br1 for row, _ in tail):
        dr, dc, steps = -1, 0, br1 - tr2 - 1
    elif all(row > br2 for row, _ in tail):
        dr, dc, steps = 1, 0, tr1 - br2 - 1
    elif all(col < bc1 for _, col in tail):
        dr, dc, steps = 0, -1, bc1 - tc2 - 1
    else:
        assert all(col > bc2 for _, col in tail)
        dr, dc, steps = 0, 1, tc1 - bc2 - 1
    assert steps > 0

    output = deepcopy(grid)
    for row, col in moving:
        output[row][col] = 0
    for row, col in body:
        output[row + dr * steps][col + dc * steps] = moving_color
    return output


def _profile(grid):
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def test_metadata_exposes_only_constructive_observable_axes():
    assert gen.GENERATOR_ID == gen.TASK_ID == TASK_ID
    assert gen.RULE_HASH == "f1cfb51e6ad7"
    assert set(gen.AXES) == {"orientation", "body_shape", "target_shape", "tail_length"}
    assert tuple(gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}-{p['pair_index']}")
def test_canonical_inputs_are_owned_and_labels_match_independent_oracle(pair):
    frozen = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert _oracle(pair["input"]) == pair["output"]
    assert pair["input"] == frozen


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_constructive_and_observable_in_every_band(band):
    requested = {
        "orientation": "down",
        "body_shape": "3x4",
        "target_shape": "7x7",
        "tail_length": 5,
    }
    grid = gen.generate(1701, 29, difficulty=band, **requested)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
    assert gen.observe_overrides(grid) == requested
    assert _oracle(grid) != grid


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"orientation": "diagonal"},
        {"body_shape": "9x9"},
        {"target_shape": "1x1"},
        {"tail_length": 0},
        {"tail_length": 7},
        {"tail_length": True},
        {"tail_length": "3"},
        {"palette_kind": "warm"},
        {"anchor_corner": True},
        {"texture": "no_tail"},
    ],
)
def test_invalid_unknown_and_retired_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize("bad_index", [True, False, -1, 1.5, "1"])
def test_sample_index_must_be_a_nonnegative_plain_integer(bad_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.generate(0, bad_index)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_hits_canonical_profiles_and_all_directions(band):
    grids = [gen.generate(8100 + index, index, difficulty=band) for index in range(24)]
    assert all(gen.self_check(grid, difficulty=band) == [] for grid in grids)
    assert any(_profile(grid) in CANONICAL_PROFILES for grid in grids)
    assert {gen.observe_overrides(grid)["orientation"] for grid in grids} == {
        "right", "left", "down", "up"
    }


def test_generated_tail_bridges_the_gap_and_reference_oracle_changes_only_mover():
    for index in range(32):
        grid = gen.generate(9200 + index, index, difficulty="hard")
        observed = gen.observe_overrides(grid)
        assert 1 <= observed["tail_length"] <= 6
        expected = _oracle(grid)
        assert expected != grid
        before_colors = {v for row in grid for v in row}
        after_colors = {v for row in expected for v in row}
        assert before_colors == after_colors


def test_semantic_witness_refutes_declared_one_step_rival():
    assert gen.SEMANTIC_WITNESSES
    assert gen.SEMANTIC_RIVALS
    for index in range(16):
        grid = gen.generate(10300, index)
        if gen.SEMANTIC_WITNESSES["long_tail_requires_full_slide"](grid):
            assert gen.SEMANTIC_RIVALS["slide_one_cell"](grid) != _oracle(grid)
            return
    pytest.fail("default schedule produced no long-tail witness")


def test_generation_is_deterministic_and_returns_independent_rows():
    first = gen.generate(73, 11, difficulty="medium")
    second = gen.generate(73, 11, difficulty="medium")
    assert first == second
    assert len({id(row) for row in first}) == len(first)
    first[0][0] = 9 if first[0][0] != 9 else 1
    assert first != second
