"""Regression and semantic-contract tests for ARC generator aa0b08801e61."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "aa0b08801e61"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _signature(grid):
    return tuple(tuple(row) for row in grid)


def independent_symmetry_rule(grid):
    """Test-only authority mirror, intentionally independent of generator helpers."""
    height, width = len(grid), len(grid[0])
    output = [[0 for _ in range(width)] for _ in range(height)]
    seen = set()
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
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            top = min(rr for rr, _ in cells)
            left = min(cc for _, cc in cells)
            mask = {(rr - top, cc - left) for rr, cc in cells}
            max_row = max(rr for rr, _ in mask)
            max_col = max(cc for _, cc in mask)
            lr = {(rr, max_col - cc) for rr, cc in mask} == mask
            ud = {(max_row - rr, cc) for rr, cc in mask} == mask
            result_color = 8 if lr and ud else 2 if lr else 3 if ud else 4
            for rr, cc in cells:
                output[rr][cc] = result_color
    return output


def _pair(grid):
    return {"input": grid, "output": independent_symmetry_rule(grid)}


def test_rule_pin_small_axis_contract_and_all_canonical_pairs():
    assert GEN.RULE_HASH == "febf74c1fcfe"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.SCHEDULE_PROFILES == (
        "canonical_lr",
        "mask_trap",
        "canonical_ud",
        "mask_trap",
    )
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_objects"}

    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert independent_symmetry_rule(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 9, "grid_w": 12, "n_objects": 3},
        {"grid_h": 10, "grid_w": 14, "n_objects": 4},
        {"grid_h": 15, "grid_w": 18, "n_objects": 3},
    ],
)
def test_exact_overrides_are_constructive_observable_and_total(band, overrides):
    grid = GEN.generate(183, 7, difficulty=band, **overrides)
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
    assert independent_symmetry_rule(grid) == GEN.rule_mirror(grid)


@pytest.mark.parametrize(
    "seed,sample_index,difficulty,overrides",
    [
        (True, 0, None, {}),
        (1.5, 0, None, {}),
        (0, True, None, {}),
        (0, -1, None, {}),
        (0, 1.5, None, {}),
        (0, 0, "impossible", {}),
        (0, 0, None, {"grid_h": 8}),
        (0, 0, None, {"grid_h": 16}),
        (0, 0, None, {"grid_w": 11}),
        (0, 0, None, {"grid_w": 19}),
        (0, 0, None, {"n_objects": 2}),
        (0, 0, None, {"n_objects": 5}),
        (0, 0, None, {"grid_h": True}),
        (0, 0, None, {"grid_w": 14.0}),
        (0, 0, None, {"n_objects": "3"}),
        (0, 0, None, {"unknown_axis": 1}),
    ],
)
def test_invalid_controls_are_rejected(seed, sample_index, difficulty, overrides):
    with pytest.raises(ValueError):
        GEN.generate(seed, sample_index, difficulty=difficulty, **overrides)


def test_default_distribution_is_valid_diverse_deterministic_fresh_and_pure():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [GEN.generate(700_000 + band_index, index, difficulty=band)
                 for index in range(96)]
        assert all(GEN.self_check(grid, difficulty=band) == [] for grid in grids)
        assert len({_signature(grid) for grid in grids}) >= 90
        observed = [GEN.observe_overrides(grid) for grid in grids]
        assert {item["n_objects"] for item in observed} == {3, 4}
        assert len({item["grid_h"] for item in observed}) >= 6
        assert len({item["grid_w"] for item in observed}) >= 6
        exact_profiles = {
            (9, 12, 3),
            (9, 13, 3),
            (10, 13, 4),
            (10, 14, 4),
        }
        assert sum(
            (item["grid_h"], item["grid_w"], item["n_objects"])
            in exact_profiles
            for item in observed
        ) >= 40
        assert sum(GEN.strict_canonical_like(grid) == [] for grid in grids) >= 20

    random.seed(20261012)
    before = random.getstate()
    first = GEN.generate(777, 19, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(777, 19, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    pristine = deepcopy(second)
    GEN.rule_mirror(first)
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(first)
    for witness in GEN.SEMANTIC_WITNESSES.values():
        witness(first)
    assert first == pristine
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(777, 19, difficulty="hard") == second


def test_shape_banks_are_connected_and_match_declared_symmetry_classes():
    for class_name, bank in GEN.SHAPE_BANKS.items():
        assert bank, class_name
        for shape in bank:
            assert GEN._symmetry_class(shape) == class_name
            assert GEN._is_4_connected(shape)
            assert 3 <= len(shape) <= 9
            assert max(row for row, _ in shape) < 3
            assert max(col for _, col in shape) < 3


def test_shape_banks_partition_one_canonical_and_two_unique_novel_masks_per_class():
    assert sum(len(bank) for bank in GEN.SHAPE_BANKS.values()) == 12
    assert len(GEN._ALL_MASKS) == 12

    seen = set()
    for class_name, bank in GEN.SHAPE_BANKS.items():
        assert len(bank) == 3, class_name
        assert len(set(bank)) == 3, class_name
        assert bank[0] in GEN._CANONICAL_MASKS, class_name
        assert all(shape not in GEN._CANONICAL_MASKS for shape in bank[1:]), class_name
        assert seen.isdisjoint(bank), class_name
        seen.update(bank)


def test_ud_crown_is_a_novel_up_down_only_shortcut_counterexample():
    assert GEN._symmetry_class(GEN._UD_CROWN) == "ud"
    assert GEN._UD_CROWN not in GEN._CANONICAL_MASKS

    grid = [[0 for _ in range(3)] for _ in range(3)]
    for row, col in GEN._UD_CROWN:
        grid[row][col] = 7

    intended = GEN.rule_mirror(grid)
    shortcut = GEN.CANONICAL_SHORTCUTS["canonical_mask_lookup"](grid)
    assert {value for row in intended for value in row if value} == {3}
    assert {value for row in shortcut for value in row if value} == {4}
    assert intended != shortcut


def test_canonical_mask_shortcut_fits_canonical_but_generated_traps_refute_it():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"canonical_mask_lookup"}
    shortcut = GEN.CANONICAL_SHORTCUTS["canonical_mask_lookup"]
    for pair in canonical_pairs(TASK_ID, root=find_root(__file__)):
        assert shortcut(pair["input"]) == pair["output"]

    grids = [GEN.generate(424242, index, difficulty="medium") for index in range(20)]
    counterexamples = [
        grid for grid in grids if shortcut(grid) != GEN.rule_mirror(grid)
    ]
    assert counterexamples
    assert all(
        GEN.SEMANTIC_WITNESSES["canonical_mask_shortcut_counterexample"](grid)
        for grid in counterexamples
    )


def test_every_consecutive_three_demo_window_refutes_every_competitor():
    for band in ("easy", "medium", "hard"):
        pairs = [_pair(GEN.generate(998877, index, difficulty=band))
                 for index in range(24)]
        for start in range(len(pairs) - GEN.EXAMPLES_NEEDED):
            demos = pairs[start : start + GEN.EXAMPLES_NEEDED]
            query = pairs[start + GEN.EXAMPLES_NEEDED]
            assert GEN.lesson_identifiable(demos, query) == [], (band, start)
            for name, competitor in GEN.LESSON_COMPETITORS.items():
                assert any(
                    competitor(pair["input"]) != pair["output"]
                    for pair in demos
                ), (band, start, name)


def test_four_pair_lessons_survive_every_query_rotation():
    for band in ("easy", "medium", "hard"):
        for block in range(8):
            start = block * 4
            pairs = [_pair(GEN.generate(606060 + block, start + offset, difficulty=band))
                     for offset in range(4)]
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs)
                         if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == [], (
                    band,
                    block,
                    query_index,
                )


def test_each_witness_names_a_real_rival_disagreement():
    assert set(GEN.WITNESS_RIVALS) == set(GEN.SEMANTIC_WITNESSES)
    grids = [GEN.generate(123456, index) for index in range(20)]
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        firing = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert firing, witness_name
        for grid in firing:
            authority = GEN.rule_mirror(grid)
            assert any(
                GEN.SEMANTIC_RIVALS[name](grid) != authority
                for name in rival_names
            )


def test_self_check_rejects_malformed_and_targeted_impostors():
    for malformed in (
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 12 for _ in range(9)],
        [[10] * 12 for _ in range(9)],
    ):
        assert GEN.self_check(malformed)

    good = GEN.generate(314159, 4, grid_h=9, grid_w=12, n_objects=3)
    assert GEN.self_check(good) == []

    repeated_color = deepcopy(good)
    color_a, _ = GEN._components_nonzero(repeated_color)[0]
    _, cells_b = GEN._components_nonzero(repeated_color)[1]
    for row, col in cells_b:
        repeated_color[row][col] = color_a
    assert GEN.self_check(repeated_color)

    too_small = [[0 for _ in range(12)] for _ in range(9)]
    too_small[0][0] = 1
    too_small[0][6] = 2
    too_small[8][11] = 3
    assert GEN.self_check(too_small)

    oversized = deepcopy(good)
    color, cells = GEN._components_nonzero(oversized)[0]
    row = min(r for r, _ in cells)
    col = min(c for _, c in cells)
    target = None
    for candidate in ((row + 3, col), (row, col + 3)):
        rr, cc = candidate
        if 0 <= rr < len(oversized) and 0 <= cc < len(oversized[0]):
            oversized[rr][cc] = color
            target = candidate
            break
    assert target is not None
    assert GEN.self_check(oversized)

    wrong_meta = {"overrides": {"grid_h": 10, "grid_w": 12, "n_objects": 3}}
    assert GEN.self_check(good, meta=wrong_meta)


def test_pinned_profile_floor_has_exact_canonical_support_in_every_band():
    """Mirror the native gate's pinned off-diagonal 20-draw census."""
    exact_profiles = {
        (9, 12, 4),
        (9, 13, 4),
        (10, 13, 5),
        (10, 14, 5),
    }
    for band in ("easy", "medium", "hard"):
        exact = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            exact += profile in exact_profiles
        assert exact >= 5, (band, exact)
