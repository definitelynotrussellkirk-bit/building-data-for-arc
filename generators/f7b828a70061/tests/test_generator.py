"""Portable regressions for marker-rotation-crop sampler repair."""
from __future__ import annotations

from collections import deque

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "f7b828a70061"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK, root=ROOT)
CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
CANONICAL_PROFILES = {
    (7, 9, 4),
    (8, 10, 4),
    (7, 10, 3),
    (8, 9, 3),
    (9, 11, 4),
}


def _components(grid):
    cleaned = [list(row) for row in grid]
    cleaned[0][0] = 0
    seen = set()
    result = []
    for sr, row in enumerate(cleaned):
        for sc, value in enumerate(row):
            if value == 0 or (sr, sc) in seen:
                continue
            todo = deque([(sr, sc)])
            seen.add((sr, sc))
            cells = []
            while todo:
                r, c = todo.popleft()
                cells.append((r, c))
                for dr, dc in CARD:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < len(cleaned) and 0 <= nc < len(cleaned[0])
                            and cleaned[nr][nc] != 0 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append(cells)
    return cleaned, result


def _rotate(grid, command):
    if command == 2:
        return [row[:] for row in grid]
    if command == 3:
        return [list(row) for row in zip(*grid[::-1])]
    if command == 4:
        return [row[::-1] for row in grid[::-1]]
    return [list(row) for row in zip(*grid)][::-1]


def intended_output(grid):
    cleaned, components = _components(grid)
    main = min(components, key=lambda cells: (-len(cells), min(cells)))
    top = min(r for r, _ in main)
    bottom = max(r for r, _ in main)
    left = min(c for _, c in main)
    right = max(c for _, c in main)
    crop = [row[left:right + 1] for row in cleaned[top:bottom + 1]]
    return _rotate(crop, grid[0][0])


def largest_bbox_area_output(grid):
    cleaned, components = _components(grid)
    def key(cells):
        top = min(r for r, _ in cells)
        bottom = max(r for r, _ in cells)
        left = min(c for _, c in cells)
        right = max(c for _, c in cells)
        return (-((bottom - top + 1) * (right - left + 1)), min(cells))
    chosen = min(components, key=key)
    top = min(r for r, _ in chosen)
    bottom = max(r for r, _ in chosen)
    left = min(c for _, c in chosen)
    right = max(c for _, c in chosen)
    crop = [row[left:right + 1] for row in cleaned[top:bottom + 1]]
    return _rotate(crop, grid[0][0])


def _pair(grid):
    return {"input": grid, "output": intended_output(grid)}


def test_canonical_inputs_and_outputs_remain_authoritative():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_joint_exact_controls_are_observable_in_every_band(band):
    requested = {
        "grid_h": 7,
        "grid_w": 9,
        "command": 5,
        "main_size": 8,
        "main_shape": "stair",
        "palette_size": 2,
    }
    grid = GEN.generate(17, 9, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert intended_output(grid) != largest_bbox_area_output(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_cycles_all_canonical_profiles(band):
    observed = set()
    for index in range(20):
        grid = GEN.generate(700 + index, index, difficulty=band)
        assert grid == GEN.generate(700 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        signature = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        assert signature in CANONICAL_PROFILES
        observed.add(signature)
        assert intended_output(grid) != largest_bbox_area_output(grid)
    assert observed == CANONICAL_PROFILES


@pytest.mark.parametrize("seed,index,difficulty", [
    (True, 0, None), (1.5, 0, None), ("1", 0, None),
    (1, True, None), (1, -1, None), (1, 1.5, None),
    (1, 0, True), (1, 0, "expert"),
])
def test_invalid_call_scalars_are_rejected(seed, index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, index, difficulty=difficulty)


@pytest.mark.parametrize("axis,value", [
    ("grid_h", True), ("grid_h", 6), ("grid_h", 10),
    ("grid_w", 9.0), ("grid_w", 8), ("grid_w", 12),
    ("command", "2"), ("command", 1), ("command", 6),
    ("main_size", False), ("main_size", 5), ("main_size", 9),
    ("main_shape", 1), ("main_shape", "line"),
    ("palette_size", 1.0), ("palette_size", 0), ("palette_size", 3),
    ("distractor_count", 1),
    ("texture", "warm"), ("position_bias", "center"), ("typo", 1),
])
def test_invalid_or_retired_controls_fail_explicitly(axis, value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **{axis: value})


def test_none_controls_preserve_default_draw():
    axes = ["grid_h", "grid_w", "command", "main_size", "main_shape",
            "palette_size"]
    assert GEN.generate(19, 3, difficulty="hard") == GEN.generate(
        19, 3, difficulty="hard", **dict.fromkeys(axes)
    )


def test_declared_shortcut_fits_canonical_pairs_and_generated_witnesses_refute_it():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    rival = GEN.CANONICAL_SHORTCUTS["largest_bbox_area"]
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)
    for index in range(16):
        grid = GEN.generate(81, index)
        assert GEN.SEMANTIC_WITNESSES["bbox_area_tie"](grid)
        assert rival(grid) == largest_bbox_area_output(grid)
        assert rival(grid) != intended_output(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_query_rotation_retains_command_mapping_and_shortcut_refutation(band):
    assert GEN.EXAMPLES_NEEDED == 7
    for start in range(8):
        pairs = [_pair(GEN.generate(42, start + offset, difficulty=band)) for offset in range(8)]
        for held_out in range(8):
            query = pairs[held_out]
            demos = [pair for i, pair in enumerate(pairs) if i != held_out]
            assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("bad", [
    None,
    [],
    [[]],
    [[0] * 9 for _ in range(7)],
    [[2] * 9 for _ in range(7)],
    [[0] * 9 for _ in range(7)],
])
def test_validator_rejects_malformed_and_minimal_impostors(bad):
    if isinstance(bad, list) and len(bad) == 7 and bad and bad[0] == [0] * 9:
        bad = [row[:] for row in bad]
        bad[0][0] = 2
        bad[3][3] = bad[3][4] = bad[4][3] = bad[4][4] = 6
    assert GEN.self_check(bad)
