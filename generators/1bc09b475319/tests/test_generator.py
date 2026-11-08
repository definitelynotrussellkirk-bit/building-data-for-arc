"""Regression tests for the Bar Caps generator repair."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "1bc09b475319"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def intended_rule(grid):
    """Independent Python transcription of the selected Racket authority."""
    h = len(grid)
    w = len(grid[0])
    out = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 0:
                continue
            right = c + 2 < w and grid[r][c + 1] == grid[r][c + 2] == 6
            left = c - 2 >= 0 and grid[r][c - 1] == grid[r][c - 2] == 6
            if left or right:
                out[r][c] = 8
    return out


def adjacent_any_six(grid):
    """Canonical-fitting shortcut: cap every horizontally adjacent 6."""
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value == 0 and (
                (c > 0 and row[c - 1] == 6)
                or (c + 1 < len(row) and row[c + 1] == 6)
            ):
                out[r][c] = 8
    return out


def cap_runs_matching(grid, predicate):
    out = [row[:] for row in grid]
    for r, start, end in row_runs(grid):
        length = end - start + 1
        if length < 2 or not predicate(r, start, end, length, len(grid[0])):
            continue
        if start > 0 and grid[r][start - 1] == 0:
            out[r][start - 1] = 8
        if end + 1 < len(grid[0]) and grid[r][end + 1] == 0:
            out[r][end + 1] = 8
    return out


def canonical_lengths_only(grid):
    """Shortcut that caps only canonical-observed lengths 2 and 3."""
    return cap_runs_matching(grid, lambda _r, _s, _e, length, _w: length in (2, 3))


def interior_bars_only(grid):
    """Shortcut that ignores bars touching either horizontal boundary."""
    return cap_runs_matching(grid, lambda _r, start, end, _length, width: start > 0 and end < width - 1)


def row_runs(grid):
    runs = []
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            if row[c] != 6:
                c += 1
                continue
            start = c
            while c < len(row) and row[c] == 6:
                c += 1
            runs.append((r, start, c - 1))
    return runs


def labeled_pair(grid):
    return {"input": grid, "output": intended_rule(grid)}


def test_rule_pin_and_small_truthful_axis_contract():
    assert getattr(GEN, "RULE_HASH", None) == "187795461399"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "n_bars",
        "bar_length",
        "edge_bar",
        "singleton_layout",
    }
    assert callable(getattr(GEN, "observe_overrides", None))


def test_canonical_pairs_are_owned_and_the_shortcut_really_fits_them():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert intended_rule(pair["input"]) == pair["output"]
        assert adjacent_any_six(pair["input"]) == pair["output"]
        assert canonical_lengths_only(pair["input"]) == pair["output"]
        for name, rival in GEN.CANONICAL_SHORTCUTS.items():
            assert rival(pair["input"]) == pair["output"], name
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", [7, 18])
@pytest.mark.parametrize("grid_w", [7, 20])
@pytest.mark.parametrize("n_bars", [3, 4])
@pytest.mark.parametrize("bar_length", [2, 5])
@pytest.mark.parametrize("edge_bar", [False, True])
@pytest.mark.parametrize("singleton_layout", ["separate", "vertical"])
def test_every_boundary_override_combination_is_constructive_and_observable(
    band, grid_h, grid_w, n_bars, bar_length, edge_bar, singleton_layout
):
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_bars": n_bars,
        "bar_length": bar_length,
        "edge_bar": edge_bar,
        "singleton_layout": singleton_layout,
    }
    grid = GEN.generate(371, 19, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert intended_rule(grid) != grid
    bars = [run for run in row_runs(grid) if run[2] > run[1]]
    lengths = {end - start + 1 for _row, start, end in bars}
    assert requested["bar_length"] == bars[0][2] - bars[0][1] + 1
    assert len(lengths) >= 2
    assert any(length in (2, 3) for length in lengths)
    assert any(length in (4, 5) for length in lengths)
    assert adjacent_any_six(grid) != intended_rule(grid)
    assert canonical_lengths_only(grid) != intended_rule(grid)
    if edge_bar:
        assert interior_bars_only(grid) != intended_rule(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"difficulty": "expert"},
        {"unknown_axis": 1},
        {"texture": "length_one_bars"},
        {"grid_h": 6},
        {"grid_h": 19},
        {"grid_w": 6},
        {"grid_w": 21},
        {"n_bars": 2},
        {"n_bars": 5},
        {"bar_length": 1},
        {"bar_length": 6},
        {"edge_bar": 1},
        {"edge_bar": "true"},
        {"singleton_layout": "diagonal"},
        {"grid_h": True},
        {"grid_w": 9.5},
        {"n_bars": "3"},
    ],
)
def test_invalid_controls_fail_loudly(kwargs):
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty, **kwargs)


@pytest.mark.parametrize("band,expected_size", [("easy", 7), ("medium", 8), ("hard", 9)])
def test_default_distribution_teaches_all_rule_boundaries(band, expected_size):
    seen_layouts = set()
    distinct = set()
    for index in range(48):
        grid = GEN.generate(901, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert (len(grid), len(grid[0])) == (expected_size, expected_size)
        runs = row_runs(grid)
        assert len([run for run in runs if run[2] == run[1]]) == 2
        bars = [run for run in runs if run[2] > run[1]]
        assert len(bars) in {3, 4}
        lengths = {end - start + 1 for _row, start, end in bars}
        assert len(lengths) >= 2
        assert any(length in (2, 3) for length in lengths)
        assert any(length in (4, 5) for length in lengths)
        assert GEN.SEMANTIC_WITNESSES["singleton_exclusion"](grid)
        assert GEN.SEMANTIC_WITNESSES["long_bar"](grid)
        assert GEN.SEMANTIC_WITNESSES["edge_bar"](grid)
        assert GEN.SEMANTIC_RIVALS["adjacent_any_six"](grid) == adjacent_any_six(grid)
        assert GEN.SEMANTIC_RIVALS["canonical_lengths_only"](grid) == canonical_lengths_only(grid)
        assert GEN.SEMANTIC_RIVALS["interior_bars_only"](grid) == interior_bars_only(grid)
        intended = intended_rule(grid)
        assert all(rival(grid) != intended for rival in GEN.LESSON_COMPETITORS.values())
        observed = GEN.observe_overrides(grid)
        assert observed["edge_bar"] is True
        seen_layouts.add(observed["singleton_layout"])
        distinct.add(tuple(map(tuple, grid)))
    assert seen_layouts == {"separate", "vertical"}
    assert len(distinct) >= 42


def test_three_demonstrations_and_every_query_rotation_refute_the_shortcut():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = [
                labeled_pair(GEN.generate(1300 + start, start + offset, difficulty=band))
                for offset in range(4)
            ]
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


def test_self_check_rejects_structural_impostors():
    valid = GEN.generate(
        29,
        4,
        grid_h=9,
        grid_w=9,
        n_bars=3,
        bar_length=3,
        edge_bar=False,
        singleton_layout="separate",
    )
    assert GEN.self_check(valid) == []

    mutations = [
        [[0] * 9 for _ in range(9)],
        [[6] * 9 for _ in range(9)],
        [[6, 6], [6, 6]],
        [[0] * 9 for _ in range(8)] + [[0] * 8],
    ]

    bad_color = deepcopy(valid)
    bad_color[0][0] = 8
    mutations.append(bad_color)

    one_singleton = deepcopy(valid)
    singleton = next(run for run in row_runs(one_singleton) if run[1] == run[2])
    one_singleton[singleton[0]][singleton[1]] = 0
    mutations.append(one_singleton)

    split_row = deepcopy(valid)
    bar = next(run for run in row_runs(split_row) if run[2] > run[1])
    split_row[bar[0]][bar[1] + 1] = 0
    mutations.append(split_row)

    oversized = [[0] * 9 for _ in range(9)]
    for r in (1, 3, 5):
        for c in range(1, 7):
            oversized[r][c] = 6
    mutations.append(oversized)

    for mutation in mutations:
        assert GEN.self_check(mutation), mutation


def test_pinned_profile_floor_has_exact_support_in_every_band():
    canonical_profiles = {(7, 7, 2), (8, 8, 2), (9, 9, 2)}
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            hits += profile in canonical_profiles
        assert hits == 20, (band, hits)


def test_generation_is_deterministic_fresh_and_helpers_are_pure():
    for band in (None, "easy", "medium", "hard"):
        for index in range(12):
            first = GEN.generate(77, index, difficulty=band)
            second = GEN.generate(77, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            original = deepcopy(first)
            GEN.observe_overrides(first)
            for helper in GEN.SEMANTIC_RIVALS.values():
                helper(first)
            for helper in GEN.SEMANTIC_WITNESSES.values():
                helper(first)
            assert first == original


def test_retained_singleton_counterexample_is_source_and_rule_bound():
    path = HOME / "counterexamples" / "adjacent-singleton-v0001" / "counterexample.json"
    record = __import__("json").loads(path.read_text())
    grid = record["input"]
    assert record["source_binding"]["rule_hash"] == GEN.RULE_HASH
    assert GEN.self_check(grid) == []
    assert intended_rule(grid) == record["intended_output"]
    assert adjacent_any_six(grid) == record["rival_output"]
    expected_diffs = [
        {"row": r, "col": c, "intended": record["intended_output"][r][c],
         "rival": record["rival_output"][r][c]}
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if record["intended_output"][r][c] != record["rival_output"][r][c]
    ]
    assert expected_diffs == record["differing_cells"]
    assert expected_diffs
