from __future__ import annotations

from copy import deepcopy
import importlib
from typing import Iterable

import pytest

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module("puzzle_generators.per_puzzle.8cfb4420a8f1.generator")
ROOT = find_root(__file__)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed(bad_seed: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index(bad_index: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, bad_index, difficulty="easy")


@pytest.mark.parametrize(
    ("axis", "bad_value"),
    [
        (axis, value)
        for axis, control in (
            ("grid_h", 5),
            ("grid_w", 8),
            ("marker_color", 1),
            ("marked_cells", 1),
            ("primary_distractor_count", 2),
            ("n_distinct_colors", 3),
        )
        for value in (True, False, float(control), control + 0.75, str(control))
    ],
)
def test_integer_axis_overrides_reject_scalar_coercions(
    axis: str, bad_value: object
) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, 0, difficulty="easy", **{axis: bad_value})


def _same_colour_component(
    grid: list[list[int]], cells: Iterable[tuple[int, int]]
) -> set[tuple[int, int]]:
    cells = set(cells)
    start = min(cells)
    colour = grid[start[0]][start[1]]
    reached = {start}
    pending = [start]
    while pending:
        r, c = pending.pop()
        for neighbour in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbour in cells and neighbour not in reached:
                nr, nc = neighbour
                assert grid[nr][nc] == colour
                reached.add(neighbour)
                pending.append(neighbour)
    return reached


def test_default_distractor_colours_are_single_connected_objects() -> None:
    """Generated texture should match the canonical connected-object idiom."""
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(16):
            grid = gen.generate(
                24000 + 100 * band_index + sample_index,
                sample_index,
                difficulty=band,
            )
            marker_colour = next(value for value in grid[0] if value != 0)
            distractor_colours = {
                value
                for row in grid[1:]
                for value in row
                if value not in (0, marker_colour)
            }
            assert distractor_colours
            for colour in distractor_colours:
                cells = {
                    (r, c)
                    for r, row in enumerate(grid[1:], start=1)
                    for c, value in enumerate(row)
                    if value == colour
                }
                assert _same_colour_component(grid, cells) == cells, (
                    band,
                    sample_index,
                    colour,
                    grid,
                )


def test_declared_canonical_shortcuts_fit_every_canonical_pair() -> None:
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True)
    assert gen.CANONICAL_SHORTCUTS
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert shortcut(deepcopy(pair["input"])) == pair["output"], name


def test_first_body_colour_shortcut_is_explicitly_taught_against() -> None:
    name = "erase_first_nonzero_body_colour"
    shortcut = gen.CANONICAL_SHORTCUTS[name]
    assert name in gen.SEMANTIC_RIVALS
    assert name in gen.LESSON_COMPETITORS
    assert any(name in rivals for rivals in gen.WITNESS_RIVALS.values())

    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [
            gen.generate(28000 + band_index * 100 + i, i, difficulty=band)
            for i in range(12)
        ]
        assert all(shortcut(grid) != gen.rule_mirror(grid) for grid in grids)


def test_retained_baseline_texture_counterexample_is_reproduced_and_repaired() -> None:
    import json

    path = (
        ROOT
        / "generators"
        / gen.TASK_ID
        / "counterexamples"
        / "baseline_disconnected_distractor.json"
    )
    case = json.loads(path.read_text(encoding="utf-8"))
    grid = case["input"]
    colour = case["distractor_colour"]
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == colour
    }
    assert cells == {tuple(cell) for cell in case["distractor_cells"]}
    assert _same_colour_component(grid, cells) != cells

    repaired = gen.generate(
        case["reproducer"]["seed"],
        case["reproducer"]["sample_index"],
        difficulty=case["reproducer"]["difficulty"],
    )
    repaired_colour = next(
        value
        for row in repaired[1:]
        for value in row
        if value not in (0, next(v for v in repaired[0] if v != 0))
    )
    repaired_cells = {
        (r, c)
        for r, row in enumerate(repaired)
        for c, value in enumerate(row)
        if value == repaired_colour
    }
    assert _same_colour_component(repaired, repaired_cells) == repaired_cells
