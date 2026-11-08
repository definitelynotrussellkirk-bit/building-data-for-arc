from __future__ import annotations

import copy
import importlib
from collections import Counter

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "2b83f40cf6d9"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _counts(grid):
    return Counter(value for row in grid for value in row if value != 0)


def _has_aligned_pair(grid):
    positions: dict[int, list[tuple[int, int]]] = {}
    for row_index, row in enumerate(grid):
        for col_index, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((row_index, col_index))
    return any(
        len(points) == 2
        and (points[0][0] == points[1][0] or points[0][1] == points[1][1])
        for points in positions.values()
    )


def test_rule_hash_python_oracle_and_canonical_shortcut_are_source_bound():
    assert GEN.RULE_HASH == "cbbc66a297e5"
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        assert GEN.self_check(grid) == []
        assert GEN._intended_output(grid) == pair["output"]
        assert GEN.SEMANTIC_RIVALS["diagonal_pairs_only"](grid) == pair["output"]
        assert grid == pair["input"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "expected",
    [
        {"grid_h": 7, "grid_w": 8, "n_colors": 2},
        {"grid_h": 7, "grid_w": 20, "n_colors": 3},
        {"grid_h": 18, "grid_w": 8, "n_colors": 3},
        {"grid_h": 18, "grid_w": 20, "n_colors": 2},
    ],
)
def test_every_override_boundary_is_realized_exactly(difficulty, expected):
    grid = GEN.generate(17, 11, difficulty=difficulty, **expected)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == expected
    assert set(_counts(grid).values()) == {2}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"grid_h": 6},
        {"grid_h": 19},
        {"grid_w": 7},
        {"grid_w": 21},
        {"n_colors": 1},
        {"n_colors": 4},
        {"n_colors": 2.0},
        {"grid_h": True},
    ],
)
def test_invalid_or_unknown_overrides_reject_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(3, 5, **kwargs)


def test_self_check_rejects_the_reproduced_one_color_contract_defect():
    grid = [[0] * 8 for _ in range(7)]
    grid[1][1] = 4
    grid[5][6] = 4
    errors = GEN.self_check(grid)
    assert errors
    assert any("2..3" in error or "2-3" in error for error in errors)


def test_self_check_rejects_adjacent_markers_and_malformed_cells_without_raising():
    adjacent = [[0] * 8 for _ in range(7)]
    adjacent[1][1] = adjacent[1][2] = 2
    adjacent[4][1] = adjacent[5][5] = 3
    assert GEN.self_check(adjacent)
    assert GEN.self_check([[False] * 8 for _ in range(7)])
    assert GEN.self_check([[0] * 8, [0] * 7])
    assert GEN.self_check(None)


def test_semantic_schedule_refutes_the_diagonal_only_shortcut_in_every_rotation():
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    for start in range(GEN.LESSON_SCHEDULE_PERIOD):
        grids = [GEN.generate(101, start + offset, grid_h=10, grid_w=12, n_colors=3)
                 for offset in range(4)]
        aligned = [_has_aligned_pair(grid) for grid in grids]
        assert sum(aligned) == 2
        for query_index in range(4):
            demos = [
                {"input": grid, "output": GEN._intended_output(grid)}
                for index, grid in enumerate(grids)
                if index != query_index
            ]
            query = {"input": grids[query_index]}
            assert GEN.lesson_identifiable(demos, query) == []


def test_aligned_pair_is_an_exact_rival_witness():
    grid = GEN.generate(9, 1, grid_h=7, grid_w=8, n_colors=2)
    assert _has_aligned_pair(grid)
    assert GEN.SEMANTIC_WITNESSES["aligned_pair"](grid)
    assert GEN.SEMANTIC_RIVALS["diagonal_pairs_only"](grid) != GEN._intended_output(grid)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_distribution_is_deterministic_lawful_and_covers_both_color_counts(difficulty):
    observations = set()
    for index in range(96):
        grid = GEN.generate(2000 + index, index, difficulty=difficulty)
        assert grid == GEN.generate(2000 + index, index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        observations.add(GEN.observe_overrides(grid)["n_colors"])
    assert observations == {2, 3}


def _profile(grid):
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


def _profile_floor_seed(band, index):
    import hashlib

    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def test_each_difficulty_band_has_pinned_canonical_profile_support():
    canonical_profiles = {
        _profile(pair["input"])
        for pair in canonical_pairs(TASK_ID, root=find_root(__file__))
    }
    assert canonical_profiles
    for band in ("easy", "medium", "hard"):
        observed = []
        for index in range(20):
            seed = _profile_floor_seed(band, index)
            sample_index = seed % 7919 + index
            observed.append(_profile(GEN.generate(seed, sample_index, difficulty=band)))
        assert canonical_profiles.intersection(observed), (band, observed)


def test_pinned_census_has_at_least_twenty_five_percent_canonical_envelope():
    canonical_profiles = [
        _profile(pair["input"])
        for pair in canonical_pairs(TASK_ID, root=find_root(__file__))
    ]
    h_lo, h_hi = min(p[0] for p in canonical_profiles), max(p[0] for p in canonical_profiles)
    w_lo, w_hi = min(p[1] for p in canonical_profiles), max(p[1] for p in canonical_profiles)
    p_lo, p_hi = min(p[2] for p in canonical_profiles), max(p[2] for p in canonical_profiles)
    envelope_hits = 0
    draws = 0
    for band in ("easy", "medium", "hard"):
        for index in range(20):
            seed = _profile_floor_seed(band, index)
            sample_index = seed % 7919 + index
            profile = _profile(GEN.generate(seed, sample_index, difficulty=band))
            draws += 1
            envelope_hits += int(
                h_lo <= profile[0] <= h_hi
                and w_lo <= profile[1] <= w_hi
                and p_lo <= profile[2] <= p_hi
            )
    assert envelope_hits / draws >= 0.25, (envelope_hits, draws)


def test_canonical_anchor_records_keyed_axis_draw_provenance(monkeypatch):
    import random

    class RecordingContext:
        def __init__(self):
            self.choice_names = []

        def draw_choice(self, name, options):
            self.choice_names.append(name)
            return list(options)[0]

        def draw_rng(self, name):
            return random.Random(0)

        def draw_distinct_colors(self, name, *, n, exclude=()):
            return [color for color in range(1, 10) if color not in exclude][:n]

    context = RecordingContext()
    monkeypatch.setattr(GEN, "gen_ctx", lambda **kwargs: context)
    grid = GEN.generate(1, 0, difficulty="hard")
    assert GEN.self_check(grid) == []
    assert set(context.choice_names) >= {"grid_h", "grid_w", "n_colors"}


def test_canonical_profile_anchors_cover_every_semantic_layout_residue(monkeypatch):
    # Force non-anchor draws outside the canonical profile set so this probes
    # the joint support of the two deterministic schedules, not random luck.
    fallback = {"grid_h": 18, "grid_w": 20, "n_colors": 2}
    monkeypatch.setattr(
        GEN,
        "_weighted_int",
        lambda ctx, name, lo, hi, favored: fallback[name],
    )
    canonical_profiles = {
        (10, 10, 4),
        (10, 12, 4),
        (11, 11, 4),
        (11, 12, 4),
        (12, 13, 4),
    }
    anchors = []
    for sample_index in range(12):
        grid = GEN.generate(701, sample_index, difficulty="medium")
        if _profile(grid) in canonical_profiles:
            anchors.append((sample_index, _has_aligned_pair(grid)))

    assert {sample_index % GEN.LESSON_SCHEDULE_PERIOD for sample_index, _ in anchors} == {
        0,
        1,
        2,
        3,
    }
    assert {has_aligned for _, has_aligned in anchors} == {False, True}
