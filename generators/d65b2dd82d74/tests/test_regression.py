"""Pixel-derived regressions for disjoint pairing of exact-span vertical bars.

No output solver mirror is used as a Racket oracle. The component parser below
only measures the input domain and the counts promised by generation axes.
"""
from collections import defaultdict
from copy import deepcopy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "d65b2dd82d74"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
BANDS = ("easy", "medium", "hard")
COUNT_COMBINATIONS = [(n, k) for n in range(1, 5) for k in range(1, n + 1)]


def _bar_groups(grid):
    """Independent same-color 4CC, grouped by color and exact endpoint rows."""
    assert grid and grid[0]
    h, w = len(grid), len(grid[0])
    assert all(len(row) == w for row in grid)
    assert all(type(v) is int and 0 <= v <= 9 for row in grid for v in row)
    seen, groups = set(), defaultdict(list)
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color, todo, cells = grid[r][c], [(r, c)], []
            seen.add((r, c))
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            rows, cols = {rr for rr, _ in cells}, {cc for _, cc in cells}
            assert len(cols) == 1 and len(rows) >= 2, (color, cells)
            r0, r1 = min(rows), max(rows)
            assert len(rows) == r1 - r0 + 1, (color, cells)
            groups[(color, r0, r1)].append(next(iter(cols)))
    for columns in groups.values():
        columns.sort()
    return dict(groups)


def _measure(grid):
    groups = _bar_groups(grid)
    fills, pair_count = {}, 0
    for (color, r0, r1), columns in groups.items():
        for left, right in zip(columns[::2], columns[1::2]):
            assert right - left >= 2, (color, columns)
            pair_count += 1
            for r in range(r0, r1 + 1):
                for c in range(left, right + 1):
                    assert grid[r][c] in (0, color), (r, c, grid[r][c], color)
                    assert fills.get((r, c), color) == color, (r, c)
                    fills[(r, c)] = color
    assert pair_count >= 1
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "n_pairs": pair_count,
            "n_distinct_colors": len({key[0] for key in groups})}, groups


def _bars(h, w, specifications):
    grid = [[0] * w for _ in range(h)]
    for color, r0, r1, columns in specifications:
        for r in range(r0, r1 + 1):
            for c in columns:
                grid[r][c] = color
    return grid


def test_axis_contract_has_only_honest_integer_controls():
    expected = {"grid_h": "6..20", "grid_w": "9..24", "n_pairs": "1..4",
                "n_distinct_colors": "1..4", "palette_size": "1..4"}
    assert set(GEN.AXES) == set(expected)
    for axis, bounds in expected.items():
        assert GEN.AXES[axis]["type"] == "int"
        assert GEN.AXES[axis]["valid"] == bounds
    assert GEN.EXAMPLES_NEEDED == 5
    assert GEN.LESSON_SCHEDULE_PERIOD == 3


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("dimensions", [(6, 9), (20, 24)])
@pytest.mark.parametrize("counts", COUNT_COMBINATIONS)
def test_every_feasible_count_combination_is_realized_at_size_boundaries(band, dimensions, counts):
    n, k = counts
    h, w = dimensions
    # Both supported spellings must control pixels, including n_pairs=3 and 4.
    color_axis = "palette_size" if n % 2 == 0 else "n_distinct_colors"
    overrides = {"grid_h": h, "grid_w": w, "n_pairs": n, color_axis: k}
    grid = GEN.generate(20261011, n * 4 + k, difficulty=band, **overrides)
    measured, _ = _measure(grid)
    assert measured == {"grid_h": h, "grid_w": w, "n_pairs": n, "n_distinct_colors": k}
    assert GEN.self_check(grid, difficulty=band) == []


def test_all_canonical_inputs_and_retained_four_bar_witness_are_accepted():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    inputs = [pair["input"] for pair in pairs]
    # Exact retained audit input; no dependency on another task's audit files.
    witness = _bars(7, 12, [(4, 2, 4, [1, 3, 7, 9])])
    measured, groups = _measure(witness)
    assert measured["n_pairs"] == 2 and list(groups.values()) == [[1, 3, 7, 9]]
    for grid in inputs + [witness]:
        original = deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert grid == original, "self_check must not mutate input"


def test_odd_trailing_bar_and_unpaired_mismatched_span_bars_are_accepted():
    grid = _bars(9, 13, [(4, 1, 3, [0, 2, 5, 7, 10]),
                         (2, 5, 6, [1]), (2, 6, 8, [8])])
    measured, groups = _measure(grid)
    assert measured["n_pairs"] == 2
    assert len(groups[(4, 1, 3)]) == 5
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("grid", [
    None, [], [[]], [[0, 0], [0]], [[True, 0]], [[1.0, 0]],
    [["1", 0]], [[-1, 0]], [[10, 0]],
])
def test_malformed_grids_return_validation_messages(grid):
    errors = GEN.self_check(grid)
    assert isinstance(errors, list) and errors


def test_row_holes_nonbar_objects_and_fill_conflicts_are_rejected():
    valid = _bars(7, 12, [(4, 1, 4, [1, 5])])
    hole = deepcopy(valid)
    hole[2][1] = hole[2][5] = 0
    horizontal = deepcopy(valid)
    horizontal[6][8:10] = [2, 2]
    singleton = deepcopy(valid)
    singleton[6][9] = 2
    conflict = _bars(7, 12, [(4, 1, 4, [1, 7]), (2, 2, 3, [3, 5])])
    for grid in (hole, horizontal, singleton, conflict, [[0] * 9 for _ in range(6)]):
        assert GEN.self_check(grid), grid


def test_invalid_seed_and_index_types_and_negative_index_are_rejected():
    for seed in (True, 1.0, "1", None):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(seed, 0)
    for index in (True, 1.0, "1", None, -1):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, index)


def test_unknown_and_removed_axes_fail_loudly():
    for axis, value in {"palette_kind": "warm", "texture": "varied",
                        "density": "sparse", "position_bias": "parallel_vertical_bars",
                        "unknown_axis": 1}.items():
        with pytest.raises((TypeError, ValueError), match="(?i)unknown|unsupported|unexpected"):
            GEN.generate(1, 0, **{axis: value})


def test_bad_integer_axis_values_are_rejected_instead_of_coerced():
    bounds = {"grid_h": (6, 20), "grid_w": (9, 24), "n_pairs": (1, 4),
              "n_distinct_colors": (1, 4), "palette_size": (1, 4)}
    for axis, (low, high) in bounds.items():
        for value in (low - 1, high + 1, True, float(low), str(low), None):
            with pytest.raises((TypeError, ValueError)):
                GEN.generate(1, 0, **{axis: value})


def test_contradictory_color_aliases_and_more_colors_than_pairs_are_rejected():
    for overrides in ({"n_pairs": 3, "n_distinct_colors": 2, "palette_size": 3},
                      {"n_pairs": 1, "n_distinct_colors": 2},
                      {"n_pairs": 2, "palette_size": 4}):
        with pytest.raises(ValueError, match="incompatible_axes"):
            GEN.generate(1, 0, **overrides)
    grid = GEN.generate(1, 0, n_pairs=4, n_distinct_colors=3, palette_size=3)
    measured, _ = _measure(grid)
    assert measured["n_pairs"] == 4 and measured["n_distinct_colors"] == 3


@pytest.mark.parametrize("band", BANDS)
def test_even_profile_contains_pair_and_unequal_span_unmatched_bar_of_same_color(band):
    for index in (1, 4, 7, 10):
        grid = GEN.generate(20261011, index, difficulty=band)
        _, groups = _measure(grid)
        paired_keys = [key for key, columns in groups.items() if len(columns) >= 2]
        unmatched_keys = [key for key, columns in groups.items() if len(columns) % 2]
        assert any(paired[0] == unmatched[0] and paired[1:] != unmatched[1:]
                   for paired in paired_keys for unmatched in unmatched_keys), groups


def test_declared_mixed_span_rejection_rival_fits_all_canonical_labels():
    rival = GEN.CANONICAL_SHORTCUTS.get("reject_color_with_mixed_spans")
    assert callable(rival), "declare the canonical-fitting mixed-span rejection rival"
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert rival(original) == pair["output"]
        assert original == pair["input"], "rival must not mutate its input"


@pytest.mark.parametrize("band", BANDS)
def test_default_support_contains_multi_pair_odd_and_mismatched_span_groups(band):
    seen_multi = seen_odd = seen_mismatched = False
    for index in range(20):
        grid = GEN.generate(20261011, index, difficulty=band)
        measured, groups = _measure(grid)
        assert GEN.self_check(grid, difficulty=band) == []
        assert measured["n_pairs"] == (2 if index % 3 == 0 else 3)
        assert measured["n_distinct_colors"] == 2
        seen_multi |= any(len(columns) >= 4 for columns in groups.values())
        seen_odd |= any(len(columns) >= 3 and len(columns) % 2 for columns in groups.values())
        spans_by_color = defaultdict(set)
        for color, r0, r1 in groups:
            spans_by_color[color].add((r0, r1))
        seen_mismatched |= any(len(spans) >= 2 for spans in spans_by_color.values())
    assert seen_multi and seen_odd and seen_mismatched


def test_determinism_global_rng_independence_and_mutability_isolation():
    state = random.getstate()
    first = GEN.generate(17, 5, difficulty="hard")
    original = deepcopy(first)
    GEN.generate(99, 2, difficulty="easy", n_pairs=4, palette_size=1)
    replay = GEN.generate(17, 5, difficulty="hard")
    assert replay == original and replay is not first
    assert all(a is not b for a, b in zip(first, replay))
    assert len({id(row) for row in first}) == len(first)
    first[0][0] = (first[0][0] + 1) % 10
    assert GEN.generate(17, 5, difficulty="hard") == original
    assert random.getstate() == state
