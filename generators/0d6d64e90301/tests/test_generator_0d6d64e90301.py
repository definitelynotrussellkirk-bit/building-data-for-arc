from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module("puzzle_generators.per_puzzle.0d6d64e90301.generator")


def test_rule_hash_and_all_canonical_pairs_are_pinned_and_accepted():
    assert gen.RULE_HASH == "511f58f5d471"
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._upscale2(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_exact_boundary_overrides_round_trip_in_every_difficulty_band():
    for band in ("easy", "medium", "hard"):
        low = gen.generate(11, 3, difficulty=band, grid_h=3, grid_w=3)
        high = gen.generate(11, 3, difficulty=band, grid_h=5, grid_w=5)
        assert gen.observe_overrides(low) == {"grid_h": 3, "grid_w": 3}
        assert gen.observe_overrides(high) == {"grid_h": 5, "grid_w": 5}
        assert gen.self_check(low) == []
        assert gen.self_check(high) == []


def test_unknown_override_is_rejected_instead_of_silently_ignored():
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(7, 1, difficulty="medium", typo_axis=4)


def test_replay_returns_fresh_grids_without_touching_global_rng():
    random.seed(20260815)
    state = random.getstate()
    first = gen.generate(99, 17, difficulty="hard")
    second = gen.generate(99, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    assert random.getstate() == state


def test_every_ordinary_draw_refutes_instance_local_upscale_rivals():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for i in range(40):
            grid = gen.generate(20_000 + 100 * band_index + i, i, difficulty=band)
            expected = gen._upscale2(grid)
            assert gen.self_check(grid) == []
            for rival in gen.INSTANCE_RIVALS.values():
                assert rival(grid) != expected


def test_self_check_rejects_declared_structural_impostors():
    fixtures = list(gen.mutation_fixtures())
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        errors = gen.self_check(grid)
        assert errors, f"declared impostor {name!r} unexpectedly passed"


def test_disconnected_negative_recombination_is_out_of_distribution():
    # Two individually lawful colors/dimensions are recombined into disconnected
    # islands.  The Racket rule can still upscale this grid, but it must not be
    # admitted as a lesson from the connected canonical teaching grammar.
    grid = [
        [2, 0, 0, 0],
        [2, 0, 0, 0],
        [0, 0, 0, 3],
        [0, 0, 3, 3],
    ]
    errors = gen.self_check(grid)
    assert any("4-connected" in error for error in errors)
    assert len(gen._upscale2(grid)) == 8
    assert len(gen._upscale2(grid)[0]) == 8


@pytest.mark.parametrize(
    ("seed", "sample_index", "difficulty", "overrides", "error", "message"),
    [
        (True, 0, None, {}, TypeError, "seed"),
        (1.0, 0, None, {}, TypeError, "seed"),
        (1, True, None, {}, TypeError, "sample_index"),
        (1, -1, None, {}, ValueError, "nonnegative"),
        (1, 0, 0, {}, ValueError, "difficulty"),
        (1, 0, "__invalid_difficulty__", {}, ValueError, "difficulty"),
        (1, 0, None, {"grid_h": 3.0}, TypeError, "grid_h"),
        (1, 0, None, {"grid_h": "3"}, TypeError, "grid_h"),
        (1, 0, None, {"grid_w": False}, TypeError, "grid_w"),
        (1, 0, None, {"grid_w": 5.75}, TypeError, "grid_w"),
    ],
)
def test_invalid_scalar_requests_are_rejected(
    seed, sample_index, difficulty, overrides, error, message
):
    with pytest.raises(error, match=message):
        gen.generate(
            seed,
            sample_index,
            difficulty=difficulty,
            **overrides,
        )


def test_square_only_canonical_shortcut_is_declared_and_has_a_rectangular_witness():
    assert set(gen.CANONICAL_SHORTCUTS) == {"square_only_upscale"}
    assert "square_only_upscale" in gen.LESSON_COMPETITORS
    assert "square_only_upscale" in gen.SEMANTIC_RIVALS

    rival = gen.CANONICAL_SHORTCUTS["square_only_upscale"]
    for pair in canonical_pairs(gen.TASK_ID, root=find_root(__file__)):
        assert len(pair["input"]) == len(pair["input"][0])
        assert rival(copy.deepcopy(pair["input"])) == pair["output"]

    rectangular = [
        [0, 2, 0, 0],
        [0, 2, 3, 0],
        [0, 0, 3, 0],
    ]
    assert gen.self_check(rectangular) == []
    assert rival(rectangular) != gen._upscale2(rectangular)
    witness = gen.SEMANTIC_WITNESSES["rectangular_input_refutes_square_only"]
    assert witness(rectangular)
    assert gen.WITNESS_RIVALS["rectangular_input_refutes_square_only"] == [
        "square_only_upscale"
    ]


def test_lesson_identifiable_rejects_square_only_demos_with_rectangular_query():
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    demos = copy.deepcopy(pairs[:2])
    rectangular = [
        [0, 2, 0, 0],
        [0, 2, 3, 0],
        [0, 0, 3, 0],
    ]
    query = {"input": rectangular, "output": gen._upscale2(rectangular)}

    reasons = gen.lesson_identifiable(demos, query)
    assert any("square_only_upscale" in reason for reason in reasons)


def test_every_three_step_lesson_schedule_has_one_square_and_two_rectangles():
    assert gen.LESSON_SCHEDULE_PERIOD == 3
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "square_anchor",
        "wide_rectangle",
        "tall_rectangle",
    )

    # The materializer requests consecutive sample indices.  Any three-step
    # window must therefore contain exactly one square anchor and two
    # rectangular counterexamples.  Holding out any one pair still leaves a
    # rectangular demonstration that refutes the square-only shortcut.
    for band in ("easy", "medium", "hard"):
        for start in range(9):
            grids = [
                gen.generate(700 + start, start + offset, difficulty=band)
                for offset in range(3)
            ]
            rectangular = [len(grid) != len(grid[0]) for grid in grids]
            assert rectangular.count(False) == 1
            assert rectangular.count(True) == 2
            for query_index in range(3):
                demo_indices = [i for i in range(3) if i != query_index]
                assert any(rectangular[i] for i in demo_indices)
