from __future__ import annotations

import copy
import random

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.23038bd082f9.generator")


def test_rule_mirror_matches_canonical_pairs():
    canonical_inputs = [
        [[0, 0, 0, 0, 0, 0, 0, 0], [0, 2, 0, 0, 0, 2, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]],
        [[0, 0, 0, 0, 0, 0, 0], [9, 0, 0, 0, 0, 0, 9], [0, 0, 0, 0, 0, 0, 0]],
    ]
    expected = [
        [[0, 0, 0, 0, 0, 0, 0, 0], [0, 2, 2, 2, 2, 2, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0]],
        [[0, 0, 0, 0, 0, 0, 0], [9, 9, 9, 9, 9, 9, 9], [0, 0, 0, 0, 0, 0, 0]],
    ]
    assert [gen.rule_mirror(grid) for grid in canonical_inputs] == expected


def test_exact_overrides_are_realized_and_replayed():
    overrides = {
        "grid_h": 12,
        "grid_w": 16,
        "span_count": 6,
        "distractor_count": 3,
        "palette_kind": "alternating",
        "gap_style": "wide",
        "distractor_mode": "mixed",
    }
    first = gen.generate(8123, 17, difficulty="hard", **overrides)
    second = gen.generate(8123, 17, difficulty="hard", **overrides)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert gen.observe_overrides(first) == {
        "grid_h": 12,
        "grid_w": 16,
        "span_count": 6,
        "distractor_count": 3,
    }
    assert gen.self_check(first) == []


def test_shortcut_rebutting_rows_are_preserved_by_rule():
    grid = gen.generate(
        991,
        4,
        difficulty="medium",
        span_count=2,
        distractor_count=3,
        distractor_mode="mixed",
    )
    facts = gen.semantic_observables(grid)
    assert facts["has_mismatch"]
    assert facts["has_blocked"]
    assert facts["has_single"]
    output = gen.rule_mirror(grid)
    for row_index, role in enumerate(facts["rows"]):
        if role["kind"] in {"mismatch", "blocked", "single", "empty"}:
            assert output[row_index] == grid[row_index]
        elif role["kind"] == "active":
            assert output[row_index] != grid[row_index]


def test_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_generate_preserves_process_global_rng_and_inputs_are_fresh():
    random.seed(20260725)
    before = random.getstate()
    first = gen.generate(42, 0, difficulty="easy")
    after = random.getstate()
    assert before == after

    replay = gen.generate(42, 0, difficulty="easy")
    replay_copy = copy.deepcopy(replay)
    first[0][0] = (first[0][0] + 1) % 10
    assert replay == replay_copy


def test_lesson_schedule_falsifies_all_declared_rivals():
    demos = []
    for sample_index in range(3):
        inp = gen.generate(7001, sample_index)
        demos.append({"input": inp, "output": gen.rule_mirror(inp)})
    query_input = gen.generate(7001, 3)
    query = {"input": query_input, "output": gen.rule_mirror(query_input)}
    assert gen.lesson_identifiable(demos, query) == []
