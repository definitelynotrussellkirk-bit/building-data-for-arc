from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import re
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs as _canonical_pairs, canonical_path, find_root


gen = importlib.import_module("puzzle_generators.per_puzzle.fbf36c193fa6.generator")

TASK_HOME = Path(__file__).resolve().parents[1]
LIB_ROOT = find_root(__file__)
TASK_ID = "fbf36c193fa6"
CANONICAL_PATH = canonical_path(LIB_ROOT)


def _base_path() -> Path:
    for relative in (
        "data/base/solutions/training/212895b5__fbf36c193fa6.json",
        "shared/data/base/solutions/training/212895b5__fbf36c193fa6.json",
    ):
        candidate = LIB_ROOT / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"missing base authority under {LIB_ROOT}")


BASE_PATH = _base_path()


def canonical_pairs(task_id: str):
    return _canonical_pairs(task_id, root=LIB_ROOT, labeled_only=True)


def _canonical_row() -> dict:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(re.sub(r"\s+", " ", source).strip().encode()).hexdigest()[:12]


def _pair(grid: list[list[int]]) -> dict:
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_pin_canonical_pairs_and_selected_source_are_exact():
    row = _canonical_row()
    pairs = canonical_pairs(TASK_ID)
    assert gen.VERSION == "4.1.0"
    assert gen.RULE_HASH == _normalized_rule_hash(row["program_solution"])
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original

    target = json.loads(BASE_PATH.read_text(encoding="utf-8"))["racket_target"]
    assert target["target_code"] == row["program_solution"]
    assert target["target_code_role"] == "selected_task_rule"
    assert target["raw_code_role"] == "archival_executable_source"
    assert target["raw_code"] != target["target_code"]


def test_mixed_profile_exposes_every_blocker_branch_and_open_controls():
    mixed = gen.generate(1776, 1, difficulty="medium", barrier_profile="mixed")
    features = gen._features_for_witness(mixed)
    assert gen.observe_overrides(mixed)["barrier_profile"] == "mixed"
    assert {"direct_gray", "corner_pair", "edge"} <= set(features["red_reasons"])
    assert {
        "start_gray",
        "intermediate_gray",
        "diagonal_gray",
        "edge",
    } <= set(features["yellow_reasons"])

    open_grid = gen.generate(1776, 0, difficulty="medium", barrier_profile="open")
    open_features = gen._features_for_witness(open_grid)
    assert open_features["red_reasons"] == ["edge"] * 4
    assert open_features["yellow_reasons"] == ["edge"] * 4

    opposite = gen.generate(1776, 2, difficulty="medium", barrier_profile="mixed")
    lesson = [open_grid, mixed, opposite]
    for name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in lesson), name
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness_grid = next(grid for grid in lesson if gen.SEMANTIC_WITNESSES[witness_name](grid))
        answer = gen.rule_mirror(witness_grid)
        for rival_name in rival_names:
            assert gen.SEMANTIC_RIVALS[rival_name](witness_grid) != answer


def test_every_sliding_lesson_window_is_identifiable():
    grids = [gen.generate(2400, index, difficulty="hard") for index in range(12)]
    profiles = [gen.observe_overrides(grid)["barrier_profile"] for grid in grids]
    for start in range(8):
        window = profiles[start : start + gen.EXAMPLES_NEEDED]
        assert set(window) == {"open", "mixed"}
        demos = [_pair(grid) for grid in grids[start : start + gen.EXAMPLES_NEEDED]]
        query = _pair(grids[start + gen.EXAMPLES_NEEDED])
        assert gen.lesson_identifiable(demos, query) == []


def test_override_full_boundaries_are_exact_observable_and_band_safe():
    case_index = 0
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (16, 23):
            for grid_w in (16, 23):
                for n_gray in (20, 64):
                    for row_band in ("upper", "center", "lower"):
                        for col_band in ("left", "center", "right"):
                            for profile in ("open", "mixed"):
                                requested = {
                                    "grid_h": grid_h,
                                    "grid_w": grid_w,
                                    "n_gray": n_gray,
                                    "square_row_band": row_band,
                                    "square_col_band": col_band,
                                    "barrier_profile": profile,
                                }
                                grid = gen.generate(
                                    10_000 + case_index,
                                    case_index % 13,
                                    difficulty=difficulty,
                                    **requested,
                                )
                                assert gen.self_check(grid) == []
                                assert gen.observe_overrides(grid) == requested
                                case_index += 1

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)


def test_replay_is_fresh_deterministic_input_pure_and_global_rng_pure():
    random.seed(20260726)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    pristine = copy.deepcopy(first)
    output = gen.rule_mirror(first)
    assert first == pristine
    assert random.getstate() == state

    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second
    assert output != second


def test_structural_mutations_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_outputs_preserve_input_roles_and_fire_both_ray_colors():
    for index in range(24):
        grid = gen.generate(50_000 + index, index, difficulty="medium")
        output = gen.rule_mirror(grid)
        assert len(output) == len(grid)
        assert all(len(out_row) == len(in_row) for in_row, out_row in zip(grid, output))
        assert any(2 in row for row in output)
        assert any(4 in row for row in output)
        for row in range(len(grid)):
            for col in range(len(grid[0])):
                if grid[row][col] in (5, 8):
                    assert output[row][col] == grid[row][col]
