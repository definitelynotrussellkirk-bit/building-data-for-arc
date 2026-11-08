from __future__ import annotations

import copy

import pytest

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.8069b5294ce4.generator")
from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "8069b5294ce4"


def test_canonical_inputs_are_accepted_regression():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen._expected_matrix(pair["input"]) == pair["output"]


def test_declared_axes_are_observable_at_boundaries():
    for overrides in (
        {"grid_h": 8, "grid_w": 13, "k_cluster": 4, "n_decoys": 1},
        {"grid_h": 18, "grid_w": 20, "k_cluster": 8, "n_decoys": 5},
    ):
        grid = gen.generate(17, 2, difficulty="hard", **overrides)
        observed = gen.observe_overrides(grid)
        assert observed == overrides
        assert gen.self_check(grid) == []


def test_unknown_override_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=3)


def test_every_four_sample_window_identifies_named_rule():
    for start in range(8):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(91, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": gen._expected_matrix(grid)})
        query_grid = gen.generate(92, start + 20, difficulty="medium")
        assert gen.lesson_identifiable(demos, {"input": query_grid}) == []


def test_self_check_rejects_targeted_impostors():
    grid = gen.generate(11, 1, difficulty="easy")

    no_seed = copy.deepcopy(grid)
    for row in no_seed:
        for c, value in enumerate(row):
            if value == 1:
                row[c] = 2
    assert gen.self_check(no_seed)

    no_decoys = copy.deepcopy(grid)
    info, errors = gen._analysis(no_decoys)
    assert not errors and info is not None
    for i in info["decoys"]:
        for r, c in info["object_list"][i]["cells"]:
            no_decoys[r][c] = 0
    assert gen.self_check(no_decoys)

    singleton_seed_cluster = [[0] * 13 for _ in range(8)]
    singleton_seed_cluster[2][2] = 1
    singleton_seed_cluster[6][10] = 3
    assert gen.self_check(singleton_seed_cluster)

    complete_graph = [[0] * 13 for _ in range(8)]
    # Four single-cell objects in a 2x2 block form a 4-cycle, not a clique;
    # removing the only multi-cell evidence is still rejected.
    complete_graph[2][2] = 1
    complete_graph[2][3] = 2
    complete_graph[3][2] = 3
    complete_graph[3][3] = 4
    complete_graph[6][10] = 5
    assert gen.self_check(complete_graph)
