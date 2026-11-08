"""Focused semantic and regression tests for generator db1284892611."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import shutil
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import purity_body, rule_application

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.db1284892611.generator"
)
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/base/solutions/banks/e14e4b5836bc/H98__db1284892611.json"


def _canonical_row() -> dict:
    path = ROOT / "data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {GEN.TASK_ID}")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"]
    return [*row["train"], *(test if isinstance(test, list) else [test])]


def _pair(grid: list[list[int]]) -> dict:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _normalized_rule_hash(source: str) -> str:
    normalized = " ".join(source.split())
    return hashlib.sha256(normalized.encode()).hexdigest()[:12]


def test_rule_pin_selected_authority_and_every_canonical_pair_are_exact() -> None:
    row = _canonical_row()
    base = json.loads(BASE.read_text(encoding="utf-8"))
    selected = base["racket_target"]["target_code"]

    assert GEN.VERSION == "4.0.0"
    assert selected == row["program_solution"]
    assert GEN.RULE_HASH == _normalized_rule_hash(selected) == "f599f53cd1ea"

    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.skipif(shutil.which("racket") is None, reason="racket is not installed")
def test_real_racket_matches_canonical_generated_and_rejected_recombination() -> None:
    row = _canonical_row()
    source = row["program_solution"]
    pairs = _canonical_pairs()
    bridge = RacketBridge(timeout=30, max_calls_before_restart=128)
    try:
        for pair in pairs:
            grid = copy.deepcopy(pair["input"])
            before = copy.deepcopy(grid)
            assert bridge.eval_text(rule_application(source, grid)) == pair["output"]
            assert grid == before

        for difficulty in ("easy", "medium", "hard"):
            for sample_index in range(4):
                grid = GEN.generate(702_928, sample_index, difficulty=difficulty)
                before = copy.deepcopy(grid)
                assert bridge.eval_text(rule_application(source, grid)) == GEN.rule_mirror(grid)
                assert grid == before

        probe = bridge.eval_text(
            purity_body(source, pairs[0]["input"], pairs[1]["input"])
        )
        assert probe == [pairs[0]["output"], pairs[0]["output"], pairs[0]["input"]]

        recombined, replacement = GEN.negative_recombination_fixture()
        assert replacement not in {
            value for row_values in GEN.generate(91_337, 1, difficulty="medium")
            for value in row_values
        }
        assert any("monochrome" in reason for reason in GEN.self_check(recombined))
        before = copy.deepcopy(recombined)
        result = bridge.eval_text(rule_application(source, recombined))
        assert isinstance(result, list) and result and result[0]
        assert recombined == before
    finally:
        bridge.shutdown()


def test_four_phase_schedule_is_valid_observable_and_semantically_decisive() -> None:
    profiles: set[str] = set()
    witness_counts = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(16):
            grid = GEN.generate(12_849, sample_index, difficulty=difficulty)
            assert GEN.self_check(grid, difficulty=difficulty) == []
            assert GEN.strict_canonical_like(grid) == []
            assert GEN.observe_overrides(grid)
            profiles.add(GEN.schedule_profile(12_849, sample_index, difficulty))
            truth = GEN.rule_mirror(grid)
            for name, witness in GEN.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    witness_counts[name] += 1
                    assert any(
                        GEN.SEMANTIC_RIVALS[rival](grid) != truth
                        for rival in GEN.WITNESS_RIVALS[name]
                    )
    assert profiles == set(GEN.SCHEDULE_PROFILES)
    assert all(count > 0 for count in witness_counts.values()), witness_counts


def test_every_sliding_lesson_window_is_identifiable() -> None:
    for difficulty_index, difficulty in enumerate(("easy", "medium", "hard")):
        grids = [
            GEN.generate(44_000 + difficulty_index, index, difficulty=difficulty)
            for index in range(16)
        ]
        for start in range(12):
            demos = [_pair(grid) for grid in grids[start : start + GEN.EXAMPLES_NEEDED]]
            query = _pair(grids[start + GEN.EXAMPLES_NEEDED])
            assert GEN.lesson_identifiable(demos, query) == []


def test_override_boundaries_are_exact_and_unknown_keys_reject() -> None:
    cases = [
        {
            "grid_h": 10,
            "grid_w": 10,
            "n": 2,
            "palette_extra": 0,
            "palette_layout": "left",
            "size_order": "ascending",
            "body_color_pattern": "all_same",
            "palette_overlap": "none",
        },
        {
            "grid_h": 13,
            "grid_w": 16,
            "n": 5,
            "palette_extra": 2,
            "palette_layout": "right",
            "size_order": "descending",
            "body_color_pattern": "mixed",
            "palette_overlap": "one",
        },
        {
            "grid_h": 11,
            "grid_w": 13,
            "n": 4,
            "palette_extra": 1,
            "palette_layout": "spaced",
            "size_order": "ascending",
            "body_color_pattern": "mixed",
            "palette_overlap": "none",
        },
    ]
    for difficulty in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = GEN.generate(
                8_000 + index,
                100 + index,
                difficulty=difficulty,
                **requested,
            )
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == requested

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", 9),
        ("grid_h", 14),
        ("grid_w", 9),
        ("grid_w", 17),
        ("n", 1),
        ("n", 6),
        ("palette_extra", -1),
        ("palette_extra", 3),
        ("palette_layout", "middle"),
        ("size_order", "random"),
        ("body_color_pattern", "unique"),
        ("palette_overlap", "all"),
    ],
)
def test_out_of_domain_overrides_reject_loudly(axis: str, value: object) -> None:
    with pytest.raises((ValueError, AssertionError)):
        GEN.generate(1, 0, **{axis: value})


def test_replay_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(20260728)
    state = random.getstate()
    first = GEN.generate(77, 91, difficulty="hard")
    pristine = copy.deepcopy(first)
    output = GEN.rule_mirror(first)
    assert first == pristine
    assert random.getstate() == state

    second = GEN.generate(77, 91, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0 if first[0][0] else 9
    assert second == GEN.generate(77, 91, difficulty="hard")
    assert output == GEN.rule_mirror(second)


def test_named_mutation_fixtures_are_all_rejected() -> None:
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert GEN.self_check(grid), name
