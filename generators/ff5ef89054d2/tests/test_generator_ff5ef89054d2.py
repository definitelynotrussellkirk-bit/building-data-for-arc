from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators import base
from puzzle_generators.per_puzzle.ff5ef89054d2 import generator
from reviewer_support import canonical_pairs as load_canonical_pairs, find_root


def canonical_pairs():
    for pair in load_canonical_pairs(generator.TASK_ID, root=find_root(__file__)):
        yield copy.deepcopy(pair["input"]), copy.deepcopy(pair["output"])


def test_all_canonical_pairs_are_accepted_and_exact():
    pairs = list(canonical_pairs())
    assert len(pairs) == 3
    for grid, expected in pairs:
        before = copy.deepcopy(grid)
        assert generator.self_check(grid) == []
        assert generator.strict_canonical_like(grid) == []
        assert generator.rule_mirror(grid) == expected
        assert grid == before


def test_default_draws_are_lawful_and_record_exact_provenance():
    for band in ("easy", "medium", "hard"):
        for seed in range(60):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = generator.generate(seed, seed * 17 + 5, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert generator.self_check(grid) == []
            assert captured[-1].recorded_draws() == generator.observe_overrides(grid)


@pytest.mark.parametrize("mode", generator.BOUNDARY_MODES)
def test_forced_boundary_modes_are_observable(mode):
    grid = generator.generate(
        103,
        211,
        difficulty="hard",
        grid_h=11,
        grid_w=9,
        n_markers=4,
        n_decoy_blobs=1,
        boundary_mode=mode,
    )
    assert generator.self_check(grid) == []
    assert generator.observe_overrides(grid) == {
        "grid_h": 11,
        "grid_w": 9,
        "n_markers": 4,
        "n_decoy_blobs": 1,
        "boundary_mode": mode,
    }


def test_extreme_override_cross_product_is_exact():
    for band in ("easy", "medium", "hard"):
        for h in (9, 11):
            for w in (9, 11):
                for markers in (2, 4):
                    for decoys in (0, 1):
                        for mode in generator.BOUNDARY_MODES:
                            requested = {
                                "grid_h": h,
                                "grid_w": w,
                                "n_markers": markers,
                                "n_decoy_blobs": decoys,
                                "boundary_mode": mode,
                            }
                            grid = generator.generate(
                                701 + h + w + markers + decoys,
                                9001,
                                difficulty=band,
                                **requested,
                            )
                            assert generator.observe_overrides(grid) == requested


def test_deterministic_fresh_returns_and_global_rng_isolation():
    random.seed(9981)
    state = random.getstate()
    first = generator.generate(19, 31, difficulty="hard")
    assert random.getstate() == state
    second = generator.generate(19, 31, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_rule_mirror_is_input_pure_and_reentrant_aba():
    a = generator.generate(41, 97, difficulty="easy")
    b = generator.generate(42, 98, difficulty="hard")
    a_before = copy.deepcopy(a)
    b_before = copy.deepcopy(b)
    a1 = generator.rule_mirror(a)
    b1 = generator.rule_mirror(b)
    a2 = generator.rule_mirror(a)
    assert a1 == a2
    assert a == a_before
    assert b == b_before
    assert a1 != b1


def test_self_check_rejects_structural_impostors():
    valid = [[0] * 9 for _ in range(9)]
    valid[1][1] = 2
    valid[4][4] = 4
    valid[7][7] = 6
    assert generator.self_check(valid) == []

    blank = [[0] * 9 for _ in range(9)]

    bad_color = copy.deepcopy(valid)
    bad_color[0][8] = 10

    occupied_arm = copy.deepcopy(valid)
    occupied_arm[0][0] = 2

    overlapping_arms = [[0] * 9 for _ in range(9)]
    overlapping_arms[2][2] = 2
    overlapping_arms[2][4] = 4
    overlapping_arms[6][6] = 6

    decoy = generator.generate(
        8,
        2,
        n_decoy_blobs=1,
        boundary_mode="interior",
        n_markers=3,
    )
    analysis = generator._analyze(decoy)
    multicolor_decoy = copy.deepcopy(decoy)
    cells = sorted(analysis["decoys"][0])
    multicolor_decoy[cells[0][0]][cells[0][1]] = (
        multicolor_decoy[cells[0][0]][cells[0][1]] % 9
    ) + 1

    for mutation in (
        blank,
        bad_color,
        occupied_arm,
        overlapping_arms,
        multicolor_decoy,
    ):
        assert generator.self_check(mutation), mutation


def test_every_semantic_witness_has_a_named_disagreeing_rival():
    assert set(generator.SEMANTIC_WITNESSES) <= set(generator.WITNESS_RIVALS)


def test_declared_rivals_have_generated_counterexamples():
    decoy_grid = generator.generate(
        17,
        2,
        n_decoy_blobs=1,
        boundary_mode="right_edge",
        n_markers=3,
    )
    truth = generator.rule_mirror(decoy_grid)
    assert generator.SEMANTIC_RIVALS["expand_all_nonzero"](decoy_grid) != truth
    assert generator.SEMANTIC_RIVALS["ignore_boundary_markers"](decoy_grid) != truth
    assert generator.SEMANTIC_RIVALS["orthogonal_plus"](decoy_grid) != truth
    assert generator.SEMANTIC_RIVALS["remove_marker_centers"](decoy_grid) != truth


def test_three_demo_windows_identify_the_rule():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for offset in range(3):
                grid = generator.generate(300 + start, start + offset, difficulty=band)
                demos.append({"input": grid, "output": generator.rule_mirror(grid)})
            query_grid = generator.generate(700 + start, start + 3, difficulty=band)
            query = {"input": query_grid, "output": generator.rule_mirror(query_grid)}
            assert generator.lesson_identifiable(demos, query) == []


def test_every_query_rotation_identifies_the_rule():
    """Any one of four materialized pairs may be the downstream query."""
    for band in ("easy", "medium", "hard"):
        for start in range(len(generator.SCHEDULE_PROFILES)):
            pairs = []
            for offset in range(4):
                grid = generator.generate(900 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": generator.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert generator.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    query_index,
                    [generator.observe_overrides(pair["input"]) for pair in pairs],
                )


def test_invalid_difficulty_and_unknown_override_fail_loudly():
    with pytest.raises(ValueError):
        generator.generate(0, 0, difficulty="expert")
    with pytest.raises(ValueError):
        generator.generate(0, 0, bogus=1)
