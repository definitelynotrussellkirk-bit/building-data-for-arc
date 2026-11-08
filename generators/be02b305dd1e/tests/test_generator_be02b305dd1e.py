from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.be02b305dd1e import generator as gen
from reviewer_support import canonical_pairs, find_root


def test_rule_hash_is_pinned_to_selected_authority() -> None:
    assert gen.RULE_HASH == "ed1eb3ca2cbf"


def test_unknown_override_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(7, 3, difficulty="easy", misspelled_profile="anything")


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed(bad_seed: object) -> None:
    with pytest.raises(TypeError, match="seed"):
        gen.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index(bad_index: object) -> None:
    error = TypeError if type(bad_index) is not int else ValueError
    with pytest.raises(error, match="sample_index"):
        gen.generate(991, bad_index, difficulty="easy")


def test_every_holdout_keeps_a_non_target_first_demonstration() -> None:
    # Retained semantic-gate replay: the old random placement made the first
    # four targets topmost, so a first-object-only rival fit all demos and
    # disagreed only on the query. Every five-pair window needs at least two
    # examples whose first nonzero component is not the green target.
    seed = 232_922_564_183_033
    grids = [
        gen.generate(seed, 33 + offset, difficulty="medium")
        for offset in range(gen.EXAMPLES_NEEDED + 1)
    ]
    non_target_first = [
        next(value for row in grid for value in row if value != 0) != 3
        for grid in grids
    ]
    for query_index in range(len(grids)):
        assert any(
            flag for index, flag in enumerate(non_target_first)
            if index != query_index
        )


def test_every_scene_profile_is_exact_and_observable() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(
                10_000 + index,
                100 + index,
                difficulty=difficulty,
                scene_profile=profile,
            )
            assert gen.self_check(grid, meta={"scene_profile": profile}) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}


def test_self_check_rejects_non_solid_target_mutation() -> None:
    grid = gen.generate(
        123,
        0,
        difficulty="easy",
        scene_profile="10x12_horizontal_plain_4",
    )
    target = gen._analyze(grid)["green_components"][0]
    row, column = target["cells"][0]
    mutated = copy.deepcopy(grid)
    mutated[row][column] = 0
    errors = gen.self_check(mutated)
    assert errors
    assert any(
        "solid rectangle" in error or "dimensions must match" in error
        for error in errors
    )


def test_canonical_pairs_are_accepted_and_python_mirror_is_exact() -> None:
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen._solve_python(pair["input"]) == pair["output"]


def test_every_four_demo_window_is_identifiable() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(16):
            seed = 20_000 + start
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                input_grid = gen.generate(
                    seed,
                    start + offset,
                    difficulty=difficulty,
                )
                demos.append(
                    {"input": input_grid, "output": gen._solve_python(input_grid)}
                )
            query_input = gen.generate(
                seed,
                start + gen.EXAMPLES_NEEDED,
                difficulty=difficulty,
            )
            query = {
                "input": query_input,
                "output": gen._solve_python(query_input),
            }
            assert gen.lesson_identifiable(demos, query) == []


def test_replay_is_deterministic_fresh_and_global_rng_pure() -> None:
    before = random.getstate()
    first = gen.generate(8080, 17, difficulty="hard")
    after = random.getstate()
    second = gen.generate(8080, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
