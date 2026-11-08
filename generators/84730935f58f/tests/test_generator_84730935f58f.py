"""Focused source tests for the repaired selector/stencil generator."""
from __future__ import annotations

import copy
from functools import cache
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "84730935f58f"
ROOT = find_root(__file__)


@cache
def gen():
    module, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    return module


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_canonical_pairs_pass_self_check_and_python_mirror_exactly():
    rows = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(rows) == 3
    for pair in rows:
        grid = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(grid)
        assert gen().self_check(grid) == []
        assert gen().rule_mirror(grid) == pair["output"]
        assert grid == snapshot


def test_exact_controls_are_observable_and_selector_halo_is_clear():
    grid = gen().generate(
        91,
        5,
        difficulty="hard",
        height=14,
        width=13,
        mode="x",
        num_seeds=6,
        n_distinct_colors=4,
        palette_kind="spread_seeds",
    )
    assert gen().self_check(grid) == []
    facts = gen().profile_signature(grid)
    assert facts["height"] == 14
    assert facts["width"] == 13
    assert facts["mode"] == "x"
    assert facts["num_seeds"] == 6
    assert facts["n_distinct_colors"] == 4
    assert facts["selector"] != 1
    assert all(grid[r][c] == 0 for r, c in ((0, 1), (1, 0), (1, 1)))


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_four_example_schedule_always_teaches_both_stencils(difficulty):
    modes = [
        gen().profile_signature(gen().generate(1, index, difficulty=difficulty))["mode"]
        for index in range(gen().EXAMPLES_NEEDED)
    ]
    assert set(modes) == {"plus", "x"}
    assert all(left != right for left, right in zip(modes, modes[1:]))


def test_palette_profiles_are_real_not_dead_metadata():
    spread = gen().generate(
        17, 3, height=14, width=14, mode="plus", num_seeds=6,
        n_distinct_colors=3, palette_kind="spread_seeds",
    )
    tight = gen().generate(
        17, 3, height=14, width=14, mode="plus", num_seeds=6,
        n_distinct_colors=3, palette_kind="tight_seeds",
    )
    sf = gen().profile_signature(spread)
    tf = gen().profile_signature(tight)
    assert sf["num_seeds"] == tf["num_seeds"] == 6
    assert sf["minimum_seed_distance"] > tf["minimum_seed_distance"]
    assert spread != tight


def test_unknown_and_malformed_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen().generate(1, 0, typo_axis=3)
    with pytest.raises((TypeError, ValueError)):
        gen().generate(1, 0, num_seeds=True)
    with pytest.raises((TypeError, ValueError)):
        gen().generate(1, 0, height="8")
    with pytest.raises(ValueError):
        gen().generate(1, 0, num_seeds=3, n_distinct_colors=4)
    with pytest.raises(ValueError):
        gen().generate(1, 0, texture="tight_seeds", palette_kind="spread_seeds")


def test_self_check_rejects_structural_impostors_without_mutation():
    valid = gen().generate(7, 2, mode="plus", num_seeds=3)
    cases = []

    no_selector = copy.deepcopy(valid)
    no_selector[0][0] = 0
    cases.append(no_selector)

    selector_overlap = copy.deepcopy(valid)
    selector_overlap[0][1] = 4
    cases.append(selector_overlap)

    output_color_in_input = copy.deepcopy(valid)
    seed = gen().profile_signature(valid)["seed_cells"][0]
    output_color_in_input[seed[0]][seed[1]] = 8
    cases.append(output_color_in_input)

    one_seed = [[0 for _ in row] for row in valid]
    one_seed[0][0] = 1
    one_seed[3][3] = 4
    cases.append(one_seed)

    cases.extend(([], [[1, 0], [0]], [[True, 0], [0, 0]]))

    for grid in cases:
        snapshot = copy.deepcopy(grid)
        assert gen().self_check(grid)
        assert grid == snapshot


def test_generation_is_deterministic_fresh_and_global_rng_independent():
    random.seed(123456789)
    state = random.getstate()
    first = gen().generate(771, 22, difficulty="hard")
    second = gen().generate(771, 22, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second and all(a is not b for a, b in zip(first, second))
    expected = frozen(second)
    first[0][0] = 9
    assert frozen(gen().generate(771, 22, difficulty="hard")) == expected
    assert len({frozen(gen().generate(seed, 9)) for seed in range(20)}) >= 18
