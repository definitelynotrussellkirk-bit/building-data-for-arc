from __future__ import annotations

import copy
import importlib
import random

import pytest
from reviewer_support import canonical_pairs, find_root

gen = importlib.import_module("puzzle_generators.per_puzzle.5ee8de1860a7.generator")
ROOT = find_root(__file__)


def _canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(gen.TASK_ID, root=ROOT)]


def _canonical_pairs():
    return canonical_pairs(gen.TASK_ID, root=ROOT)


def _marker(grid):
    cells = [(r, c, v) for r, row in enumerate(grid) for c, v in enumerate(row) if v]
    assert len(cells) == 1
    return cells[0]


def test_canonical_inputs_are_accepted():
    assert all(gen.self_check(grid) == [] for grid in _canonical_inputs())


def test_default_draws_have_one_interior_marker_and_honest_observation():
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            grid = gen.generate(seed, seed * 17 + 3, difficulty=band)
            assert gen.self_check(grid) == []
            r, c, color = _marker(grid)
            assert gen.observe_overrides(grid) == {
                "grid_h": len(grid),
                "grid_w": len(grid[0]),
                "fg_color": color,
                "marker_row": r,
                "marker_col": c,
            }


def test_exact_boundary_overrides_and_conflicts():
    grid = gen.generate(
        7,
        9,
        difficulty="easy",
        grid_h=15,
        grid_w=15,
        fg_color=9,
        marker_row=13,
        marker_col=13,
    )
    assert gen.observe_overrides(grid) == {
        "grid_h": 15,
        "grid_w": 15,
        "fg_color": 9,
        "marker_row": 13,
        "marker_col": 13,
    }
    with pytest.raises(ValueError, match="cannot contain"):
        gen.generate(1, 1, grid_h=3, marker_row=13)
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 1, texture="cluster")


def test_self_check_rejects_targeted_impostors():
    impostors = [
        [[0] * 5 for _ in range(5)],
        [[0, 0, 0], [0, 2, 2], [0, 0, 0]],
        [[0, 0, 0], [0, 2, 3], [0, 0, 0]],
        [[2, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
    ]
    assert all(gen.self_check(grid) for grid in impostors)


def test_replay_freshness_and_global_rng_purity():
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    mutated = copy.deepcopy(first)
    mutated[0][0] = 9
    assert gen.generate(123, 456, difficulty="hard") == second


def test_canonical_profile_schedule_is_stable_and_above_floor():
    canonical_profiles = {(5, 7, 1), (5, 3, 3), (5, 5, 6), (3, 3, 2), (9, 7, 8)}

    def strict(grid):
        h, w = len(grid), len(grid[0])
        r, c, color = _marker(grid)
        return (h, w, color) in canonical_profiles and (r, c) == (h // 2, w // 2)

    for start in (0, 10000):
        for band in ("easy", "medium", "hard"):
            grids = [gen.generate(start + i, start + i, difficulty=band) for i in range(200)]
            assert sum(strict(grid) for grid in grids) >= 50


def _pair(grid):
    return {"input": grid, "output": gen._rule_mirror(grid)}


@pytest.mark.parametrize(
    ("band", "seed", "start"),
    [
        ("easy", 1087120524, 38),
        ("easy", 2719317930, 76),
        ("medium", 674903444, 21),
    ],
)
def test_regression_every_query_rotation_is_lesson_identifiable(band, seed, start):
    pairs = [
        _pair(gen.generate(seed, sample_index, difficulty=band))
        for sample_index in range(start, start + 4)
    ]
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []


def test_declared_override_incompatibilities_match_dimension_marker_bounds():
    declared = getattr(gen, "INCOMPATIBLE_OVERRIDE_COMBINATIONS", None)
    assert declared is not None
    actual = {tuple(sorted(item.items())) for item in declared}
    expected = {
        tuple(sorted({"grid_h": height, "marker_row": row}.items()))
        for height in range(3, 16)
        for row in range(1, 14)
        if row > height - 2
    } | {
        tuple(sorted({"grid_w": width, "marker_col": col}.items()))
        for width in range(3, 16)
        for col in range(1, 14)
        if col > width - 2
    }
    assert actual == expected


def test_every_semantic_witness_has_a_verified_rival_or_branch_role():
    rival_witnesses = set(gen.WITNESS_RIVALS)
    branch_witnesses = set(gen.BRANCH_WITNESSES)
    assert rival_witnesses | branch_witnesses == set(gen.SEMANTIC_WITNESSES)
    assert rival_witnesses & branch_witnesses == set()
    for names in gen.WITNESS_RIVALS.values():
        assert names
        assert set(names) <= set(gen.SEMANTIC_RIVALS)


def test_canonical_profile_only_rival_fits_canonical_and_is_refuted_off_manifold():
    rival = gen.SEMANTIC_RIVALS["canonical_profile_only"]
    assert gen.CANONICAL_SHORTCUTS["canonical_profile_only"] is rival
    assert gen.LESSON_COMPETITORS["canonical_profile_only"] is rival
    for pair in _canonical_pairs():
        assert rival(pair["input"]) == pair["output"]

    for band in ("easy", "medium", "hard"):
        grid = gen.generate(17, 1, difficulty=band)
        assert gen.strict_canonical_like(grid)
        assert all(
            gen.SEMANTIC_WITNESSES[name](grid)
            for name in ("off_center_marker", "non_canonical_dims", "non_canonical_color")
        )
        assert rival(grid) != gen._rule_mirror(grid)


def test_lesson_hook_flags_canonical_profile_only_survivor():
    demos = [
        {"input": pair["input"], "output": pair["output"]}
        for pair in _canonical_pairs()[:3]
    ]
    query_grid = gen.generate(
        3,
        7,
        grid_h=5,
        grid_w=7,
        fg_color=4,
        marker_row=2,
        marker_col=3,
    )
    query = {"input": query_grid, "output": gen._rule_mirror(query_grid)}
    reasons = gen.lesson_identifiable(demos, query)
    assert any("canonical_profile_only" in reason for reason in reasons)
