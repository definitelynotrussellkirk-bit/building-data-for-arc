"""Focused public-contract regressions for Right-Hand Echo (2c35533cc389)."""
from __future__ import annotations

from itertools import product
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "2c35533cc389"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize(
    ("seed", "sample_index", "difficulty"),
    [
        (True, 0, "easy"),
        (1.0, 0, "easy"),
        ("1", 0, "easy"),
        (991, True, "easy"),
        (991, 1.0, "easy"),
        (991, "0", "easy"),
        (991, -1, "easy"),
        (991, 0, True),
        (991, 0, 0),
        (991, 0, 1.0),
        (991, 0, "__invalid_difficulty__"),
    ],
)
def test_generate_rejects_invalid_public_scalar_arguments(
    seed, sample_index, difficulty
):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, sample_index, difficulty=difficulty)


@pytest.mark.parametrize("axis,control", (("grid_h", 5), ("grid_w", 6), ("n_cells", 2)))
@pytest.mark.parametrize(
    "invalid_factory",
    (lambda n: True, lambda n: str(n), lambda n: float(n), lambda n: n + 0.75),
)
def test_exact_integer_axes_reject_coercible_nonintegers(
    axis, control, invalid_factory
):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(
            991,
            0,
            difficulty="easy",
            **{axis: invalid_factory(control)},
        )


def test_unknown_override_is_rejected_instead_of_silently_ignored():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(991, 0, mystery_axis="red")


@pytest.mark.parametrize("difficulty", (None, "easy", "medium", "hard"))
def test_literal_integer_overrides_remain_exact_and_observable(difficulty):
    requested = {
        "grid_h": 8,
        "grid_w": 10,
        "n_cells": 8,
        "right_edge_mode": "present",
        "right_neighbor_relation": "red",
    }
    grid = GEN.generate(991, 0, difficulty=difficulty, **requested)
    assert GEN.observe_overrides(grid) == requested
    assert GEN.self_check(grid, meta={"overrides": requested}) == []


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
@pytest.mark.parametrize(
    "height,width,n_cells,edge_mode,neighbor_relation",
    product((5, 8), (6, 10), (2, 8), ("absent", "present"), ("empty", "red")),
)
def test_boundary_cartesian_product_is_constructive_and_exact(
    difficulty, height, width, n_cells, edge_mode, neighbor_relation
):
    requested = {
        "grid_h": height,
        "grid_w": width,
        "n_cells": n_cells,
        "right_edge_mode": edge_mode,
        "right_neighbor_relation": neighbor_relation,
    }
    grid = GEN.generate(1201, 2, difficulty=difficulty, **requested)
    assert GEN.self_check(grid, meta={"overrides": requested}) == []
    assert GEN.observe_overrides(grid) == requested


def test_every_three_example_schedule_window_contains_all_teaching_profiles():
    expected = set(GEN.SCHEDULE_PROFILES)
    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(18):
            observed = {
                GEN.schedule_profile(77, index, difficulty=difficulty)
                for index in range(start, start + GEN.EXAMPLES_NEEDED)
            }
            assert observed == expected


def test_rule_mirror_matches_every_labeled_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_rule_reads_all_sources_before_overwriting_adjacent_red():
    grid = [
        [0, 0, 0, 0, 0, 0],
        [0, 2, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 2, 0],
    ]
    assert GEN.self_check(grid) == []
    output = GEN.rule_mirror(grid)
    assert output[1] == [0, 2, 1, 1, 0, 0]
    assert output[4] == [0, 0, 0, 0, 2, 1]


def test_generate_is_deterministic_and_does_not_touch_global_random_state():
    state = random.getstate()
    first = GEN.generate(4381, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == GEN.generate(4381, 17, difficulty="hard")
    assert first is not GEN.generate(4381, 17, difficulty="hard")
