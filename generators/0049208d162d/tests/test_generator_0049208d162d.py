from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.0049208d162d.generator")

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "0049208d162d"
BASE_PATH = ROOT / "data/base/solutions/banks/884454e62c49/M27__0049208d162d.json"


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


def test_rule_pin_canonical_pairs_and_selected_source_are_exact():
    row = _canonical_row()
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "b21bae0aa3d4"
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]

    target = json.loads(BASE_PATH.read_text(encoding="utf-8"))["racket_target"]
    assert target["target_code"] == row["program_solution"]
    assert target["raw_code"] != target["target_code"]  # preserved archival source


def test_scheduled_lesson_covers_topology_branches_and_refutes_rivals():
    grids = [gen.generate(1701, index, difficulty="medium") for index in range(4)]
    observed = [gen.observe_overrides(grid) for grid in grids]
    assert [gen.schedule_profile(1701, index) for index in range(4)] == [1, 2, 3, 0]
    assert {item["n_holed"] for item in observed} == {1, 2}
    assert {item["n_solid"] for item in observed} == {1, 2}
    assert {item["color_policy"] for item in observed} == {"distinct", "shared"}
    assert {item["near_miss"] for item in observed} == {"on", "off"}

    for name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), name

    demos = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]
    assert gen.lesson_identifiable(demos[:3], demos[3]) == []
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness_grid = next(grid for grid in grids if gen.SEMANTIC_WITNESSES[witness_name](grid))
        answer = gen.rule_mirror(witness_grid)
        for rival_name in rival_names:
            assert gen.SEMANTIC_RIVALS[rival_name](witness_grid) != answer


def test_override_full_boundaries_are_exact_observable_and_band_safe():
    for difficulty in ("easy", "medium", "hard"):
        case_index = 0
        for grid_h in (8, 14):
            for grid_w in (9, 14):
                for n_holed in (1, 2):
                    for n_solid in (1, 2):
                        for color_policy in ("distinct", "shared"):
                            for near_miss in ("on", "off"):
                                requested = {
                                    "grid_h": grid_h,
                                    "grid_w": grid_w,
                                    "n_holed": n_holed,
                                    "n_solid": n_solid,
                                    "color_policy": color_policy,
                                    "near_miss": near_miss,
                                }
                                grid = gen.generate(
                                    9000 + case_index,
                                    case_index % 11,
                                    difficulty=difficulty,
                                    **requested,
                                )
                                assert gen.self_check(grid) == []
                                assert gen.observe_overrides(grid) == requested
                                case_index += 1

    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)


def test_replay_is_fresh_deterministic_and_global_rng_pure():
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


def test_structural_mutations_are_rejected_and_canonical_diagonals_allowed():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name

    # The second canonical train input contains a diagonal-only same-color
    # component contact.  `objects` is 4-connected, so diagonal contact must
    # remain lawful while edge-sharing objects are rejected.
    second_train = _canonical_row()["train"][1]["input"]
    assert gen.self_check(second_train) == []


def test_rule_mirror_keeps_only_components_with_enclosed_bbox_background():
    grid = gen.generate(
        31415,
        9,
        difficulty="medium",
        n_holed=2,
        n_solid=2,
        color_policy="shared",
        near_miss="on",
    )
    analysis = gen._analyze(grid)
    output = gen.rule_mirror(grid)
    assert output == analysis["output"]
    for component in analysis["holed"]:
        assert all(output[row][col] == component["color"] for row, col in component["cells"])
    for component in analysis["solid"]:
        assert all(output[row][col] == 0 for row, col in component["cells"])
