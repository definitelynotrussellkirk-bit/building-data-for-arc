"""Independent regressions for third-red corners and attached red endpoints."""
from __future__ import annotations

import copy
import importlib.util

import pytest
from reviewer_support import canonical_pairs, find_root


TASK = "249b59452da6"
ROOT = find_root(__file__)
HOME = next(path for path in (
    ROOT / "generators" / TASK,
    ROOT / "puzzle_generators" / "per_puzzle" / TASK,
) if (path / "generator.py").is_file())
SPEC = importlib.util.spec_from_file_location("reviewed_e82_motifs", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
PAIRS = canonical_pairs(TASK, root=ROOT)
SHAPES = sorted({(9, 9)} | {(len(p["input"]), len(p["input"][0])) for p in PAIRS})


def red_diagonals(grid):
    """Enumerate neighboring red-cell pairs and their other two corners."""
    red = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2}
    for r, c in sorted(red):
        for dc in (-1, 1):
            other = (r + 1, c + dc)
            if other in red:
                yield ((r, c), other), ((r, c + dc), (r + 1, c))


def eligible(grid):
    return [(ends, corners) for ends, corners in red_diagonals(grid)
            if all(grid[r][c] == 0 for r, c in corners)]


def painted_copy(grid, cells):
    out = copy.deepcopy(grid)
    for r, c in cells:
        out[r][c] = 3
    return out


def exact_rule(grid):
    # Inspect the original grid before applying the union of all local edits.
    return painted_copy(grid, {p for _, corners in eligible(grid) for p in corners})


def allow_third_red(grid):
    cells = {p for _, corners in red_diagonals(grid)
             if all(grid[r][c] in (0, 2) for r, c in corners)
             for p in corners if grid[p[0]][p[1]] == 0}
    return painted_copy(grid, cells)


def reject_attached_endpoint(grid):
    red = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2}
    cells = set()
    for ends, corners in eligible(grid):
        if not any((r + dr, c + dc) in red for r, c in ends
                   for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            cells.update(corners)
    return painted_copy(grid, cells)


RIVALS = (allow_third_red, reject_attached_endpoint)


@pytest.mark.parametrize("grid,expected,disagrees", [
    ([[2, 2], [0, 2]], [[2, 2], [0, 2]], [True, False]),
    ([[2, 2, 0], [0, 0, 2]], [[2, 2, 3], [0, 3, 2]], [False, True]),
    ([[2, 6], [0, 2]], [[2, 6], [0, 2]], [False, False]),
])
def test_independent_rules_have_the_stated_local_behavior(grid, expected, disagrees):
    original = copy.deepcopy(grid)
    assert exact_rule(grid) == expected
    assert [rival(grid) != expected for rival in RIVALS] == disagrees
    assert grid == original


def test_both_independent_rivals_fit_all_five_canonical_pairs():
    assert len(PAIRS) == 5
    for pair in PAIRS:
        original = copy.deepcopy(pair["input"])
        for rule in (exact_rule, *RIVALS):
            assert rule(pair["input"]) == pair["output"], rule.__name__
            assert pair["input"] == original, rule.__name__


def assert_full_teaching_grid(grid, requested):
    original = copy.deepcopy(grid)
    h, w = len(grid), len(grid[0])
    assert 9 <= h <= 18 and 9 <= w <= 18
    assert all(len(row) == w for row in grid)
    assert all(type(v) is int and 0 <= v <= 9 for row in grid for v in row)
    assert sum(v == 0 for row in grid for v in row) * 2 >= h * w
    windows = eligible(grid)
    observed = {"grid_h": h, "grid_w": w, "n_pairs": len(windows),
                "palette_size": len({v for row in grid for v in row})}
    assert 2 <= observed["n_pairs"] <= 8 and 3 <= observed["palette_size"] <= 5
    assert all(observed[key] == value for key, value in requested.items()), observed
    assert GEN.self_check(grid) == []
    truth = exact_rule(grid)
    assert grid == original
    assert truth != grid
    assert all(truth[r][c] == v or (v == 0 and truth[r][c] == 3)
               for r, row in enumerate(grid) for c, v in enumerate(row))
    survivors = []
    for rival in RIVALS:
        if rival(grid) == truth:
            survivors.append(rival.__name__)
        assert grid == original, rival.__name__
    assert not survivors, f"missing decisive motifs for {survivors}"


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [0, 5])
@pytest.mark.parametrize("sample_index", range(5))
def test_default_draws_refute_both_new_shortcuts(band, seed, sample_index):
    grid = GEN.generate(seed, sample_index, difficulty=band)
    assert_full_teaching_grid(grid, {})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("seed", [0, 5])
@pytest.mark.parametrize("shape", SHAPES)
@pytest.mark.parametrize("palette", [3, 4, 5])
@pytest.mark.parametrize("count", [2, 3, 4, 8])
def test_full_teaching_overrides_keep_exact_controls_and_both_motifs(band, seed, shape, palette, count):
    requested = dict(grid_h=shape[0], grid_w=shape[1], n_pairs=count, palette_size=palette)
    grid = GEN.generate(seed, 0, difficulty=band, **requested)
    assert_full_teaching_grid(grid, requested)
