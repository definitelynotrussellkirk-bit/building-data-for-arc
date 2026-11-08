"""Focused contract tests for the reviewed 961add4a2688 generator."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "961add4a2688"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

PROFILES = {
    "canonical_8x9_p6": (8, 9, 6),
    "canonical_9x10_p8": (9, 10, 8),
    "canonical_9x11_p8": (9, 11, 8),
    "canonical_10x10_p6": (10, 10, 6),
}


def _frame(grid):
    cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8}
    assert cells
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    border = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    assert cells == border
    return r0, c0, r1, c1


def independent_rule(grid):
    r0, c0, r1, c1 = _frame(grid)
    out = [[0 for _ in row] for row in grid]
    for r, c in {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)
                 if r in (r0, r1) or c in (c0, c1)}:
        out[r][c] = 8
    for c in range(c0 + 1, c1):
        values = [grid[r][c] for r in range(r0 + 1, r1) if grid[r][c] != 0]
        for offset, value in enumerate(values):
            out[r0 + 1 + offset][c] = value
    return out


def _pair(grid):
    return {"input": grid, "output": independent_rule(grid)}


def test_metadata_pins_small_observable_contract():
    assert GEN.RULE_HASH == "9c6db5aba1ba"
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert GEN.SCHEDULE_PROFILES == (0, 1, 2, 3)
    assert set(GEN.AXES) == {"scene_profile", "n_markers", "column_pattern", "frame_position"}
    assert set(GEN.LESSON_COMPETITORS) == {
        "sort_each_column_ascending",
        "sort_each_column_descending",
        "pack_each_column_down",
        "keep_only_first_marker",
        "leave_markers_in_place",
    }


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("scene_profile", sorted(PROFILES))
@pytest.mark.parametrize("n_markers", [6, 7])
@pytest.mark.parametrize("column_pattern", ["separate", "stacked", "mixed"])
@pytest.mark.parametrize("frame_position", ["top_left", "center", "bottom_right"])
def test_exact_overrides_are_constructive_and_observable(
    band, scene_profile, n_markers, column_pattern, frame_position
):
    grid = GEN.generate(
        911,
        17,
        difficulty=band,
        scene_profile=scene_profile,
        n_markers=n_markers,
        column_pattern=column_pattern,
        frame_position=frame_position,
    )
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == {
        "scene_profile": scene_profile,
        "n_markers": n_markers,
        "column_pattern": column_pattern,
        "frame_position": frame_position,
    }
    h, w, palette = PROFILES[scene_profile]
    assert (len(grid), len(grid[0]), len({v for row in grid for v in row})) == (h, w, palette)
    assert independent_rule(grid) == GEN.rule_mirror(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"scene_profile": "unknown"},
        {"scene_profile": 1},
        {"n_markers": 5},
        {"n_markers": 8},
        {"n_markers": True},
        {"column_pattern": "random"},
        {"column_pattern": 3},
        {"frame_position": "random"},
        {"frame_position": 2},
        {"unknown_axis": 1},
        {"difficulty": "impossible"},
    ],
)
def test_invalid_controls_are_rejected(kwargs):
    kwargs = dict(kwargs)
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty, **kwargs)


def test_canonical_inputs_are_accepted_and_python_mirror_matches_authority():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        before = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert independent_rule(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_schedule_hits_every_canonical_profile_and_semantic_pattern(band):
    grids = [GEN.generate(317, index, difficulty=band) for index in range(4)]
    observed = [GEN.observe_overrides(grid) for grid in grids]
    assert [GEN.schedule_profile(317, index, band) for index in range(4)] == [0, 1, 2, 3]
    assert {item["scene_profile"] for item in observed} == set(PROFILES)
    assert {item["column_pattern"] for item in observed} == {"separate", "stacked", "mixed"}
    assert {item["frame_position"] for item in observed} == {"top_left", "center", "bottom_right"}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_five_pair_window_and_query_rotation_is_identifiable(band):
    for start in range(12):
        pairs = [
            _pair(GEN.generate(1207 + start, start + offset, difficulty=band))
            for offset in range(5)
        ]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(item["input"]) != item["output"] for item in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_witnesses_are_real_and_bound_to_their_rivals(band):
    grids = [GEN.generate(97, index, difficulty=band) for index in range(8)]
    for witness_name, rivals in GEN.WITNESS_RIVALS.items():
        witness_grids = [g for g in grids if GEN.SEMANTIC_WITNESSES[witness_name](g)]
        assert witness_grids, witness_name
        for rival_name in rivals:
            assert any(
                GEN.LESSON_COMPETITORS[rival_name](g) != independent_rule(g)
                for g in witness_grids
            ), (witness_name, rival_name)


def test_self_check_rejects_structural_near_misses():
    good = GEN.generate(
        5,
        0,
        scene_profile="canonical_9x10_p8",
        n_markers=7,
        column_pattern="mixed",
        frame_position="center",
    )
    assert GEN.self_check(good) == []
    r0, c0, r1, c1 = _frame(good)

    broken_frame = deepcopy(good)
    broken_frame[r0][c0 + 1] = 0
    assert GEN.self_check(broken_frame)

    extra_frame_color = deepcopy(good)
    extra_frame_color[0][0] = 8
    assert GEN.self_check(extra_frame_color)

    outside_marker = deepcopy(good)
    target = next(
        (r, c)
        for r in range(len(good))
        for c in range(len(good[0]))
        if not (r0 <= r <= r1 and c0 <= c <= c1) and good[r][c] == 0
    )
    outside_marker[target[0]][target[1]] = 4
    assert GEN.self_check(outside_marker)

    identity = deepcopy(good)
    for c in range(c0 + 1, c1):
        vals = [identity[r][c] for r in range(r0 + 1, r1) if identity[r][c] != 0]
        for r in range(r0 + 1, r1):
            identity[r][c] = 0
        for offset, value in enumerate(vals):
            identity[r0 + 1 + offset][c] = value
    assert GEN.self_check(identity)

    assert GEN.self_check([])
    assert GEN.self_check([[0, 0], [0]])
    assert GEN.self_check([["0"]])


def test_helpers_are_deterministic_fresh_and_pure():
    for band in (None, "easy", "medium", "hard"):
        for index in range(16):
            first = GEN.generate(77, index, difficulty=band)
            second = GEN.generate(77, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            before = deepcopy(first)
            assert GEN.rule_mirror(first) == independent_rule(first)
            for fn in GEN.SEMANTIC_RIVALS.values():
                fn(first)
                assert first == before
            for fn in GEN.SEMANTIC_WITNESSES.values():
                fn(first)
                assert first == before


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_pinned_profile_floor_has_exact_support_in_every_band(band):
    exact = 0
    for index in range(20):
        digest = hashlib.sha256(f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()).hexdigest()
        seed = int(digest[:12], 16)
        grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
        profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        exact += profile in set(PROFILES.values())
    assert exact == 20


def test_default_distribution_is_not_a_four_grid_replay():
    grids = [GEN.generate(314159, index, difficulty="medium") for index in range(80)]
    frozen = {tuple(tuple(row) for row in grid) for grid in grids}
    assert len(frozen) >= 72
