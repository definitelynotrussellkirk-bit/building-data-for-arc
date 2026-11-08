from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.c7a821733003.generator")


def test_all_canonical_pairs_are_accepted_and_solved_without_mutation():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(original) == []
        assert gen.rule_mirror(original) == pair["output"]
        assert original == pair["input"]


def test_every_scene_profile_is_exactly_observable_and_override_safe():
    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(1000 + index, index, difficulty="medium", scene_profile=profile)
        assert gen.self_check(grid, meta={"overrides": {"scene_profile": profile}}) == []
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert gen.strict_canonical_like(grid) == []


def test_unknown_overrides_and_profiles_fail_closed():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="x")
    with pytest.raises(ValueError, match="unknown scene_profile"):
        gen.generate(1, 0, scene_profile="not-a-profile")


def test_regression_source_shortcut_is_falsified_but_canonical_anchor_remains():
    common = gen.generate(7, 0, scene_profile="canonical_common_first")
    assert gen._rival_source_mismatch(common) == gen.rule_mirror(common)

    for profile in ("canonical_odd_middle", "wide_unrelated_middle"):
        grid = gen.generate(7, 0, scene_profile=profile)
        assert gen._rival_source_mismatch(grid) != gen.rule_mirror(grid)
        assert gen.SEMANTIC_WITNESSES["source_relation_breaks_source_mismatch"](grid)


def test_structural_and_semantic_mutations_are_rejected():
    grid = gen.generate(19, 5, scene_profile="wide_unrelated_middle")

    ragged = copy.deepcopy(grid)
    ragged[0].pop()
    assert any("rectangular" in message for message in gen.self_check(ragged))

    missing_basis = copy.deepcopy(grid)
    analysis = gen._analysis(missing_basis)
    (_origin, vx, _vy) = analysis["candidates"][0]
    row, col = _origin[0] + vx[0], _origin[1] + vx[1]
    missing_basis[row][col] = 0
    assert gen.self_check(missing_basis)

    all_same = copy.deepcopy(grid)
    analysis = gen._analysis(all_same)
    odd_frame = analysis["candidates"][analysis["odd_index"]]
    common = analysis["common_signature"]
    (orow, ocol), vx, vy = odd_frame
    for row, values in enumerate(all_same):
        for col, value in enumerate(values):
            if value == 8:
                dr, dc = row - orow, col - ocol
                u = dr * vx[0] + dc * vx[1]
                v = dr * vy[0] + dc * vy[1]
                if max(abs(u), abs(v)) <= 3:
                    all_same[row][col] = 0
    for u, v in common:
        all_same[orow + u * vx[0] + v * vy[0]][ocol + u * vx[1] + v * vy[1]] = 8
    assert any("exactly one odd" in message for message in gen.self_check(all_same))

    stray_eight = copy.deepcopy(grid)
    stray_eight[-1][0] = 8
    assert any(
        "all color-8 cells" in message
        for message in gen.self_check(stray_eight)
    )

    unequal_cardinality = copy.deepcopy(grid)
    analysis = gen._analysis(unequal_cardinality)
    odd_frame = analysis["candidates"][analysis["odd_index"]]
    (orow, ocol), vx, vy = odd_frame
    u, v = analysis["odd_signature"][0]
    unequal_cardinality[orow + u * vx[0] + v * vy[0]][
        ocol + u * vx[1] + v * vy[1]
    ] = 0
    assert any(
        "cardinality must be equal" in message
        for message in gen.self_check(unequal_cardinality)
    )


def test_four_consecutive_demos_identify_every_query_start_offset():
    for start in range(len(gen.SCENE_PROFILES)):
        demos = []
        for offset in range(gen.EXAMPLES_NEEDED):
            grid = gen.generate(31, start + offset, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(31, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []


def test_replay_fresh_returns_and_global_random_state():
    state = random.getstate()
    a = gen.generate(123, 9, difficulty="hard")
    b = gen.generate(123, 9, difficulty="hard")
    assert a == b and a is not b and all(x is not y for x, y in zip(a, b))
    a[0][0] = 9
    assert b[0][0] != 9
    assert random.getstate() == state
