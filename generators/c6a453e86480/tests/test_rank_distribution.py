"""Regressions for canonical support, observable controls and rank teaching."""
import copy
import importlib.util
from collections import deque

import pytest
from reviewer_support import canonical_pairs, find_root


TASK = "c6a453e86480"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("rank_distribution_under_test", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
CANONICAL = canonical_pairs(TASK, root=ROOT)


def components(grid):
    """Independent component census used only by these tests."""
    remaining = {(r, c) for r, row in enumerate(grid) if r
                 for c, value in enumerate(row) if value == 1}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        todo = deque([start])
        cells = {start}
        while todo:
            r, c = todo.popleft()
            for point in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if point in remaining:
                    remaining.remove(point)
                    cells.add(point)
                    todo.append(point)
        result.append(cells)
    return result


@pytest.mark.parametrize("pair", CANONICAL, ids=lambda p: f"{p['split']}-{p['pair_index']}")
def test_accepts_every_canonical_input_including_four_blobs(pair):
    assert GEN.self_check(pair["input"]) == []


def test_rejects_foreign_body_color():
    grid = copy.deepcopy(CANONICAL[0]["input"])
    grid[-1][-1] = 8
    assert GEN.self_check(grid), "a non-legend body color was silently accepted"


@pytest.mark.parametrize("grid", [None, [], [[]], [[0]], [3], [[0, 0], [0]],
                                  [[False]*12 for _ in range(5)],
                                  [[10]*12 for _ in range(5)]])
def test_malformed_grid_returns_reasons_instead_of_raising(grid):
    reasons = GEN.self_check(grid)
    assert isinstance(reasons, list) and reasons


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("count", [3, 4])
def test_blob_count_override_is_observable(band, count):
    grid = GEN.generate(81, 4, difficulty=band, n_blobs=count)
    assert len(components(grid)) == count
    assert len([c for c in grid[0] if c]) == count
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(5, 10), (5, 16), (10, 10), (10, 16)])
def test_exact_dimension_boundaries_work_in_every_band(band, height, width):
    grid = GEN.generate(13, 0, difficulty=band, grid_h=height, grid_w=width,
                        n_blobs=4)
    assert (len(grid), len(grid[0])) == (height, width)
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_row_two_and_canonical_profiles_are_reachable(band):
    grids = [GEN.generate(991, index, difficulty=band) for index in range(40)]
    assert any(1 in g[2] for g in grids), "an unintended second separator blocked row 2"
    profiles = {(len(g), len(g[0]), len({v for row in g for v in row})) for g in grids}
    assert {(5, 13, 5), (5, 14, 6), (6, 13, 5)} <= profiles


@pytest.mark.parametrize("kind", ["default", "warm", "cool", "varied"])
def test_palette_controls_and_texture_alias_affect_real_legend_colors(kind):
    for count in (3, 4):
        a = GEN.generate(57, 0, palette_kind=kind, n_blobs=count)
        b = GEN.generate(57, 0, texture=kind, n_blobs=count)
        assert a == b
        colors = {v for v in a[0] if v}
        if kind == "warm":
            assert colors <= {2, 4, 6, 9}
        elif kind == "cool":
            assert colors <= {3, 5, 7, 8}
        elif kind == "default":
            assert {2, 3} <= colors
        else:
            assert colors & {2, 4, 6, 9} and colors & {3, 5, 7, 8}
            assert not {2, 3} <= colors
        observed = GEN.observe_overrides(a)
        assert observed["palette_kind"] == kind
        assert observed["texture"] == kind


@pytest.mark.parametrize("overrides", [{"unknown_axis": 3}, {"n_blobs": 2},
                                      {"n_blobs": 3.5}, {"n_blobs": True},
                                      {"grid_h": "5"}, {"grid_w": 17},
                                      {"palette_kind": "purple"},
                                      {"texture": "no_legend"},
                                      {"palette_kind": "warm", "texture": "cool"}])
def test_invalid_or_conflicting_controls_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(7, 0, **overrides)


def test_canonical_shortcuts_fit_all_actual_canonical_labels():
    rivals = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert rivals, "no executable canonical-compatible rivals were retained"
    for name, rival in rivals.items():
        for pair in CANONICAL:
            original = copy.deepcopy(pair["input"])
            assert rival(original) == pair["output"], name
            assert original == pair["input"], f"{name} mutates its input"


def test_bottom_row_shortcut_is_explicitly_challenged():
    rival = getattr(GEN, "LESSON_COMPETITORS", {}).get("bottom_row_column")
    assert callable(rival), "bottom-row rank can fit three demos yet change the query"
    for band in ("easy", "medium", "hard"):
        refutations = 0
        for index in range(8, 12):
            grid = GEN.generate(12, index, difficulty=band)
            ordered = sorted(components(grid), key=lambda cells: min(c for r, c in cells))
            colors = [v for v in grid[0] if v]
            prediction = rival(grid)
            refutations += any(prediction[r][c] != colors[rank]
                               for rank, cells in enumerate(ordered) for r, c in cells)
        assert refutations >= 2


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_four_pair_window_keeps_a_refutation_after_any_query_holdout(band):
    rivals = getattr(GEN, "LESSON_COMPETITORS", {})
    assert rivals, "lesson competitors are absent"
    for start in range(4):
        grids = [GEN.generate(2026, index, difficulty=band)
                 for index in range(start, start+4)]
        for name, rival in rivals.items():
            refutations = []
            for grid in grids:
                # Compare recoloring to hand-interpreted component ranks; no
                # implementation oracle is reused to calculate this expectation.
                ordered = sorted(components(grid), key=lambda cells: min(c for r, c in cells))
                colors = [v for v in grid[0] if v]
                predicted = rival(copy.deepcopy(grid))
                refutations.append(any(predicted[r][c] != colors[rank]
                                       for rank, cells in enumerate(ordered) for r, c in cells))
            assert sum(refutations) >= 2, (start, name, refutations)


def test_generation_is_deterministic_and_returns_independent_grids():
    grid = GEN.generate(342, 3, difficulty="hard")
    before = copy.deepcopy(grid)
    other = GEN.generate(342, 3, difficulty="hard")
    assert other == before
    grid[0][0] = 99
    assert other == before
