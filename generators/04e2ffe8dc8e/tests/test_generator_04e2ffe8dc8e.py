"""Focused regressions for the smallest-green generator."""
from __future__ import annotations

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "04e2ffe8dc8e"
ROOT = find_root(__file__)
mod, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def test_rule_hash_version_and_axis_surface_are_pinned():
    assert mod.VERSION == "1.3.0"
    assert mod.RULE_HASH == "c67640298f12"
    assert set(mod.AXES) == {"grid_h", "grid_w", "small_size", "n_large", "texture"}


def test_all_canonical_inputs_pass_and_python_mirror_matches_outputs():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert mod.self_check(pair["input"]) == []
        assert mod._rule_mirror(pair["input"]) == pair["output"]


def _global_smallest_rule(grid):
    components = []
    seen = set()
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((len(cells), min(cells), cells))
    _, _, target = min(components)
    output = [list(row) for row in grid]
    for row, col in target:
        output[row][col] = 6
    return output


def test_unknown_overrides_and_impossible_decoy_reject_loudly():
    import pytest

    with pytest.raises(ValueError, match="unsupported override"):
        mod.generate(1, 0, invented_axis=True)
    with pytest.raises(ValueError, match="decoy.*small_size=1"):
        mod.generate(1, 0, texture="decoy", small_size=1)


def test_every_three_sample_window_refutes_global_smallest_rival():
    for seed in range(8):
        for start in range(4):
            grids = [mod.generate(seed, start + offset, difficulty="medium") for offset in range(3)]
            assert any(mod._rule_mirror(grid) != _global_smallest_rule(grid) for grid in grids)


def test_exact_axes_are_observable_and_real_decoy_is_smaller():
    grid = mod.generate(
        91,
        17,
        difficulty="hard",
        grid_h=14,
        grid_w=16,
        small_size=2,
        n_large=4,
        texture="decoy",
    )
    assert mod.self_check(grid) == []
    assert mod.observe_overrides(grid) == {
        "grid_h": 14,
        "grid_w": 16,
        "small_size": 2,
        "n_large": 4,
        "texture": "decoy",
    }
    assert sum(value not in (0, 3) for row in grid for value in row) == 1


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    import copy
    import random

    random.seed(78123)
    state = random.getstate()
    first = mod.generate(77, 31, difficulty="hard")
    pristine = copy.deepcopy(first)
    second = mod.generate(77, 31, difficulty="hard")
    assert state == random.getstate()
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert mod.generate(77, 31, difficulty="hard") == pristine
