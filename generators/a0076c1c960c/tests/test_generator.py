"""Focused regression tests for the bridge-only input sampler."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "a0076c1c960c"
ROOT = find_root(__file__)
gen, _SOURCE, _DIGEST = load_selected_generator(TASK_ID, root=ROOT)


def oracle(grid):
    """Independent Python restatement of the selected Racket row-closure rule."""
    out = [[0 for _ in row] for row in grid]
    for r, row in enumerate(grid):
        cols = [c for c, value in enumerate(row) if value != 0]
        if not cols:
            continue
        for c in range(min(cols), max(cols) + 1):
            if grid[r][c] == 0:
                out[r][c] = 8
    return out


def active_rows(grid):
    return [(r, [(c, value) for c, value in enumerate(row) if value])
            for r, row in enumerate(grid) if any(row)]


def test_authority_pin_and_exact_axis_surface():
    assert gen.RULE_HASH == "2205cb4e988b"
    assert set(gen.AXES) == {"shape", "active_rows", "span", "adjacent_mode", "palette_mode"}
    assert gen.EXPECTED_OUTPUT_CODOMAIN == (0, 8)


@pytest.mark.parametrize("pair", canonical_pairs(TASK_ID, root=ROOT, labeled_only=True),
                         ids=["train0", "train1", "test0"])
def test_accepts_every_canonical_pair_and_matches_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert oracle(pair["input"]) == pair["output"]
    assert gen._bridge_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("shape", ["8x10", "8x11", "9x9"])
@pytest.mark.parametrize("active_count", [2, 3, 4])
@pytest.mark.parametrize("span", [2, 3, 6])
@pytest.mark.parametrize("adjacent_mode", ["absent", "present"])
@pytest.mark.parametrize("palette_mode", ["canonical", "same_color", "mixed_color"])
def test_explicit_overrides_are_exact_and_observable(shape, active_count, span, adjacent_mode, palette_mode):
    options = {
        "shape": shape,
        "active_rows": active_count,
        "span": span,
        "adjacent_mode": adjacent_mode,
        "palette_mode": palette_mode,
    }
    grid = gen.generate(71, 13, difficulty="hard", **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options
    assert oracle(grid) == gen._bridge_output(grid)


@pytest.mark.parametrize("mode", ["canonical", "same_color", "mixed_color"])
def test_palette_modes_have_distinct_pixel_semantics(mode):
    grid = gen.generate(9, 2, shape="8x10", active_rows=4, span=4, adjacent_mode="absent", palette_mode=mode)
    rows = active_rows(grid)
    assert len(rows) == 4
    if mode == "canonical":
        assert {value for _r, cells in rows for _c, value in cells} == {2}
    elif mode == "same_color":
        assert all(cells[0][1] == cells[1][1] != 2 for _r, cells in rows)
    else:
        assert all(cells[0][1] != cells[1][1] for _r, cells in rows)


@pytest.mark.parametrize("bad", [
    {"typo": 1},
    {"shape": "7x9"},
    {"active_rows": 1},
    {"active_rows": 5},
    {"span": 1},
    {"span": 7},
    {"adjacent_mode": "sometimes"},
    {"palette_mode": "rainbow"},
    {"span": True},
    {"active_rows": 2.0},
    {"shape": 810},
])
def test_invalid_overrides_are_rejected(bad):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **bad)


@pytest.mark.parametrize("sample_index", [-1, True, 1.0, "1"])
def test_invalid_sample_index_is_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, sample_index)


def test_semantic_shortcut_fits_canonical_but_mixed_colors_refute_it():
    rival = gen.CANONICAL_SHORTCUTS["same_color_pairs_only"]
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert rival(pair["input"]) == pair["output"]

    grid = gen.generate(5, 0, shape="8x10", active_rows=2, span=4,
                        adjacent_mode="absent", palette_mode="mixed_color")
    assert gen.SEMANTIC_WITNESSES["mixed_endpoint_colors"](grid)
    assert rival(grid) != oracle(grid)
    assert gen.WITNESS_RIVALS["mixed_endpoint_colors"] == ["same_color_pairs_only"]


def test_every_four_default_draws_keep_a_mixed_counterexample_after_any_holdout():
    for start in range(18):
        grids = [gen.generate(101, start + offset) for offset in range(4)]
        modes = [gen.observe_overrides(grid)["palette_mode"] for grid in grids]
        assert modes.count("mixed_color") >= 2
        for held_out in range(4):
            demos = [grid for i, grid in enumerate(grids) if i != held_out]
            assert any(gen.SEMANTIC_WITNESSES["mixed_endpoint_colors"](grid)
                       for grid in demos)


def test_bridge_output_is_fresh_drops_markers_and_paints_only_interiors():
    grid = gen.generate(33, 8, shape="8x11", active_rows=3, span=5,
                        adjacent_mode="present", palette_mode="mixed_color")
    original = deepcopy(grid)
    out = gen._bridge_output(grid)
    assert grid == original
    assert out == oracle(grid)
    for _r, cells in active_rows(grid):
        for c, _value in cells:
            assert out[_r][c] == 0
    assert {value for row in out for value in row} <= {0, 8}


@pytest.mark.parametrize("mutation", ["blank", "third_marker", "vertical_pair", "bad_color", "too_many_rows", "solid_2x2"])
def test_self_check_rejects_near_miss_inputs(mutation):
    grid = gen.generate(17, 3, shape="8x10", active_rows=2, span=3,
                        adjacent_mode="absent", palette_mode="canonical")
    if mutation == "blank":
        grid = [[0] * 10 for _ in range(8)]
    elif mutation == "third_marker":
        r, cells = active_rows(grid)[0]
        occupied = {c for c, _ in cells}
        c = next(c for c in range(10) if c not in occupied)
        grid[r][c] = 3
    elif mutation == "vertical_pair":
        rows = active_rows(grid)
        r, cells = rows[0]
        c, value = cells[0]
        grid[r][c] = 0
        empty_row = next(rr for rr in range(8) if not any(grid[rr]))
        grid[empty_row][c] = value
    elif mutation == "bad_color":
        r, cells = active_rows(grid)[0]
        grid[r][cells[0][0]] = 8
    elif mutation == "too_many_rows":
        grid = [[0] * 10 for _ in range(8)]
        for r in range(5):
            grid[r][1] = grid[r][4] = 2
    elif mutation == "solid_2x2":
        grid = [[0] * 10 for _ in range(8)]
        grid[0][0] = grid[0][1] = 2
        grid[1][0] = grid[1][1] = 2
    assert gen.self_check(grid)


def test_retained_same_color_shortcut_counterexample_is_replayable():
    overrides = {
        "shape": "8x10",
        "active_rows": 2,
        "span": 4,
        "adjacent_mode": "absent",
        "palette_mode": "mixed_color",
    }
    input_grid = gen.generate(5, 0, difficulty=None, **overrides)
    authority_output = oracle(input_grid)
    rival_output = gen._same_color_pairs_only(input_grid)

    # The portable task-test runtime intentionally snapshots the selected
    # generator and tests but may omit task-local counterexample assets.  Keep
    # the exact seeded witness executable there, and additionally bind the
    # retained JSON record whenever running from the full repository layout.
    path = Path(_SOURCE).parent / "counterexamples" / "same_color_pairs_only.json"
    if path.exists():
        record = json.loads(path.read_text(encoding="utf-8"))
        assert record["task_id"] == TASK_ID
        assert record["generator_sha256"] == _DIGEST
        assert record["rule_source_sha256"].startswith(gen.RULE_HASH)
        assert record["seed"] == 5
        assert record["sample_index"] == 0
        assert record["difficulty"] is None
        assert record["overrides"] == overrides
        assert record["self_check"] == []
        assert record["input"] == input_grid
        assert record["authority_output"] == authority_output
        assert record["rival_output"] == rival_output

    assert gen.self_check(input_grid) == []
    assert gen._bridge_output(input_grid) == authority_output
    assert authority_output != rival_output
