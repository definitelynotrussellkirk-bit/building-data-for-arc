"""Regression and semantic-contract tests for 7355dc4aa5e5."""
from __future__ import annotations

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "7355dc4aa5e5"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"reviewed_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)

BANDS = (None, "easy", "medium", "hard")
CANONICAL_PROFILES = {
    (9, 9, 2, 9),
    (13, 13, 4, 8),
    (11, 11, 3, 7),
    (14, 14, 4, 8),
}


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _background(grid: list[list[int]]) -> int:
    colors = {value for row in grid for value in row if value != 1}
    assert len(colors) == 1
    return next(iter(colors))


def _observed(grid: list[list[int]]) -> dict[str, int]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_ones": sum(value == 1 for row in grid for value in row),
        "bg_color": _background(grid),
    }


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_pin_and_public_surface_are_narrow_and_exact():
    assert GEN.RULE_HASH == "6e7e8a6d6088"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_ones", "bg_color"}
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.MIN_STRICT_FRAC == 0.75
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "canonical_9_bg9_n2_interior",
        "canonical_13_bg8_n4_interior",
        "canonical_11_bg7_n3_edge",
        "rectangular_bg8_n3_edge_generalization",
    )


def test_selected_base_rule_text_matches_canonical_authority():
    root = find_root(__file__)
    canonical_path = root / "shared/data/canonical/puzzles.jsonl"
    canonical = None
    with canonical_path.open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                canonical = row
                break
    assert canonical is not None
    base_path = root / "shared/data/base/solutions/training/140c817e__7355dc4aa5e5.json"
    base = json.loads(base_path.read_text())
    assert base["racket_target"]["target_code"].strip() == canonical["program_solution"].strip()
    assert base["racket_target"]["raw_code"].strip() == canonical["program_solution"].strip()


def test_canonical_shortcuts_are_only_canonical_fitting_hypotheses():
    # These rivals are useful lesson competitors, but each is already refuted
    # by at least one authoritative canonical pair.  Advertising them as
    # canonical-fitting would make the semantic gate test the wrong contract.
    assert GEN.CANONICAL_SHORTCUTS == {}
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.SEMANTIC_RIVALS) == {
        "first_marker_only",
        "cross_without_diagonals",
        "background9_only",
        "skip_edge_markers",
    }


@pytest.mark.parametrize(
    "difficulty",
    ["__invalid_difficulty__", "", "EASY", 0, 0.5, True, False, [], {}],
)
def test_invalid_difficulty_fails_closed_at_both_public_entry_points(difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        GEN.schedule_profile(0, 0, difficulty=difficulty)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty=difficulty)


def test_difficulty_bands_influence_private_layout_without_changing_public_axes():
    grids = {
        band: GEN.generate(991, 1, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in grids.values()}) >= 2
    observed = [GEN.observe_overrides(grid) for grid in grids.values()]
    assert observed[0] == observed[1] == observed[2]


def test_default_exact_axes_are_not_pairwise_locked():
    observations = [GEN.observe_overrides(GEN.generate(seed, index, difficulty="medium"))
                    for seed in range(4) for index in range(4)]
    axes = tuple(GEN.AXES)
    for left_index, left in enumerate(axes):
        for right in axes[left_index + 1:]:
            pairs = {(row[left], row[right]) for row in observations}
            left_values = {pair[0] for pair in pairs}
            right_values = {pair[1] for pair in pairs}
            assert not (len(pairs) >= 3 and len(left_values) == len(right_values) == len(pairs)), (
                left, right, pairs
            )


@pytest.mark.parametrize(
    "pair",
    _canonical_pairs(),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_accepted_and_independent_mirror_matches(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
def test_four_sample_windows_cover_every_profile_and_remain_strict(band):
    expected = set(GEN.SCHEDULE_PROFILES)
    for start in range(8):
        profiles = {
            GEN.schedule_profile(1907, index, difficulty=band)
            for index in range(start, start + 4)
        }
        assert profiles == expected
        strict_count = 0
        for index in range(start, start + 4):
            grid = GEN.generate(1907, index, difficulty=band)
            assert GEN.self_check(grid) == []
            observed = _observed(grid)
            profile = GEN.schedule_profile(1907, index, difficulty=band)
            strict_errors = GEN.strict_canonical_like(grid)
            if profile == "rectangular_bg8_n3_edge_generalization":
                assert strict_errors
                assert observed == {
                    "grid_h": 14,
                    "grid_w": 9,
                    "n_ones": 3,
                    "bg_color": 8,
                }
            else:
                assert strict_errors == []
                strict_count += 1
                assert (
                    observed["grid_h"],
                    observed["grid_w"],
                    observed["n_ones"],
                    observed["bg_color"],
                ) in CANONICAL_PROFILES
            assert GEN.observe_overrides(grid) == observed
        assert strict_count == 3


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 7, "grid_w": 7, "n_ones": 2, "bg_color": 0},
        {"grid_h": 7, "grid_w": 7, "n_ones": 4, "bg_color": 4},
        {"grid_h": 16, "grid_w": 7, "n_ones": 4, "bg_color": 6},
        {"grid_h": 7, "grid_w": 16, "n_ones": 4, "bg_color": 7},
        {"grid_h": 16, "grid_w": 16, "n_ones": 4, "bg_color": 9},
    ],
)
def test_boundary_overrides_round_trip_in_every_band(band, requested):
    grid = GEN.generate(823, 3, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert _observed(grid) == requested
    assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"position_bias": "corners"},
        {"texture": "full_grid"},
        {"grid_h": 6},
        {"grid_h": 17},
        {"grid_w": 6},
        {"grid_w": 17},
        {"n_ones": 1},
        {"n_ones": 5},
        {"bg_color": 1},
        {"bg_color": 2},
        {"bg_color": 3},
        {"grid_h": True},
        {"grid_w": 9.0},
        {"n_ones": "2"},
        {"bg_color": False},
    ],
)
def test_invalid_or_retired_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", [], {}])
def test_invalid_seed_scalars_are_rejected_at_both_public_entry_points(seed):
    with pytest.raises((TypeError, ValueError), match="seed"):
        GEN.schedule_profile(seed, 0)
    with pytest.raises((TypeError, ValueError), match="seed"):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_invalid_sample_indexes_are_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


def test_self_check_rejects_declared_old_degenerates_and_minimal_impostors():
    background = [[9] * 9 for _ in range(9)]
    same_row = deepcopy(background)
    same_row[4][1] = same_row[4][7] = 1
    solid_2x2 = deepcopy(background)
    for row in (3, 4):
        for col in (3, 4):
            solid_2x2[row][col] = 1
    singleton = deepcopy(background)
    singleton[4][4] = 1

    assert GEN.self_check(background)
    assert GEN.self_check(same_row)
    assert GEN.self_check(solid_2x2)
    assert GEN.self_check(singleton)


@pytest.mark.parametrize("band", BANDS)
def test_semantic_witnesses_refute_named_rivals_and_lessons_are_rotation_safe(band):
    for start in range(8):
        grids = [GEN.generate(7331, start + offset, difficulty=band) for offset in range(4)]
        pairs = [_pair(grid) for grid in grids]

        assert sum(GEN.SEMANTIC_WITNESSES["edge_marker"](grid) for grid in grids) >= 2
        assert sum(GEN.SEMANTIC_WITNESSES["non_nine_background"](grid) for grid in grids) >= 3
        assert all(GEN.SEMANTIC_WITNESSES["multiple_markers"](grid) for grid in grids)
        assert all(GEN.SEMANTIC_WITNESSES["diagonal_stamp"](grid) for grid in grids)

        for grid, pair in zip(grids, pairs):
            intended = pair["output"]
            for witness, rival_names in GEN.WITNESS_RIVALS.items():
                if GEN.SEMANTIC_WITNESSES[witness](grid):
                    assert any(
                        GEN.SEMANTIC_RIVALS[name](grid) != intended
                        for name in rival_names
                    )

        for query_index in range(4):
            query = pairs[query_index]
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []


def test_generation_and_all_semantic_helpers_are_pure_and_deterministic():
    first = GEN.generate(412, 111, difficulty="hard")
    assert first == GEN.generate(412, 111, difficulty="hard")
    original = deepcopy(first)
    GEN.rule_mirror(first)
    GEN.observe_overrides(first)
    for witness in GEN.SEMANTIC_WITNESSES.values():
        witness(first)
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(first)
    assert first == original


@pytest.mark.parametrize(
    "bad_grid",
    [None, [], [[]], [[9], [9, 1]], [[True] * 9 for _ in range(9)]],
)
def test_malformed_grids_are_diagnostic_not_exceptions(bad_grid):
    assert GEN.self_check(bad_grid)
