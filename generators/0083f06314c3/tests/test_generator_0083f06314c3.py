from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs

GEN = importlib.import_module("puzzle_generators.per_puzzle.0083f06314c3.generator")


def test_rule_hash_pinned():
    assert GEN.RULE_HASH == "6a4eb398052b"


def test_canonical_pairs_owned_and_solved():
    pairs = canonical_pairs("0083f06314c3")
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_unknown_override_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, difficulty="medium", definitely_unknown_axis=7)


@pytest.mark.parametrize("axis,boundaries", [
    ("grid_h", (6, 8)),
    ("template_w", (3, 4)),
    ("board_w", (8, 12)),
    ("template_cells", (3, 5)),
    ("selected_copies", (1, 2)),
    ("distractor_copies", (1, 2)),
])
def test_axis_boundaries_are_observable(axis, boundaries):
    for offset, value in enumerate(boundaries):
        grid = GEN.generate(101 + offset, 101 + offset, difficulty="hard", **{axis: value})
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid)[axis] == value


def test_schedule_window_exercises_both_branches_and_adversarial_rivals():
    grids = [GEN.generate(888, i, difficulty="medium") for i in range(4)]
    assert [GEN.schedule_profile(888, i, "medium") for i in range(4)] == list(GEN.SCHEDULE_PROFILES)
    assert {GEN._selected_index(g) for g in grids} == {0, 1}
    for i in (1, 3):
        canonical = GEN.rule_mirror(grids[i])
        names = [name for name, rival in GEN.SEMANTIC_RIVALS.items() if rival(grids[i]) != canonical]
        assert "solid_bbox" in names
        assert "d4_rotation" in names
        assert "shape_only_ignore_color" in names


def test_minimal_invalid_mutations_are_rejected():
    grid = GEN.generate(42, 1, difficulty="medium")
    assert GEN.self_check(grid) == []
    dividers = [c for c in range(len(grid[0])) if all(row[c] == 9 for row in grid)]

    no_divider = copy.deepcopy(grid)
    for row in no_divider:
        row[dividers[0]] = 0
    assert GEN.self_check(no_divider)

    no_selector = copy.deepcopy(grid)
    selector_col = dividers[1] + 1
    for row in no_selector:
        row[selector_col] = 0
    assert GEN.self_check(no_selector)

    too_wide = copy.deepcopy(grid)
    for row in too_wide:
        row.extend([0] * 5)
    assert GEN.self_check(too_wide)


def test_generator_preserves_process_global_random_state():
    import random
    random.seed(10203)
    before = random.getstate()
    GEN.generate(9, 9, difficulty="easy")
    assert random.getstate() == before
