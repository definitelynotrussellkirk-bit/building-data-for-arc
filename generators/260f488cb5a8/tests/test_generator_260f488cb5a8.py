from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest


GEN = importlib.import_module("puzzle_generators.per_puzzle.260f488cb5a8.generator")
ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "260f488cb5a8"


def _grid(rows: list[str]) -> list[list[int]]:
    return [[int(value) for value in row] for row in rows]


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    row = _canonical_row()
    raw_pairs = [*row["train"], row["test"]]
    return [
        {"input": _grid(pair["input"]), "output": _grid(pair["output"])}
        for pair in raw_pairs
    ]


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_pin_and_all_canonical_pairs_are_exact() -> None:
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "70d01868db22"
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_four_profile_lesson_refutes_every_named_rival() -> None:
    grids = [GEN.generate(1701, index, difficulty="medium") for index in range(4)]
    assert [GEN.schedule_profile(1701, index) for index in range(4)] == list(
        GEN.SCENE_PROFILES
    )
    assert {GEN.observe_overrides(grid)["scene_profile"] for grid in grids} == set(
        GEN.SCENE_PROFILES
    )
    assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)

    demos = [_pair(grid) for grid in grids]
    query = _pair(GEN.generate(1701, 4, difficulty="medium"))
    assert GEN.lesson_identifiable(demos, query) == []

    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        witness_grid = next(
            grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)
        )
        answer = GEN.rule_mirror(witness_grid)
        for rival_name in rival_names:
            assert GEN.SEMANTIC_RIVALS[rival_name](witness_grid) != answer


def test_every_sliding_four_example_window_is_identifiable() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(12):
            lesson = [
                _pair(GEN.generate(8000 + start, start + offset, difficulty=difficulty))
                for offset in range(5)
            ]
            assert GEN.lesson_identifiable(lesson[:4], lesson[4]) == []


def test_boundary_overrides_are_exact_observable_and_band_safe() -> None:
    case_index = 0
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (4, 9):
            for grid_w in (6, 10):
                for scene_profile in GEN.SCENE_PROFILES:
                    requested = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "scene_profile": scene_profile,
                    }
                    grid = GEN.generate(
                        9000 + case_index,
                        case_index % 13,
                        difficulty=difficulty,
                        **requested,
                    )
                    assert GEN.self_check(grid) == []
                    assert GEN.observe_overrides(grid) == requested
                    case_index += 1

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, bogus_axis=3)


def test_replay_is_fresh_deterministic_global_rng_pure_and_band_specific() -> None:
    random.seed(20260725)
    state = random.getstate()
    first = GEN.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second

    band_outputs = {
        difficulty: GEN.generate(222, 17, difficulty=difficulty)
        for difficulty in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in band_outputs.values()}) == 3


def test_structural_impostors_are_rejected() -> None:
    mutations = {
        "all_zero": [[0] * 6 for _ in range(4)],
        "single_active_row": [
            [1, 0, 2, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ],
        "one_color_only": [
            [1, 0, 1, 0, 0, 0],
            [0, 1, 0, 1, 0, 0],
            [1, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0],
        ],
        "solid_active_rows": [
            [1, 2, 3, 4, 5, 6],
            [6, 5, 4, 3, 2, 1],
            [1, 3, 5, 2, 4, 6],
            [0, 0, 0, 0, 0, 0],
        ],
        "jagged": [[1, 0, 2, 0, 0, 0], [3, 0, 4]],
    }
    for name, grid in mutations.items():
        assert GEN.self_check(grid), name
