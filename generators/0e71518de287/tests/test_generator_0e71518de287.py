from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "0e71518de287"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")

def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID)


def test_rule_hash_and_all_canonical_pairs_are_exact_and_input_pure():
    assert gen.RULE_HASH == "f3552b0bd0f3"
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_canonical_tie_is_accepted_but_generated_rows_are_unambiguous():
    tied = _pairs()[1]["input"]
    info, errors = gen._analyse(tied)
    assert errors == []
    assert info["adjacent_indices"] == (0, 1)
    assert gen.rule_mirror(tied) == _pairs()[1]["output"]

    for difficulty in ("easy", "medium", "hard", None):
        for sample_index in range(30):
            grid = gen.generate(20260729, sample_index, difficulty=difficulty)
            assert gen.generation_check(grid) == []


def test_every_exact_axis_boundary_is_observable_and_unknown_keys_reject():
    base = {"grid_h": 9, "grid_w": 10, "marker_color": 1,
            "marker_side": "top", "selected_frame": 0}
    cases = []
    for value in (9, 10):
        cases.append({**base, "grid_h": value})
    for value in (10, 12):
        cases.append({**base, "grid_w": value})
    for value in (1, 9):
        cases.append({**base, "marker_color": value})
    for value in gen.MARKER_SIDES:
        cases.append({**base, "marker_side": value})
    for value in (0, 1):
        cases.append({**base, "selected_frame": value})

    for difficulty in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = gen.generate(1234, index, difficulty=difficulty, **overrides)
            observed = gen.observe_overrides(grid)
            for key, value in overrides.items():
                assert observed[key] == value
            assert gen.generation_check(grid) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_marker_side="top")


def test_four_consecutive_demos_refute_all_named_rivals():
    for start in range(12):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(314159, sample_index, difficulty="hard")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(314159, start + gen.EXAMPLES_NEEDED, difficulty="hard")
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        for competitor in gen.LESSON_COMPETITORS.values():
            assert any(competitor(pair["input"]) != pair["output"] for pair in demos)


def test_self_check_rejects_targeted_rule_hiding_mutations():
    grid = gen.generate(99, 7, grid_h=10, grid_w=12,
                        marker_color=6, marker_side="right", selected_frame=1)
    assert gen.generation_check(grid) == []
    info, _ = gen._analyse(grid)

    broken_frame = copy.deepcopy(grid)
    r0, c0, _, _ = info["frames"][0]
    broken_frame[r0][c0] = 0
    assert any("hollow rectangular frame" in e or "exactly two" in e
               for e in gen.self_check(broken_frame))

    second_marker = copy.deepcopy(grid)
    second_marker[0][0] = 3
    assert any("exactly one non-yellow marker" in e for e in gen.self_check(second_marker))

    detached_marker = copy.deepcopy(grid)
    mr, mc = info["marker"]
    detached_marker[mr][mc] = 0
    detached_marker[0][0] = info["marker_color"]
    assert any("adjacent" in e for e in gen.self_check(detached_marker))

    solid_frame = copy.deepcopy(grid)
    r0, c0, r1, c1 = info["frames"][0]
    solid_frame[r0 + 1][c0 + 1] = 4
    assert any("hollow rectangular frame" in e for e in gen.self_check(solid_frame))


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260729)
    before = random.getstate()
    first = gen.generate(777, 12, difficulty="hard")
    after = random.getstate()
    second = gen.generate(777, 12, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after

    first[0][0] = 9
    assert gen.generate(777, 12, difficulty="hard") == second
