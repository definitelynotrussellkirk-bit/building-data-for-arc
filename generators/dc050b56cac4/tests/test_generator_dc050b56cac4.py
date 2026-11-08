"""Regression tests for dc050b56cac4.

The Python rule below is an independent test oracle. Racket remains the label
authority; these tests pin the public generator contract and known shortcut
counterexamples without importing production-private helpers.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys

import pytest

TASK = "dc050b56cac4"
HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))
from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_dc050b56cac4", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
PAIRS = canonical_pairs(TASK, root=find_root(__file__), labeled_only=True)


def analyze(grid):
    h, w = len(grid), len(grid[0])
    rows = [
        (r, grid[r][0])
        for r in range(h)
        if grid[r][0] not in (0, 5) and len(set(grid[r])) == 1
    ]
    cols = []
    for c in range(w):
        values = [grid[r][c] for r in range(h)]
        if values[0] not in (0, 5) and len(set(values)) == 1:
            cols.append((c, values[0]))
    if len(rows) != 1 or len(cols) != 1 or rows[0][1] != cols[0][1]:
        raise ValueError("not one same-color full-row/full-column cross")
    grays = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]
    return {
        "grid_h": h,
        "grid_w": w,
        "cross_row": rows[0][0],
        "cross_col": cols[0][0],
        "cross_color": rows[0][1],
        "n_grays": len(grays),
        "grays": grays,
    }


def intended_output(grid, *, shift=None):
    facts = analyze(grid)
    n = facts["n_grays"] if shift is None else shift
    nr = facts["cross_row"] + n
    nc = facts["cross_col"] - n
    return [
        [facts["cross_color"] if r == nr or c == nc else 0 for c in range(facts["grid_w"])]
        for r in range(facts["grid_h"])
    ]


def gray_row_count_rival(grid):
    return intended_output(grid, shift=len({r for r, _ in analyze(grid)["grays"]}))


def gray_vertical_span_rival(grid):
    rows = [r for r, _ in analyze(grid)["grays"]]
    return intended_output(grid, shift=max(rows) - min(rows) + 1)


def top_right_stack_rival(grid):
    n = 0
    for row in grid:
        if row[-1] != 5:
            break
        n += 1
    return intended_output(grid, shift=n)


def test_rule_pin_and_constructive_public_axes():
    assert GEN.RULE_HASH == "4fe6d23687d0"
    assert set(GEN.AXES) == {
        "grid_h", "grid_w", "cross_color", "n_grays", "cross_position"
    }
    assert tuple(GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()
    assert not getattr(GEN, "DEGENERATE_TEXTURES", ())


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"v{p['variant']}-{p['split']}{p['pair_index']}")
def test_canonical_pairs_are_accepted_and_match_independent_rule(pair):
    assert GEN.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "position", ["center", "upper_left", "upper_right", "lower_left", "lower_right"]
)
def test_every_exact_override_is_constructive_and_observable_in_every_band(band, position):
    expected = {
        "grid_h": 8,
        "grid_w": 8,
        "cross_color": 9,
        "n_grays": 3,
        "cross_position": position,
    }
    grid = GEN.generate(41, 7, difficulty=band, **expected)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == expected
    assert intended_output(grid) != grid


@pytest.mark.parametrize(
    "bad",
    [
        {"typo": 1},
        {"grid_h": 7}, {"grid_h": 21}, {"grid_h": True}, {"grid_h": 9.5},
        {"grid_w": 7}, {"grid_w": 21}, {"grid_w": "10"},
        {"cross_color": 0}, {"cross_color": 5}, {"cross_color": 10}, {"cross_color": True},
        {"n_grays": 0}, {"n_grays": 4}, {"n_grays": 2.0},
        {"cross_position": "spread"}, {"cross_position": 1},
    ],
)
def test_invalid_overrides_are_rejected_instead_of_clipped_or_ignored(bad):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **bad)


def test_invalid_difficulty_is_rejected():
    with pytest.raises(ValueError):
        GEN.generate(0, 0, difficulty="expert")


def test_schedule_emits_canonical_profile_and_two_shortcut_counterexamples():
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "canonical_stack", "same_row_witness", "scattered_witness"
    )
    grids = [GEN.generate(701, i, difficulty="medium") for i in range(3)]
    assert [GEN.schedule_profile(701, i, "medium") for i in range(3)] == list(GEN.SCHEDULE_PROFILES)
    assert all(GEN.self_check(grid) == [] for grid in grids)

    canonical, same_row, scattered = map(analyze, grids)
    assert (canonical["grid_h"], canonical["grid_w"]) == (10, 10)
    assert canonical["grays"] == [(r, 9) for r in range(canonical["n_grays"])]

    assert same_row["n_grays"] >= 2
    assert len({r for r, _ in same_row["grays"]}) == 1
    assert all(c != same_row["grid_w"] - 1 for _, c in same_row["grays"])

    assert scattered["n_grays"] == 3
    assert len({r for r, _ in scattered["grays"]}) == 2
    assert max(r for r, _ in scattered["grays"]) - min(r for r, _ in scattered["grays"]) + 1 == 2
    assert all(c != scattered["grid_w"] - 1 for _, c in scattered["grays"])


def test_declared_shortcuts_fit_every_canonical_pair():
    rivals = (gray_row_count_rival, gray_vertical_span_rival, top_right_stack_rival)
    for pair in PAIRS:
        assert all(rival(pair["input"]) == pair["output"] for rival in rivals)


@pytest.mark.parametrize("sample_index", [1, 2])
def test_generated_witnesses_refute_all_three_canonical_shortcuts(sample_index):
    grid = GEN.generate(701, sample_index, difficulty="medium")
    intended = intended_output(grid)
    assert intended != gray_row_count_rival(grid)
    assert intended != gray_vertical_span_rival(grid)
    assert intended != top_right_stack_rival(grid)
    assert any(predicate(grid) for predicate in GEN.SEMANTIC_WITNESSES.values())
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert rival(grid) != intended, name


def test_every_four_pair_window_remains_identifiable_under_query_rotation():
    for start in range(12):
        pairs = []
        for offset in range(4):
            grid = GEN.generate(9000 + start, start + offset, difficulty="hard")
            pairs.append({"input": grid, "output": intended_output(grid)})
        for query_index in range(4):
            query = pairs[query_index]
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for rival in GEN.LESSON_COMPETITORS.values():
                assert not all(rival(d["input"]) == d["output"] for d in demos)


@pytest.mark.parametrize(
    "mutation",
    ["remove_gray", "extra_gray", "extra_cross_color", "unknown_color", "edge_shift"],
)
def test_self_check_rejects_structural_near_misses(mutation):
    grid = GEN.generate(222, 1, grid_h=10, grid_w=10, n_grays=2, cross_position="center")
    facts = analyze(grid)
    if mutation == "remove_gray":
        for r, c in facts["grays"]:
            grid[r][c] = 0
    elif mutation == "extra_gray":
        placed = 0
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if grid[r][c] == 0:
                    grid[r][c] = 5
                    placed += 1
                    if placed == 2:
                        break
            if placed == 2:
                break
    elif mutation == "extra_cross_color":
        r, c = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 0)
        grid[r][c] = facts["cross_color"]
    elif mutation == "unknown_color":
        r, c = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 0)
        grid[r][c] = 10
    elif mutation == "edge_shift":
        grid = [[0] * 8 for _ in range(8)]
        for c in range(8):
            grid[7][c] = 2
        for r in range(8):
            grid[r][1] = 2
        grid[0][7] = 5
    assert GEN.self_check(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(8)]])
def test_self_check_is_diagnostic_on_malformed_grids(bad):
    assert GEN.self_check(bad)


def test_generation_is_deterministic_and_does_not_mutate_inputs():
    first = GEN.generate(992, 8, difficulty="hard")
    assert first == GEN.generate(992, 8, difficulty="hard")
    original = deepcopy(first)
    assert intended_output(first)
    assert first == original
