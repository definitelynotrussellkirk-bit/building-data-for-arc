"""Behavioral contract for the aligned-endpoint span generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK = "63a780e1d475"
ROOT = find_root(__file__)
SOURCE = Path(__file__).resolve().parents[1] / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("selected_endpoint_generator", SOURCE)
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def spans(grid):
    """Independent extraction of consecutive clear blue endpoint spans."""
    h, w = len(grid), len(grid[0])
    horizontal = []
    vertical = []
    for r in range(h):
        cols = [c for c in range(w) if grid[r][c] == 1]
        for c1, c2 in zip(cols, cols[1:]):
            if c2 - c1 > 1 and all(grid[r][c] == 0 for c in range(c1 + 1, c2)):
                horizontal.append((r, c1, c2))
    for c in range(w):
        rows = [r for r in range(h) if grid[r][c] == 1]
        for r1, r2 in zip(rows, rows[1:]):
            if r2 - r1 > 1 and all(grid[r][c] == 0 for r in range(r1 + 1, r2)):
                vertical.append((c, r1, r2))
    return horizontal, vertical


def intended_output(grid):
    """Independent Python mirror; canonical Racket remains label authority."""
    out = deepcopy(grid)
    horizontal, vertical = spans(grid)
    for r, c1, c2 in horizontal:
        for c in range(c1, c2 + 1):
            out[r][c] = 2
    for c, r1, r2 in vertical:
        for r in range(r1, r2 + 1):
            out[r][c] = 2
    return out


def crossing_count(grid):
    horizontal, vertical = spans(grid)
    return sum(
        c1 < c < c2 and r1 < r < r2
        for r, c1, c2 in horizontal
        for c, r1, r2 in vertical
    )


def observed(grid):
    horizontal, vertical = spans(grid)
    if horizontal and vertical:
        mode = "mixed_crossing" if crossing_count(grid) else "mixed_clear"
    elif horizontal:
        mode = "horizontal_only"
    elif vertical:
        mode = "vertical_only"
    else:
        mode = None
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_pairs": len(horizontal) + len(vertical),
        "orientation_mode": mode,
    }


def sequential_block_crossings(grid):
    """Plausible bug: test vertical clear-space after painting rows."""
    out = deepcopy(grid)
    horizontal, vertical = spans(grid)
    for r, c1, c2 in horizontal:
        for c in range(c1, c2 + 1):
            out[r][c] = 2
    for c, r1, r2 in vertical:
        if all(out[r][c] == 0 for r in range(r1 + 1, r2)):
            for r in range(r1, r2 + 1):
                out[r][c] = 2
    return out


def first_per_orientation(grid):
    out = deepcopy(grid)
    horizontal, vertical = spans(grid)
    if horizontal:
        r, c1, c2 = horizontal[0]
        for c in range(c1, c2 + 1):
            out[r][c] = 2
    if vertical:
        c, r1, r2 = vertical[0]
        for r in range(r1, r2 + 1):
            out[r][c] = 2
    return out


@pytest.mark.parametrize("pair", canonical_pairs(TASK, root=ROOT), ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_canonical_inputs_are_owned_and_python_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("mode,n_pairs", [
    ("horizontal_only", 2),
    ("horizontal_only", 4),
    ("vertical_only", 3),
    ("mixed_clear", 4),
    ("mixed_crossing", 2),
    ("mixed_crossing", 4),
])
def test_exact_overrides_are_pixel_observable_in_every_band(band, mode, n_pairs):
    options = {
        "grid_h": 12,
        "grid_w": 13,
        "n_pairs": n_pairs,
        "orientation_mode": mode,
    }
    grid = gen.generate(731, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert intended_output(grid) != grid


@pytest.mark.parametrize("override", [
    {"typo": 1},
    {"grid_h": 7}, {"grid_h": 15}, {"grid_h": True}, {"grid_h": 8.5},
    {"grid_w": 8}, {"grid_w": 15}, {"grid_w": "10"},
    {"n_pairs": 1}, {"n_pairs": 5}, {"n_pairs": False},
    {"orientation_mode": "diagonal"}, {"orientation_mode": 3},
    {"texture": "legacy"}, {"palette_kind": "default"},
])
def test_invalid_and_retired_controls_fail_loudly(override):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **override)


@pytest.mark.parametrize("mode", ["horizontal_only", "vertical_only", "mixed_clear", "mixed_crossing"])
def test_smallest_dimensions_support_maximum_pair_count(mode):
    grid = gen.generate(
        44, 3, grid_h=8, grid_w=9, n_pairs=4, orientation_mode=mode
    )
    assert gen.self_check(grid) == []
    assert observed(grid) == {
        "grid_h": 8,
        "grid_w": 9,
        "n_pairs": 4,
        "orientation_mode": mode,
    }


def test_mixed_crossing_is_a_real_canonical_shortcut_counterexample():
    grid = gen.generate(
        19, 0, grid_h=8, grid_w=9, n_pairs=3,
        orientation_mode="mixed_crossing",
    )
    assert crossing_count(grid) >= 1
    assert sequential_block_crossings(grid) != intended_output(grid)
    assert gen.SEMANTIC_RIVALS["sequential_block_crossings"](grid) == sequential_block_crossings(grid)
    assert gen.SEMANTIC_WITNESSES["crossing_spans"](grid)


def test_declared_canonical_shortcut_really_fits_every_labeled_pair():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


def test_first_per_orientation_is_the_train_only_shortcut():
    pairs = canonical_pairs(TASK, root=ROOT)
    train = [pair for pair in pairs if pair["split"] == "train"]
    test = [pair for pair in pairs if pair["split"] == "test"]
    assert all(first_per_orientation(pair["input"]) == pair["output"] for pair in train)
    assert any(first_per_orientation(pair["input"]) != pair["output"] for pair in test)
    assert gen.LESSON_COMPETITORS["first_per_orientation"](test[0]["input"]) == first_per_orientation(test[0]["input"])


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_schedule_start_and_query_rotation_refutes_declared_competitors(band):
    # Four demonstrations plus one query. Two crossing profiles per four-slot
    # cycle mean that holding out any one pair still leaves a crossing witness.
    for seed in range(8):
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            grids = [gen.generate(seed, start + offset, difficulty=band) for offset in range(5)]
            pairs = [{"input": g, "output": intended_output(g)} for g in grids]
            for query_index in range(5):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                query = pairs[query_index]
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(p["input"]) != p["output"] for p in demos), name


def test_difficulty_bands_have_distinct_default_pair_curricula():
    easy = [observed(gen.generate(701, i, difficulty="easy"))["n_pairs"] for i in range(8)]
    medium = [observed(gen.generate(701, i, difficulty="medium"))["n_pairs"] for i in range(8)]
    hard = [observed(gen.generate(701, i, difficulty="hard"))["n_pairs"] for i in range(8)]
    assert easy != medium != hard
    assert sum(easy) < sum(medium) < sum(hard)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_anchors_every_canonical_shape_and_all_modes(band):
    grids = [gen.generate(913 + i, i, difficulty=band) for i in range(80)]
    observations = [observed(grid) for grid in grids]
    shapes = {(item["grid_h"], item["grid_w"]) for item in observations}
    modes = {item["orientation_mode"] for item in observations}
    canonical_shapes = {
        (len(pair["input"]), len(pair["input"][0]))
        for pair in canonical_pairs(TASK, root=ROOT)
    }
    assert canonical_shapes <= shapes
    assert {"horizontal_only", "vertical_only", "mixed_crossing"} <= modes
    assert all(gen.self_check(grid) == [] for grid in grids)


def test_determinism_and_no_return_aliasing():
    first = gen.generate(876, 9, difficulty="hard")
    expected = deepcopy(first)
    first[0][0] = 9
    assert gen.generate(876, 9, difficulty="hard") == expected


@pytest.mark.parametrize("grid", [
    None,
    [],
    [[]],
    [[0], [0, 1]],
    [[False] * 9 for _ in range(8)],
    [[0] * 9 for _ in range(7)],
    [[0] * 8 for _ in range(8)],
    [[0] * 9 for _ in range(8)],
    [[3] + [0] * 8 for _ in range(8)],
])
def test_validator_rejects_malformed_or_rule_hiding_inputs(grid):
    assert gen.self_check(grid)


def test_validator_rejects_lone_or_multiply_used_blue_endpoints():
    lone = [[0] * 9 for _ in range(8)]
    lone[2][3] = 1
    assert gen.self_check(lone)

    ambiguous = [[0] * 9 for _ in range(8)]
    for r, c in ((1, 1), (1, 5), (4, 1)):
        ambiguous[r][c] = 1
    assert gen.self_check(ambiguous)
