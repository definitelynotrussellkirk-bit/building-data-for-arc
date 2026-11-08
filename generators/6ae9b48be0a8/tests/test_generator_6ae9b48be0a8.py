"""Focused structural and semantic regressions for generator 6ae9b48be0a8."""
from __future__ import annotations

from collections import Counter
import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import (
    canonical_pairs,
    canonical_rule_hash,
    normalized_rule_hash,
)


TASK_ID = "6ae9b48be0a8"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.6ae9b48be0a8.generator"
)
BANDS = ("easy", "medium", "hard")


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _blank(height=12, width=14):
    return [[0] * width for _ in range(height)]


def _paint(grid, top, left, shape, color=3):
    for row, col in shape:
        grid[top + row][left + col] = color


def test_metadata_and_authoritative_rule_hash_are_pinned():
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "4.0.0"
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID)
    assert GEN.RULE_HASH == normalized_rule_hash(
        " ".join(importlib.import_module("scripts.canonical_profile_gate").canonical_rule_source(TASK_ID).split())
    )


def test_all_canonical_pairs_are_accepted_and_exact():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        analysis = GEN._analyze(pair["input"])
        assert sorted(analysis["frequencies"].values()) == [1, 2]
        assert analysis["border"]


def test_canonical_shortcuts_really_fit_the_canonical_examples():
    pairs = canonical_pairs(TASK_ID)
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


def test_every_band_and_schedule_profile_is_strict_and_exact():
    for band_index, band in enumerate(BANDS):
        profiles = Counter()
        ranks = Counter()
        for index in range(120):
            grid = GEN.generate(10_000 * band_index + index, index, difficulty=band)
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
            observed = GEN.observe_overrides(grid)
            profiles[observed["unique_relation"]] += 1
            ranks[observed["target_rank"]] += 1
            output = GEN.rule_mirror(grid)
            analysis = GEN._analyze(grid)
            yellow = {
                (row, col)
                for row, values in enumerate(output)
                for col, value in enumerate(values)
                if value == 4
            }
            assert yellow == set(analysis["border"])
            assert all(output[row][col] == 3 for row, col in analysis["target"])
        assert set(profiles) == set(GEN._RELATIONS)
        assert set(ranks) == set(GEN._TARGET_RANKS)


def test_every_four_demo_window_is_identifiable():
    for band_index, band in enumerate(BANDS):
        for start in range(16):
            demos = []
            for offset in range(GEN.EXAMPLES_NEEDED):
                index = start + offset
                grid = GEN.generate(
                    20_000 + 1_000 * band_index + start,
                    index,
                    difficulty=band,
                )
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            query_grid = GEN.generate(30_000 + start, start + 4, difficulty=band)
            assert GEN.lesson_identifiable(demos, {"input": query_grid}) == []


@pytest.mark.parametrize("grid_h", [10, 16])
@pytest.mark.parametrize("grid_w", [12, 18])
@pytest.mark.parametrize("unique_relation", list(GEN._RELATIONS))
@pytest.mark.parametrize("target_rank", list(GEN._TARGET_RANKS))
def test_full_boundary_override_cross_product_is_observable(
    grid_h, grid_w, unique_relation, target_rank
):
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "unique_relation": unique_relation,
        "target_rank": target_rank,
    }
    grid = GEN.generate(40_001, 23, difficulty="hard", **requested)
    assert GEN.self_check(grid, meta=requested) == []
    assert GEN.observe_overrides(grid) == requested
    assert GEN.strict_canonical_like(grid) == []


def test_unknown_and_invalid_controls_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, texture="solid")
    with pytest.raises(ValueError, match="grid_h must be an integer"):
        GEN.generate(1, 0, grid_h=True)
    with pytest.raises(ValueError, match="unique_relation"):
        GEN.generate(1, 0, unique_relation="reflection")
    with pytest.raises(ValueError, match="target_rank"):
        GEN.generate(1, 0, target_rank="north")
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="expert")


def test_semantic_witnesses_fire_and_their_rivals_disagree():
    seen = set()
    for index in range(80):
        grid = GEN.generate(50_000 + index, index, difficulty="medium")
        exact = GEN.rule_mirror(grid)
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            if not witness(grid):
                continue
            seen.add(witness_name)
            for rival_name in GEN.WITNESS_RIVALS[witness_name]:
                assert GEN.SEMANTIC_RIVALS[rival_name](grid) != exact
    assert seen == set(GEN.SEMANTIC_WITNESSES)


def test_self_check_rejects_targeted_semantic_impostors():
    base = GEN.generate(60_000, 3, difficulty="hard")
    info = GEN._analyze(base)

    all_blank = [[0 for _ in row] for row in base]
    assert GEN.self_check(all_blank)

    wrong_color = copy.deepcopy(base)
    row, col = info["target"][0]
    wrong_color[row][col] = 4
    assert GEN.self_check(wrong_color)

    all_same = _blank()
    l_shape = ((0, 0), (1, 0), (1, 1))
    for top, left in ((2, 2), (2, 8), (8, 5)):
        _paint(all_same, top, left, l_shape)
    assert GEN.self_check(all_same)

    all_distinct = _blank()
    _paint(all_distinct, 2, 2, l_shape)
    _paint(all_distinct, 2, 8, ((0, 0), (1, 0), (2, 0)))
    _paint(all_distinct, 7, 5, ((0, 1), (1, 0), (1, 1), (1, 2)))
    assert GEN.self_check(all_distinct)

    occupied_ring = copy.deepcopy(base)
    ring_cell = info["border"][0]
    occupied_ring[ring_cell[0]][ring_cell[1]] = 3
    assert GEN.self_check(occupied_ring)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(8675309)
    before = random.getstate()
    first = GEN.generate(70_000, 31, difficulty="medium")
    after = random.getstate()
    second = GEN.generate(70_000, 31, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert _freeze(GEN.generate(70_000, 31, difficulty="medium")) == _freeze(second)
