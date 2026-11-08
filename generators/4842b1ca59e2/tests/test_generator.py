"""Focused regression and curriculum tests for 4842b1ca59e2."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import random
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "4842b1ca59e2"
HOME = Path(__file__).resolve().parents[1]
SPEC = spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def intended(grid):
    height = len(grid)
    width = len(grid[0])
    out = [[0] * width for _ in range(height)]
    for col in range(width):
        color = next((grid[row][col] for row in range(height) if grid[row][col] != 0), 0)
        for row in range(height):
            out[row][col] = color
    return out


def pair(grid):
    return {"input": grid, "output": intended(grid)}


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_pin_and_minimal_exact_axis_contract():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "977235c720d6"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {
        "grid_h", "grid_w", "active_columns", "stacked_columns", "stack_depth"
    }


def test_all_canonical_pairs_are_accepted_and_mirrored_exactly():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    for item in pairs:
        original = deepcopy(item["input"])
        assert GEN.self_check(item["input"]) == []
        assert GEN.strict_canonical_like(item["input"]) == []
        assert intended(item["input"]) == item["output"]
        assert GEN.rule_mirror(item["input"]) == item["output"]
        assert item["input"] == original


def test_declared_canonical_shortcuts_reproduce_every_public_label():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert set(GEN.CANONICAL_SHORTCUTS) == {"single_seed_columns_only", "bottommost_seed"}
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(item["input"]) == item["output"] for item in pairs), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 4, "grid_w": 5, "active_columns": 2, "stacked_columns": 1, "stack_depth": 2},
        {"grid_h": 8, "grid_w": 9, "active_columns": 4, "stacked_columns": 2, "stack_depth": 3},
        {"grid_h": 5, "grid_w": 6, "active_columns": 3, "stacked_columns": 2, "stack_depth": 2},
    ],
)
def test_exact_overrides_are_constructive_observable_and_semantic(band, overrides):
    grid = GEN.generate(1701, 29, difficulty=band, **overrides)
    assert GEN.self_check(grid, difficulty=band) == []
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.rule_mirror(grid) == intended(grid)
    assert all(predicate(grid) for predicate in GEN.SEMANTIC_WITNESSES.values())
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert rival(grid) != intended(grid), name


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1}, {"grid_h": 3}, {"grid_h": 9}, {"grid_w": 4},
        {"grid_w": 10}, {"active_columns": 1}, {"active_columns": 5},
        {"stacked_columns": 0}, {"stacked_columns": 3}, {"stack_depth": 1},
        {"stack_depth": 4}, {"grid_h": True}, {"grid_w": 6.0},
        {"active_columns": "3"}, {"stacked_columns": None},
    ],
)
def test_invalid_unknown_or_wrong_typed_controls_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_default_draw_is_a_counterexample_to_both_canonical_shortcuts(band):
    grids = [GEN.generate(9100 + index, index, difficulty=band) for index in range(80)]
    assert len({frozen(grid) for grid in grids}) >= 76
    for grid in grids:
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert all(predicate(grid) for predicate in GEN.SEMANTIC_WITNESSES.values())
        truth = intended(grid)
        assert GEN.rule_mirror(grid) == truth
        for name, rival in GEN.CANONICAL_SHORTCUTS.items():
            assert rival(grid) != truth, name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_pair_window_and_every_query_rotation_is_identifiable(band):
    for start in range(16):
        pairs = [pair(GEN.generate(1207 + start, start + offset, difficulty=band))
                 for offset in range(4)]
        for query_index, query in enumerate(pairs):
            demos = [item for index, item in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(item["input"]) != item["output"] for item in demos), (
                    band, start, query_index, name
                )


def test_generation_and_helpers_are_deterministic_fresh_and_pure():
    random.seed(987654321)
    state = random.getstate()
    for band in (None, "easy", "medium", "hard"):
        for index in range(12):
            first = GEN.generate(77, index, difficulty=band)
            second = GEN.generate(77, index, difficulty=band)
            assert random.getstate() == state
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            original = deepcopy(first)
            assert GEN.rule_mirror(first) == intended(first)
            for fn in GEN.SEMANTIC_RIVALS.values():
                fn(first)
                assert first == original
            for fn in GEN.SEMANTIC_WITNESSES.values():
                fn(first)
                assert first == original


def test_self_check_rejects_malformed_and_semantic_impostors_without_raising():
    invalid = [
        None, [], [[]], [[0] * 5 for _ in range(4)], [[1, 0], [0]],
        [[10, 0, 0, 0, 0] for _ in range(4)],
        [[1, 2, 0, 0, 0] for _ in range(4)],
    ]
    for grid in invalid:
        reasons = GEN.self_check(grid)
        assert isinstance(reasons, list) and reasons

    good = GEN.generate(44, 2)
    duplicate_top_color = deepcopy(good)
    active = [c for c in range(len(good[0])) if any(row[c] for row in good)]
    top = []
    for col in active:
        row = next(r for r in range(len(good)) if good[r][col])
        top.append((row, col))
    duplicate_top_color[top[1][0]][top[1][1]] = duplicate_top_color[top[0][0]][top[0][1]]
    assert GEN.self_check(duplicate_top_color)


def test_pinned_profile_floor_has_exact_canonical_support_in_every_band():
    canonical_profiles = {(4, 5, 3), (4, 6, 3), (5, 6, 3), (5, 6, 4)}
    for band in ("easy", "medium", "hard"):
        exact = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            exact += profile in canonical_profiles
        assert exact == 20, (band, exact)
