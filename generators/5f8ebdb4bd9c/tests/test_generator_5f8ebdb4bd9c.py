"""Focused semantic regressions for transform-analogy generator 5f8ebdb4bd9c."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.5f8ebdb4bd9c.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _normalize(grid):
    return [[int(char) for char in row] if isinstance(row, str) else list(row) for row in grid]


def _canonical_pairs():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return row["train"] + [row["test"]]
    raise AssertionError("canonical task missing")


def _pair(seed: int, sample_index: int, difficulty: str):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_regression_canonical_symmetric_sources_are_accepted():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    saw_incidental_symmetry = False
    for pair in pairs:
        grid = _normalize(pair["input"])
        analysis = GEN._analyze(grid)
        assert GEN.self_check(copy.deepcopy(grid)) == []
        assert GEN.strict_canonical_like(copy.deepcopy(grid)) == []
        assert GEN.rule_mirror(copy.deepcopy(grid)) == _normalize(pair["output"])
        if not analysis["facts"]["a_transform_discriminative"]:
            saw_incidental_symmetry = True
        assert len(analysis["facts"]["matches"]) == 1
    assert saw_incidental_symmetry, "fixture must cover the old over-strict asymmetry defect"


def test_rule_hash_matches_pinned_authority():
    assert GEN.RULE_HASH == "bfccb7008cc6"


def test_boundary_overrides_are_exact_and_observable():
    for difficulty in ("easy", "medium", "hard"):
        for command in GEN.TCODES:
            for a_count, c_count in ((3, 3), (3, 6), (6, 3), (6, 6)):
                requested = {
                    "command": command,
                    "a_active_count": a_count,
                    "c_active_count": c_count,
                }
                grid = GEN.generate(91, 17, difficulty=difficulty, **requested)
                assert GEN.self_check(grid, meta={"overrides": requested}) == []
                assert GEN.observe_overrides(grid) == requested
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis=1)
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(0, 0, a_active_count=2)
    with pytest.raises(ValueError, match="not in options"):
        GEN.generate(0, 0, command=0)


def test_default_draw_provenance_matches_returned_axes():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(12):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(4_000 + sample_index, sample_index, difficulty=difficulty)
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            assert captured[0].recorded_draws() == GEN.observe_overrides(grid)
            assert captured[0].overrides_used() == {}


def test_every_four_sample_window_covers_all_transform_branches():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = [_pair(12_345, start + offset, difficulty) for offset in range(5)]
            commands = {
                GEN.observe_overrides(pair["input"])["command"] for pair in pairs[:4]
            }
            assert commands == set(GEN.TCODES)
            assert GEN.lesson_identifiable(pairs[:4], pairs[4]) == []


def test_lessons_refute_named_fixed_and_copy_rivals():
    demos = [_pair(88_001, index, "medium") for index in range(4)]
    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_generated_c_panels_discriminate_every_oracle_transform():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(40):
            analysis = GEN._analyze(GEN.generate(700, sample_index, difficulty=difficulty))
            assert analysis["errors"] == []
            assert analysis["facts"]["a_transform_discriminative"]
            assert analysis["facts"]["c_transform_discriminative"]
            assert analysis["facts"]["command"] in GEN.TCODES


def test_mutation_fixtures_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_difficulty_bands_are_observably_distinct():
    observations = {
        band: GEN.observe_overrides(GEN.generate(321, 7, difficulty=band))
        for band in ("easy", "medium", "hard")
    }
    assert observations["easy"] != observations["medium"]
    assert observations["medium"] != observations["hard"]
    assert observations["easy"] != observations["hard"]


def test_replay_fresh_returns_and_global_rng_purity():
    random.seed(991)
    before = random.getstate()
    first = GEN.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(42, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
