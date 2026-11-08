from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.e8ae3b180a0f.generator")

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "e8ae3b180a0f"
BASE_PATH = ROOT / "data/base/solutions/banks/e1d39660275b/hard_n02__e8ae3b180a0f.json"


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [pair for split in ("train", "test") for pair in row[split]]


def _normalized_rule_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()[:12]


def test_rule_pin_all_canonical_pairs_and_scan_order_exception():
    row = _canonical_row()
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == _normalized_rule_hash(row["program_solution"])
    assert gen.RULE_HASH == "e8c06275e008"

    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original

    # Canonical train #2 contains two D4-congruent candidates.  The selected
    # Racket source scans objects in row-major/top-left order and chooses color
    # 3 first; generated lessons intentionally avoid this answer-equivalent
    # canonical tie.
    ambiguous = gen._analysis(row["train"][2]["input"])
    assert [obj["color"] for obj in ambiguous["matches"]] == [3, 6]
    assert ambiguous["match"]["color"] == 3
    assert gen.rule_mirror(row["train"][2]["input"]) == row["train"][2]["output"]

    authority = json.loads(BASE_PATH.read_text(encoding="utf-8"))["racket_target"]
    assert authority["target_code"] == row["program_solution"]
    assert authority["raw_code"] != authority["target_code"]


def test_ordinary_distribution_has_unique_same_count_match_and_branch_coverage():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(40):
            grids = [gen.generate(seed, index, difficulty=difficulty) for index in range(3)]
            analyses = [gen._analysis(grid) for grid in grids]
            assert {info["match_rank"] for info in analyses} == {0, 1, 2}
            assert {info["match_color_rank"] for info in analyses} == {0, 1, 2}
            assert any(info["reflection_required"] for info in analyses)
            for grid, info in zip(grids, analyses):
                assert gen.self_check(grid) == []
                assert gen._ordinary_lesson_errors(grid) == []
                assert len(info["matches"]) == 1
                guide_n = len(info["guide"]["cells"])
                assert all(len(obj["cells"]) == guide_n for obj in info["candidates"])
                assert info["match"]["shape"] != info["guide"]["shape"]

            demos = [
                {"input": grid, "output": gen.rule_mirror(grid)}
                for grid in grids
            ]
            query_grid = gen.generate(seed, 3, difficulty=difficulty)
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []


def test_semantic_witnesses_really_refute_their_named_rivals():
    grids = [gen.generate(seed, index, difficulty="medium") for seed in range(6) for index in range(6)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness_grid = next(
            grid for grid in grids if gen.SEMANTIC_WITNESSES[witness_name](grid)
        )
        expected = gen.rule_mirror(witness_grid)
        for rival_name in rival_names:
            assert gen.SEMANTIC_RIVALS[rival_name](witness_grid) != expected


def test_override_boundaries_are_composable_exact_observable_and_band_safe():
    case_index = 0
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (9, 15):
            for grid_w in (12, 16):
                for guide_size in (3, 4, 5):
                    for match_color in (3, 4, 5, 6):
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "guide_size": guide_size,
                            "match_color": match_color,
                        }
                        grid = gen.generate(
                            50_000 + case_index,
                            case_index % 13,
                            difficulty=difficulty,
                            **requested,
                        )
                        assert gen._ordinary_lesson_errors(grid) == []
                        assert gen.observe_overrides(grid) == requested
                        case_index += 1

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)
    with pytest.raises(ValueError, match="unsupported difficulty"):
        gen.generate(1, 2, difficulty="nightmare")


def test_replay_returns_fresh_objects_and_preserves_global_rng_state():
    random.seed(20260725)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_structural_mutations_and_ordinary_ambiguity_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name

    valid = gen.generate(1776, 0, difficulty="medium", guide_size=4)
    info = gen._analysis(valid)
    tied = copy.deepcopy(valid)
    distractor = next(obj for obj in info["candidates"] if obj is not info["match"])
    for r, c in distractor["cells"]:
        tied[r][c] = 0
    shape = gen._normalize(info["match"]["shape"])
    row, col = distractor["r1"], distractor["c1"]
    for dr, dc in shape:
        tied[row + dr][col + dc] = distractor["color"]
    assert gen.self_check(tied) == []  # lawful under canonical scan-order semantics
    assert len(gen._analysis(tied)["matches"]) == 2
    assert gen._ordinary_lesson_errors(tied)  # but rejected from generated curriculum
