"""Regression tests for the exact-two-matching-row-endpoints generator."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "ffa91bb651d1"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def intended_output(grid):
    """Independent mirror of the selected exact-row predicate."""
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        nonzero = [(c, value) for c, value in enumerate(row) if value != 0]
        if len(nonzero) == 2 and nonzero[0][1] == nonzero[1][1]:
            left, color = nonzero[0]
            right = nonzero[1][0]
            for c in range(left, right + 1):
                out[r][c] = color
    return out


def per_color_exact_pair_shortcut(grid):
    """Wrong rival: fill any color occurring exactly twice, despite extra cells."""
    out = deepcopy(grid)
    for r, row in enumerate(grid):
        counts = Counter(value for value in row if value != 0)
        for color, count in counts.items():
            if count == 2:
                cols = [c for c, value in enumerate(row) if value == color]
                for c in range(cols[0], cols[-1] + 1):
                    out[r][c] = color
    return out


def row_or_column_shortcut(grid):
    """Wrong rival: apply the intended exact-pair rule to rows and columns."""
    out = intended_output(grid)
    height, width = len(grid), len(grid[0])
    for c in range(width):
        nonzero = [(r, grid[r][c]) for r in range(height) if grid[r][c] != 0]
        if len(nonzero) == 2 and nonzero[0][1] == nonzero[1][1]:
            top, color = nonzero[0]
            bottom = nonzero[1][0]
            for r in range(top, bottom + 1):
                out[r][c] = color
    return out


def exactly_three_targets_shortcut(grid):
    """Wrong rival: run the row rule only when the scene has three targets."""
    targets = 0
    for row in grid:
        nonzero = [(c, value) for c, value in enumerate(row) if value != 0]
        targets += int(len(nonzero) == 2 and nonzero[0][1] == nonzero[1][1])
    return intended_output(grid) if targets == 3 else deepcopy(grid)


def test_rule_pin_and_small_exact_axis_contract():
    assert GEN.RULE_HASH == "021dbc79a954"
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.EXAMPLES_NEEDED == 3
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "n_targets",
        "scene_pattern",
        "palette_count",
    }


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("pattern", ["canonical", "comprehensive"])
@pytest.mark.parametrize("n_targets", [2, 3])
@pytest.mark.parametrize("palette_count", [6, 7])
def test_every_joint_exact_override_is_constructive_and_observable(
    band, pattern, n_targets, palette_count
):
    grid = GEN.generate(
        91,
        7,
        difficulty=band,
        grid_h=6,
        grid_w=8,
        n_targets=n_targets,
        scene_pattern=pattern,
        palette_count=palette_count,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": 6,
        "grid_w": 8,
        "n_targets": n_targets,
        "scene_pattern": pattern,
        "palette_count": palette_count,
    }
    assert intended_output(grid) != grid


@pytest.mark.parametrize(
    "key,value",
    [
        ("grid_h", 5),
        ("grid_h", 17),
        ("grid_w", 7),
        ("grid_w", 17),
        ("n_targets", 1),
        ("n_targets", 4),
        ("scene_pattern", "unknown"),
        ("palette_count", 5),
        ("palette_count", 8),
        ("typo_axis", 1),
        ("grid_h", True),
        ("grid_w", 8.5),
        ("scene_pattern", 1),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **{key: value})


def test_canonical_inputs_are_owned_and_independent_oracle_matches_answers():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]


def test_declared_shortcuts_fit_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    shortcuts = {
        "per_color_exact_pair": per_color_exact_pair_shortcut,
        "row_or_column": row_or_column_shortcut,
        "exactly_three_targets": exactly_three_targets_shortcut,
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == set(shortcuts)
    for name, shortcut in shortcuts.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


def test_comprehensive_scene_refutes_all_canonical_fitting_shortcuts():
    grid = GEN.generate(
        44,
        1,
        scene_pattern="comprehensive",
        n_targets=2,
        grid_h=6,
        grid_w=8,
        palette_count=6,
    )
    truth = intended_output(grid)
    assert GEN.self_check(grid) == []
    assert GEN.SEMANTIC_WITNESSES["pair_plus_singleton"](grid)
    assert GEN.SEMANTIC_WITNESSES["vertical_exact_pair"](grid)
    assert GEN.SEMANTIC_WITNESSES["non_three_target_count"](grid)
    assert per_color_exact_pair_shortcut(grid) != truth
    assert row_or_column_shortcut(grid) != truth
    assert exactly_three_targets_shortcut(grid) != truth
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert rival(grid) != truth, name


def test_default_schedule_makes_every_cyclic_window_and_rotation_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(20):
            pairs = []
            for index in range(start, start + 4):
                grid = GEN.generate(700 + start, index, difficulty=band)
                pairs.append({"input": grid, "output": intended_output(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert GEN.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    query_index,
                )
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


def test_generation_and_semantic_helpers_do_not_mutate_inputs():
    grid = GEN.generate(101, 203, scene_pattern="comprehensive")
    original = deepcopy(grid)
    assert intended_output(grid) != grid
    for function in GEN.SEMANTIC_RIVALS.values():
        function(grid)
        assert grid == original
    for predicate in GEN.SEMANTIC_WITNESSES.values():
        predicate(grid)
        assert grid == original
    GEN.strict_canonical_like(grid)
    GEN.observe_overrides(grid)
    assert grid == original


def test_self_check_rejects_semantically_malformed_near_misses():
    good = GEN.generate(20, 1, scene_pattern="comprehensive")
    assert GEN.self_check(good) == []

    bad_color = deepcopy(good)
    bad_color[0][0] = 10
    assert GEN.self_check(bad_color)

    ragged = deepcopy(good)
    ragged[0].pop()
    assert GEN.self_check(ragged)

    no_targets = [[0 for _ in row] for row in good]
    assert GEN.self_check(no_targets)

    # Turn one target into adjacent matching cells: the selected rule would be
    # identity on that row, so the curriculum must reject it.
    adjacent = deepcopy(good)
    target_row = next(
        r
        for r, row in enumerate(adjacent)
        if len([v for v in row if v != 0]) == 2
        and len({v for v in row if v != 0}) == 1
    )
    cols = [c for c, value in enumerate(adjacent[target_row]) if value != 0]
    color = adjacent[target_row][cols[0]]
    adjacent[target_row] = [0] * len(adjacent[target_row])
    adjacent[target_row][0] = color
    adjacent[target_row][1] = color
    assert GEN.self_check(adjacent)


def test_pinned_profile_floor_has_cross_band_exact_and_envelope_support():
    canonical_profiles = {
        (8, 10, 6),
        (7, 11, 7),
        (9, 9, 7),
        (6, 12, 6),
        (8, 8, 7),
    }
    pooled_envelope = 0
    for band in ("easy", "medium", "hard"):
        exact = 0
        envelope = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            exact += profile in canonical_profiles
            envelope += (
                6 <= profile[0] <= 9
                and 8 <= profile[1] <= 12
                and 6 <= profile[2] <= 7
            )
        assert exact >= 1, band
        assert envelope >= 5, band
        pooled_envelope += envelope
    assert pooled_envelope >= 15
