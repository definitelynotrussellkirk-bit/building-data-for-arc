"""Focused semantic and contract regressions for 82b2be9b4f4e."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "82b2be9b4f4e"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
BANDS = ("easy", "medium", "hard")
ROOT = find_root(__file__)


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] != color:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = set()
            while stack:
                cr, cc = stack.pop()
                cells.add((cr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = (cr + dr, cc + dc)
                    if (
                        0 <= point[0] < h
                        and 0 <= point[1] < w
                        and point not in seen
                        and grid[point[0]][point[1]] == color
                    ):
                        seen.add(point)
                        stack.append(point)
            result.append(cells)
    return result


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _reference_output(grid):
    """Independent mirror of the unchanged Racket authority for test evidence."""
    work = [list(row) for row in grid]
    key = work[-1][0]
    work[-1][0] = 0
    components = _components(work, key)
    assert components
    # The repaired generator makes sizes unique, so the authority's tie-break is idle.
    winner = max(components, key=len)
    r0, c0, r1, c1 = _bbox(winner)
    crop = [row[c0 : c1 + 1] for row in work[r0 : r1 + 1]]
    return [
        [value for value in row for _ in range(2)]
        for row in crop
        for _ in range(2)
    ]


def _observed_key_components(grid):
    work = [list(row) for row in grid]
    key = work[-1][0]
    work[-1][0] = 0
    return key, _components(work, key)


def test_rule_hash_and_all_canonical_pairs_are_bound_and_lawful():
    assert GEN.RULE_HASH == "eff131529ace"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert _reference_output(source) == pair["output"]
        assert source == pair["input"]


def test_exact_axes_round_trip_in_every_band():
    cases = (
        {
            "grid_h": 8,
            "grid_w": 11,
            "key_color": 1,
            "n_key_blobs": 1,
            "n_distractors": 2,
        },
        {
            "grid_h": 16,
            "grid_w": 17,
            "key_color": 9,
            "n_key_blobs": 2,
            "n_distractors": 3,
        },
        {
            "grid_h": 9,
            "grid_w": 13,
            "key_color": 5,
            "n_key_blobs": 2,
            "n_distractors": 2,
        },
    )
    for band in BANDS:
        for index, expected in enumerate(cases):
            grid = GEN.generate(1701 + index, 7 + index, difficulty=band, **expected)
            assert GEN.self_check(grid, meta={"overrides": expected}) == []
            assert GEN.observe_overrides(grid) == expected
            assert _reference_output(grid)


@pytest.mark.parametrize(
    "overrides",
    (
        {"grid_h": 7},
        {"grid_h": 17},
        {"grid_w": 10},
        {"grid_w": 18},
        {"key_color": 0},
        {"key_color": 10},
        {"n_key_blobs": 0},
        {"n_key_blobs": 3},
        {"n_distractors": 1},
        {"n_distractors": 4},
        {"grid_h": True},
        {"n_key_blobs": 1.5},
    ),
)
def test_invalid_override_values_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **overrides)


def test_unknown_override_and_difficulty_are_rejected():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 0, misspelled_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="expert")


def test_minimum_canvas_supports_maximum_counts_across_many_draws():
    expected = {
        "grid_h": 8,
        "grid_w": 11,
        "key_color": 9,
        "n_key_blobs": 2,
        "n_distractors": 3,
    }
    for seed in range(80):
        grid = GEN.generate(seed, seed * 13 + 5, difficulty=BANDS[seed % 3], **expected)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == expected


def test_default_census_covers_canonical_winner_component_sizes():
    canonical_sizes = set()
    for pair in canonical_pairs(TASK_ID, root=ROOT):
        key, components = _observed_key_components(pair["input"])
        assert key != 0 and components
        canonical_sizes.add(max(map(len, components)))

    generated_sizes = set()
    for band in BANDS:
        for seed in range(1, 49):
            grid = GEN.generate(seed, seed, difficulty=band)
            _, components = _observed_key_components(grid)
            generated_sizes.add(max(map(len, components)))

    assert canonical_sizes <= generated_sizes


def test_default_distribution_is_lawful_and_covers_core_and_discriminator_branches():
    for band in BANDS:
        observed = []
        for index in range(90):
            grid = GEN.generate(4400 + index, index, difficulty=band)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            observed.append(GEN.observe_overrides(grid))
        assert {item["n_key_blobs"] for item in observed} == {1, 2}
        assert {item["n_distractors"] for item in observed} == {2, 3}
        assert any(8 <= item["grid_h"] <= 10 and 11 <= item["grid_w"] <= 13 for item in observed)
        assert len({item["key_color"] for item in observed}) >= 7


def test_deterministic_fresh_returns_and_global_rng_purity():
    random.seed(987654321)
    state = random.getstate()
    first = GEN.generate(77, 19, difficulty="hard")
    intervening = GEN.generate(78, 20, difficulty="easy")
    second = GEN.generate(77, 19, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert intervening != first
    first[0][0] = 99
    assert GEN.generate(77, 19, difficulty="hard") == second


def test_winner_bbox_is_pure_and_key_sizes_are_unique():
    for index in range(120):
        grid = GEN.generate(8000 + index, index, n_key_blobs=2)
        key, components = _observed_key_components(grid)
        assert len(components) == 2
        assert len({len(component) for component in components}) == 2
        winner = max(components, key=len)
        r0, c0, r1, c1 = _bbox(winner)
        assert {
            grid[r][c]
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
        } <= {0, key}


def test_self_check_rejects_structural_impostors():
    assert GEN.self_check([[5] * 11 for _ in range(8)])

    valid = GEN.generate(71, 4, n_key_blobs=2, n_distractors=2)
    key, components = _observed_key_components(valid)

    missing_distractors = copy.deepcopy(valid)
    for r, row in enumerate(missing_distractors):
        for c, value in enumerate(row):
            if value not in (0, key):
                missing_distractors[r][c] = 0
    assert GEN.self_check(missing_distractors)

    contaminated = copy.deepcopy(valid)
    winner = max(components, key=len)
    r0, c0, r1, c1 = _bbox(winner)
    hole = next(
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if contaminated[r][c] == 0
    )
    distractor = next(value for row in valid for value in row if value not in (0, key))
    contaminated[hole[0]][hole[1]] = distractor
    assert any("winner bbox" in message for message in GEN.self_check(contaminated))


def test_every_four_pair_window_refutes_rival_under_every_query_rotation():
    rival = GEN.SEMANTIC_RIVALS["merge_all_matching_pixels"]
    for band in BANDS:
        for seed in range(10):
            for start in range(4):
                window = [
                    GEN.generate(seed, start + offset, difficulty=band)
                    for offset in range(4)
                ]
                for query_index in range(4):
                    demos = [
                        grid
                        for index, grid in enumerate(window)
                        if index != query_index
                    ]
                    assert any(
                        rival(grid) != _reference_output(grid) for grid in demos
                    ), (band, seed, start, query_index)


def test_declared_rival_fits_canonical_but_generated_witness_refutes_it():
    rival = GEN.SEMANTIC_RIVALS["merge_all_matching_pixels"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs(TASK_ID, root=ROOT))

    for band in BANDS:
        grid = GEN.generate(991, 2, difficulty=band, n_key_blobs=2)
        assert GEN.SEMANTIC_WITNESSES["multiple_matching_objects"](grid)
        assert rival(grid) != _reference_output(grid)
        assert GEN.CANONICAL_SHORTCUTS["merge_all_matching_pixels"](grid) == rival(grid)
        assert GEN.LESSON_COMPETITORS["merge_all_matching_pixels"](grid) == rival(grid)
