"""Task-local regression tests for 2c83e8cd1c07."""
from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

TASK_ID = "2c83e8cd1c07"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    source = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _path(a, b):
    (r1, c1), (r2, c2) = a, b
    dr = (r2 > r1) - (r2 < r1)
    dc = (c2 > c1) - (c2 < c1)
    return [(r1 + i * dr, c1 + i * dc) for i in range(abs(r2 - r1) + 1)]


def _analyze(grid):
    by_color = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                by_color[value].append((r, c))
    fillable = []
    blocked = []
    for color, cells in sorted(by_color.items()):
        if len(cells) != 2:
            continue
        a, b = cells
        if a[0] == b[0] or abs(a[0] - b[0]) != abs(a[1] - b[1]):
            continue
        record = (color, a, b, _path(a, b))
        if all(grid[r][c] == 0 for r, c in record[3][1:-1]):
            fillable.append(record)
        else:
            blocked.append(record)
    return by_color, fillable, blocked


def _reference(grid, *, ignore_blockers=False):
    """Independent Python reading-order mirror of the selected Racket rule."""
    out = deepcopy(grid)
    colors = []
    for row in grid:
        for value in row:
            if value and value not in colors:
                colors.append(value)
    for color in colors:
        cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        if len(cells) != 2:
            continue
        a, b = cells
        if a[0] == b[0] or abs(a[0] - b[0]) != abs(a[1] - b[1]):
            continue
        path = _path(a, b)
        if ignore_blockers or all(grid[r][c] == 0 for r, c in path[1:-1]):
            for r, c in path:
                out[r][c] = color
    return out


def test_rule_hash_pins_selected_authority():
    assert getattr(gen, "RULE_HASH", None) == "177b2df2b99a"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_extreme_overrides_construct_and_are_observable(band):
    for requested in (
        {"grid_h": 7, "grid_w": 7, "segments": 1},
        {"grid_h": 7, "grid_w": 7, "segments": 5},
        {"grid_h": 14, "grid_w": 14, "segments": 5},
    ):
        grid = gen.generate(17, 9, difficulty=band, **requested)
        assert gen.self_check(grid, difficulty=band, meta={"overrides": requested}) == []
        assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"grid_h": 6},
        {"grid_h": 15},
        {"grid_w": True},
        {"grid_w": 8.5},
        {"segments": 0},
        {"segments": 6},
        {"segments": "2"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_production_draw_contains_exactly_one_blocked_counterexample(band):
    for index in range(48):
        grid = gen.generate(700 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        by_color, fillable, blocked = _analyze(grid)
        assert 1 <= len(fillable) <= 5
        assert len(blocked) == 1
        assert all(len(cells) == 2 for cells in by_color.values())
        blocker_cells = [(r, c) for r, c in blocked[0][3][1:-1] if grid[r][c] != 0]
        assert len(blocker_cells) == 1
        assert any(blocker_cells[0] in (record[1], record[2]) for record in fillable)
        assert _reference(grid) != _reference(grid, ignore_blockers=True)


def test_declared_rival_fits_canonical_pairs_but_is_refuted_by_generated_witness():
    from reviewer_support import canonical_pairs, find_root

    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert pairs
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert _reference(pair["input"]) == pair["output"]
        assert _reference(pair["input"], ignore_blockers=True) == pair["output"]

    witness = gen.generate(91, 4, grid_h=7, grid_w=7, segments=1)
    canonical = _reference(witness)
    rival = _reference(witness, ignore_blockers=True)
    assert canonical != rival
    assert gen.SEMANTIC_WITNESSES["blocked_diagonal"](witness)
    assert gen.SEMANTIC_RIVALS["ignore_interior_blocker"](witness) == rival
    assert gen.CANONICAL_SHORTCUTS["ignore_interior_blocker"](witness) == rival
    assert gen.LESSON_COMPETITORS["ignore_interior_blocker"](witness) == rival


def test_every_three_demo_window_refutes_the_canonical_shortcut():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = [gen.generate(917263, start + offset, difficulty=band) for offset in range(3)]
            assert all(_reference(grid) != _reference(grid, ignore_blockers=True) for grid in demos)


def test_default_schedule_covers_canonical_size_palette_profiles_in_every_band():
    canonical_profiles = {(7, 7, 3), (8, 8, 3), (8, 9, 3)}
    for band in ("easy", "medium", "hard"):
        seen = set()
        segment_counts = set()
        for index in range(36):
            grid = gen.generate(3100, index, difficulty=band)
            assert grid == gen.generate(3100, index, difficulty=band)
            assert gen.self_check(grid) == []
            palette_size = len({value for row in grid for value in row})
            seen.add((len(grid), len(grid[0]), palette_size))
            segment_counts.add(gen.observe_overrides(grid)["segments"])
        assert seen & canonical_profiles
        assert 1 in segment_counts
        assert max(segment_counts) >= {"easy": 2, "medium": 3, "hard": 5}[band]


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0, 0], [0]],
        [[0, 11], [0, 0]],
        [[1, 0], [0, 0]],
        [[1, 1], [0, 0]],
    ],
)
def test_self_check_rejects_malformed_or_semantically_empty_inputs(grid):
    assert gen.self_check(grid)


def test_self_check_detects_destructive_mutations():
    grid = gen.generate(31, 8, grid_h=8, grid_w=9, segments=3)
    assert gen.self_check(grid) == []

    extra = deepcopy(grid)
    extra[6][6] = next(value for row in grid for value in row if value)
    assert gen.self_check(extra)

    erased = deepcopy(grid)
    for r, row in enumerate(erased):
        for c, value in enumerate(row):
            if value:
                erased[r][c] = 0
                break
        else:
            continue
        break
    assert gen.self_check(erased)
