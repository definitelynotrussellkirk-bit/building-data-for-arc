"""Regression and semantic-contract tests for 3e0aef964b9e."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import hashlib
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "3e0aef964b9e"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_pin_and_exact_axis_contract():
    assert GEN.RULE_HASH == "cac0ce22f2ed"
    assert GEN.VERSION == "3.1.0"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 3
    assert GEN.SCHEDULE_PROFILES == (0, 1, 2)
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_holes", "n_decoys"}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 13, "grid_w": 13, "n_holes": 1, "n_decoys": 1},
        {"grid_h": 24, "grid_w": 24, "n_holes": 6, "n_decoys": 2},
        {"grid_h": 15, "grid_w": 16, "n_holes": 4, "n_decoys": 2},
    ],
)
def test_exact_overrides_are_constructive_observable_and_lawful(band, overrides):
    grid = GEN.generate(181, 5, difficulty=band, **overrides)
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    analysis = GEN.analyze_grid(grid)
    assert len(analysis["missing"]) == overrides["n_holes"]
    assert len(analysis["target_components"]) - 1 == overrides["n_decoys"]
    assert GEN.rule_mirror(grid) != grid


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 12},
        {"grid_h": 25},
        {"grid_w": 12},
        {"grid_w": 25},
        {"n_holes": 0},
        {"n_holes": 7},
        {"n_decoys": 0},
        {"n_decoys": 3},
        {"grid_h": True},
        {"grid_w": 15.5},
        {"n_holes": "3"},
        {"unknown_axis": 1},
    ],
)
def test_invalid_controls_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


def test_all_canonical_variants_are_accepted_and_mirror_exact_authority():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 6
    for pair in pairs:
        source = deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_audit_impostor_is_rejected_and_connected_donors_are_generated():
    impostor = [[0, 1, 0], [0, 0, 2], [0, 0, 0]]
    assert GEN.self_check(impostor)
    assert GEN.strict_canonical_like(impostor)

    grids = [GEN.generate(47, index, difficulty="medium") for index in range(12)]
    witness = GEN.SEMANTIC_WITNESSES["connected_donor_component"]
    assert any(witness(grid) for grid in grids)
    assert any(not witness(grid) for grid in grids)


def test_three_profile_schedule_rebuts_each_declared_shortcut_in_every_band():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(101, index, difficulty=band) for index in range(3)]
        assert {GEN.schedule_profile(101, i, band) for i in range(3)} == {0, 1, 2}
        for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
            assert any(GEN.SEMANTIC_WITNESSES[witness_name](grid) for grid in grids), witness_name
            for rival_name in rival_names:
                rival = GEN.SEMANTIC_RIVALS[rival_name]
                assert any(rival(grid) != GEN.rule_mirror(grid) for grid in grids), rival_name


def test_every_cyclic_four_pair_window_and_rotation_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(9):
            pairs = [_pair(GEN.generate(700 + start, start + offset, difficulty=band))
                     for offset in range(4)]
            for query_index, query in enumerate(pairs):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


def test_default_distribution_covers_shapes_roles_layouts_and_counts():
    grids = [GEN.generate(313, index, difficulty="medium") for index in range(36)]
    analyses = [GEN.analyze_grid(grid) for grid in grids]

    assert {len(item["missing"]) for item in analyses} >= {1, 2, 3, 4, 5, 6}
    assert {len(item["target_components"]) - 1 for item in analyses} == {1, 2}
    assert any(item["target"] > item["donor"] for item in analyses)
    assert any(item["target"] < item["donor"] for item in analyses)
    assert any(GEN.SEMANTIC_WITNESSES["nonrectangular_candidate_hull"](g) for g in grids)
    assert any(GEN.SEMANTIC_WITNESSES["larger_decoy_than_candidate"](g) for g in grids)
    assert len({tuple(tuple(row) for row in g) for g in grids}) >= 34


def test_generation_helpers_and_rivals_are_deterministic_fresh_and_pure():
    global_state = random.getstate()
    for band in (None, "easy", "medium", "hard"):
        for index in range(9):
            first = GEN.generate(77, index, difficulty=band)
            after_first = random.getstate()
            second = GEN.generate(77, index, difficulty=band)
            after_second = random.getstate()
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert global_state == after_first == after_second
            assert GEN.self_check(first) == []

            original = deepcopy(first)
            GEN.rule_mirror(first)
            GEN.observe_overrides(first)
            GEN.analyze_grid(first)
            for rival in GEN.SEMANTIC_RIVALS.values():
                rival(first)
            for witness in GEN.SEMANTIC_WITNESSES.values():
                witness(first)
            assert first == original


def test_self_check_rejects_semantic_near_misses():
    grid = GEN.generate(29, 0, grid_h=15, grid_w=15, n_holes=4, n_decoys=2)
    info = GEN.analyze_grid(grid)

    missing_donor = deepcopy(grid)
    r, c = info["donor_cells"][0]
    missing_donor[r][c] = info["background"]
    assert GEN.self_check(missing_donor)

    filled_hole = deepcopy(grid)
    r, c = info["missing"][0]
    filled_hole[r][c] = info["target"]
    assert GEN.self_check(filled_hole)

    ambiguous = deepcopy(grid)
    # Recolor one full decoy as the donor; this destroys the two-role grammar.
    for r, c in info["target_components"][1]:
        ambiguous[r][c] = info["donor"]
    assert GEN.self_check(ambiguous)


def test_rule_clears_all_donors_and_fills_only_selected_gap():
    grid = GEN.generate(991, 2, grid_h=16, grid_w=16, n_holes=5, n_decoys=2)
    info = GEN.analyze_grid(grid)
    output = GEN.rule_mirror(grid)
    changed = {
        (r, c, grid[r][c], output[r][c])
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] != output[r][c]
    }
    expected = {
        (r, c, info["donor"], info["background"])
        for r, c in info["donor_cells"]
    } | {
        (r, c, info["background"], info["donor"])
        for r, c in info["missing"]
    }
    assert changed == expected


def _max_same_colour_four_component(grid):
    background = max(
        set(value for row in grid for value in row),
        key=lambda color: sum(value == color for row in grid for value in row),
    )
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != background
    }
    biggest = 0
    while remaining:
        start = min(remaining)
        color = grid[start[0]][start[1]]
        stack = [start]
        remaining.remove(start)
        size = 0
        while stack:
            row, col = stack.pop()
            size += 1
            for drow, dcol in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + drow, col + dcol)
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        biggest = max(biggest, size)
    return biggest


def test_default_schedule_reaches_canonical_sparse_four_connected_scale():
    grids = [GEN.generate(313, index, difficulty="medium") for index in range(12)]
    assert min(_max_same_colour_four_component(grid) for grid in grids) == 1


def test_each_profile_floor_band_has_an_exact_canonical_profile():
    canonical_profiles = {(13, 13, 3), (15, 15, 3), (16, 16, 3)}
    for band in ("easy", "medium", "hard"):
        profiles = set()
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = GEN.generate(seed, sample_index, difficulty=band)
            profiles.add(
                (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            )
        assert profiles & canonical_profiles, (band, profiles)
