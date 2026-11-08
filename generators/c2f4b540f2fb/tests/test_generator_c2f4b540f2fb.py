from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.c2f4b540f2fb.generator"
)
TASK_ID = "c2f4b540f2fb"
ROOT = find_root(__file__)


def test_canonical_inputs_are_accepted_and_mirror_exact() -> None:
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.strict_canonical_like(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]


def test_scheduled_lessons_cover_unique_tied_and_signed_maxima() -> None:
    grids = [MODULE.generate(2026, index, difficulty="medium") for index in range(4)]
    analyses = [MODULE._analyze(grid) for grid in grids]
    assert all(not analysis["errors"] for analysis in analyses)
    assert {analysis["motif_profile"] for analysis in analyses} == set(MODULE.MOTIF_PROFILES)
    assert any(len(analysis["chosen"]) == 1 for analysis in analyses)
    assert any(len(analysis["chosen"]) > 1 for analysis in analyses)
    assert {analysis["max_u"] < 0 for analysis in analyses} == {False, True}
    assert any(analysis["max_u"] == 0 for analysis in analyses)


def test_all_declared_override_boundaries_are_exact_and_observable() -> None:
    cases = (
        {"grid_h": 11, "grid_w": 14},
        {"grid_h": 16, "grid_w": 18},
        {"motif_profile": "negative_tie", "frame_relation": "quarter_turn"},
        {"motif_profile": "positive_unique", "layout_axis": "vertical"},
        {"frame_relation": "reflected", "layout_axis": "horizontal"},
    )
    for difficulty in ("easy", "medium", "hard"):
        for case in cases:
            grid = MODULE.generate(101, 37, difficulty=difficulty, **case)
            assert MODULE.self_check(grid) == []
            observed = MODULE.observe_overrides(grid)
            for name, value in case.items():
                assert observed[name] == value


def test_unknown_overrides_and_bad_difficulty_reject_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 1, texture="warm")
    with pytest.raises(ValueError, match="unknown difficulty"):
        MODULE.generate(1, 1, difficulty="extreme")


def test_declared_mutation_fixtures_are_rejected() -> None:
    fixtures = MODULE.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert MODULE.self_check(grid), name


def test_tied_maximum_copies_every_tied_point() -> None:
    grid = MODULE.generate(
        707,
        3,
        motif_profile="positive_tie",
        frame_relation="quarter_turn",
        layout_axis="vertical",
    )
    analysis = MODULE._analyze(grid)
    assert len(analysis["chosen"]) == 2
    out = MODULE.rule_mirror(grid)
    changed = {
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] != out[r][c]
    }
    assert changed == set(analysis["target_cells"])
    assert all(out[r][c] == 8 for r, c in changed)


def test_four_demo_schedule_identifies_rule_against_declared_rivals() -> None:
    demos = []
    for index in range(MODULE.EXAMPLES_NEEDED):
        inp = MODULE.generate(818, index, difficulty="medium")
        demos.append({"input": inp, "output": MODULE.rule_mirror(inp)})
    query_input = MODULE.generate(818, MODULE.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_input, "output": MODULE.rule_mirror(query_input)}
    assert MODULE.lesson_identifiable(demos, query) == []


def test_replay_freshness_input_purity_and_global_rng() -> None:
    random.seed(1739)
    before_rng = random.getstate()
    first = MODULE.generate(919, 12, difficulty="hard")
    after_rng = random.getstate()
    second = MODULE.generate(919, 12, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before_rng == after_rng

    original = copy.deepcopy(first)
    _ = MODULE.rule_mirror(first)
    assert first == original
