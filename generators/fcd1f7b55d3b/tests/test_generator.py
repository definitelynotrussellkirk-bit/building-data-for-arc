"""Regression tests for the diagonal-corner rectangle-fill generator."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from itertools import combinations
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "fcd1f7b55d3b"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def intended_output(grid):
    """Independent mirror: exactly-two colors paint their bbox on blank output."""
    height = len(grid)
    width = len(grid[0])
    out = [[0] * width for _ in range(height)]
    by_color = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                by_color.setdefault(value, []).append((row, col))
    for color, cells in by_color.items():
        if len(cells) != 2:
            continue
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        for row in range(min(rows), max(rows) + 1):
            for col in range(min(cols), max(cols) + 1):
                out[row][col] = color
    return out


def copy_then_fill_shortcut(grid):
    out = deepcopy(grid)
    by_color = _by_color(grid)
    for color, cells in by_color.items():
        if len(cells) == 2:
            _paint_bbox(out, color, cells)
    return out


def all_colors_bbox_shortcut(grid):
    out = [[0] * len(grid[0]) for _ in grid]
    for color, cells in _by_color(grid).items():
        _paint_bbox(out, color, cells)
    return out


def backslash_only_shortcut(grid):
    out = [[0] * len(grid[0]) for _ in grid]
    for color, cells in _by_color(grid).items():
        if len(cells) != 2:
            continue
        (r0, c0), (r1, c1) = sorted(cells)
        if c0 < c1:
            _paint_bbox(out, color, cells)
    return out


def exactly_two_pairs_shortcut(grid):
    pair_count = sum(len(cells) == 2 for cells in _by_color(grid).values())
    return intended_output(grid) if pair_count == 2 else [[0] * len(grid[0]) for _ in grid]


def _by_color(grid):
    result = {}
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value:
                result.setdefault(value, []).append((row, col))
    return result


def _paint_bbox(out, color, cells):
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    for row in range(min(rows), max(rows) + 1):
        for col in range(min(cols), max(cols) + 1):
            out[row][col] = color


def _pair_bboxes(grid):
    boxes = []
    for color, cells in _by_color(grid).items():
        if len(cells) != 2:
            continue
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        boxes.append((color, min(rows), min(cols), max(rows), max(cols)))
    return boxes


def _overlap(first, second):
    _, ar0, ac0, ar1, ac1 = first
    _, br0, bc0, br1, bc1 = second
    return not (ar1 < br0 or br1 < ar0 or ac1 < bc0 or bc1 < ac0)


def test_rule_pin_and_small_exact_axis_contract():
    assert GEN.RULE_HASH == "d0be8e83eb5b"
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.EXAMPLES_NEEDED == 4
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "n_pairs",
        "n_decoys",
        "orientation",
    }


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h,grid_w", [(7, 8), (14, 15)])
@pytest.mark.parametrize("n_pairs", [2, 3, 4])
@pytest.mark.parametrize("n_decoys", [0, 1])
@pytest.mark.parametrize("orientation", ["backslash", "slash"])
def test_every_joint_exact_override_is_constructive_and_observable(
    band, grid_h, grid_w, n_pairs, n_decoys, orientation
):
    grid = GEN.generate(
        91,
        7,
        difficulty=band,
        grid_h=grid_h,
        grid_w=grid_w,
        n_pairs=n_pairs,
        n_decoys=n_decoys,
        orientation=orientation,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_pairs": n_pairs,
        "n_decoys": n_decoys,
        "orientation": orientation,
    }
    boxes = _pair_bboxes(grid)
    assert len(boxes) == n_pairs
    assert all(not _overlap(a, b) for a, b in combinations(boxes, 2))
    assert intended_output(grid) != grid


@pytest.mark.parametrize(
    "key,value",
    [
        ("grid_h", 6),
        ("grid_h", 15),
        ("grid_w", 7),
        ("grid_w", 16),
        ("n_pairs", 1),
        ("n_pairs", 5),
        ("n_decoys", -1),
        ("n_decoys", 2),
        ("orientation", "mixed"),
        ("typo_axis", 1),
        ("grid_h", True),
        ("grid_w", 8.5),
        ("orientation", 1),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
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
        "copy_then_fill": copy_then_fill_shortcut,
        "all_colors_bbox": all_colors_bbox_shortcut,
        "backslash_only": backslash_only_shortcut,
        "exactly_two_pairs": exactly_two_pairs_shortcut,
    }
    assert set(GEN.CANONICAL_SHORTCUTS) == set(shortcuts)
    for name, shortcut in shortcuts.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


def test_scheduled_counterexamples_refute_all_canonical_fitting_shortcuts():
    grids = [GEN.generate(44, index, difficulty="hard") for index in range(4)]
    assert all(GEN.self_check(grid) == [] for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["decoy_filter"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["slash_orientation"](grid) for grid in grids)
    assert any(GEN.SEMANTIC_WITNESSES["more_than_two_pairs"](grid) for grid in grids)
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert any(rival(grid) != intended_output(grid) for grid in grids), name


def test_default_schedule_makes_every_cyclic_window_and_rotation_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            pairs = []
            for index in range(start, start + 5):
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
    grid = GEN.generate(101, 2, difficulty="hard")
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
    good = GEN.generate(20, 2, difficulty="hard")
    assert GEN.self_check(good) == []

    bad_color = deepcopy(good)
    bad_color[0][0] = 10
    assert GEN.self_check(bad_color)

    ragged = deepcopy(good)
    ragged[0].pop()
    assert GEN.self_check(ragged)

    one_pair = [[0 for _ in row] for row in good]
    pair_color, cells = next(
        (color, cells) for color, cells in _by_color(good).items() if len(cells) == 2
    )
    for row, col in cells:
        one_pair[row][col] = pair_color
    assert GEN.self_check(one_pair)

    collinear = deepcopy(good)
    color, cells = next(
        (color, cells) for color, cells in _by_color(collinear).items() if len(cells) == 2
    )
    for row, col in cells:
        collinear[row][col] = 0
    row = cells[0][0]
    collinear[row][0] = color
    collinear[row][3] = color
    assert GEN.self_check(collinear)

    overlapping = deepcopy(good)
    pair_rows = [(color, cells) for color, cells in _by_color(overlapping).items() if len(cells) == 2]
    (color_a, cells_a), (color_b, cells_b) = pair_rows[:2]
    for row, col in cells_b:
        overlapping[row][col] = 0
    rows = sorted({row for row, _ in cells_a})
    cols = sorted({col for _, col in cells_a})
    overlapping[rows[0]][cols[-1]] = color_b
    overlapping[rows[-1]][cols[0]] = color_b
    assert GEN.self_check(overlapping)


def test_default_draws_are_deterministic_lawful_and_cover_all_profiles():
    for band in ("easy", "medium", "hard"):
        profiles = Counter()
        for index in range(40):
            grid = GEN.generate(1234, index, difficulty=band)
            assert grid == GEN.generate(1234, index, difficulty=band)
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            profiles[(observed["n_pairs"], observed["n_decoys"], observed["orientation"])] += 1
        assert profiles[(2, 0, "backslash")] > 0
        assert profiles[(2, 0, "slash")] > 0
        assert any(n_pairs > 2 and n_decoys == 1 for n_pairs, n_decoys, _ in profiles)
        assert any(orientation == "slash" and n_decoys == 1 for _, n_decoys, orientation in profiles)


def test_pinned_profile_floor_has_cross_band_exact_and_envelope_support():
    canonical_profiles = {
        (8, 9, 3),
        (9, 10, 3),
        (7, 8, 3),
        (9, 9, 3),
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
            profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            exact += profile in canonical_profiles
            envelope += (
                7 <= profile[0] <= 9
                and 8 <= profile[1] <= 10
                and profile[2] == 3
            )
        assert exact >= 1, band
        assert envelope >= 4, band
        pooled_envelope += envelope
    assert pooled_envelope >= 12


def test_retained_counterexamples_replay_against_independent_oracle():
    path = HOME / "counterexamples" / "canonical_shortcuts.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    rivals = {
        "copy_then_fill": copy_then_fill_shortcut,
        "all_colors_bbox": all_colors_bbox_shortcut,
        "backslash_only": backslash_only_shortcut,
        "exactly_two_pairs": exactly_two_pairs_shortcut,
    }
    assert payload["task_id"] == TASK_ID
    assert payload["generator_sha256"] == hashlib.sha256(
        (HOME / "generator.py").read_bytes()
    ).hexdigest()
    for record in payload["records"]:
        grid = record["input"]
        expected = intended_output(grid)
        assert record["authority_output"] == expected
        assert GEN.self_check(grid) == []
        for name in record["refutes"]:
            assert rivals[name](grid) != expected
