"""Focused semantic regressions for ARC generator 348efda982ab."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import purity_body, rule_application

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "348efda982ab"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
BASE_PATH = ROOT / "data/base/solutions/banks/445ef4275a64/S21_M6__348efda982ab.json"


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return list(row["train"]) + list(test)


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _non_intersection_internal_wall(grid):
    analysis = MODULE._analysis(grid)
    row_separators = [0]
    for height in analysis["row_heights"]:
        row_separators.append(row_separators[-1] + height + 1)
    col_separators = [0]
    for width in analysis["col_widths"]:
        col_separators.append(col_separators[-1] + width + 1)
    for row in range(1, len(grid) - 1):
        for col in range(1, len(grid[0]) - 1):
            if (
                grid[row][col] in {1, 9}
                and ((row in row_separators) ^ (col in col_separators))
            ):
                return row, col
    raise AssertionError("no internal wall cell found")


def test_version_rule_hash_and_axes_are_pinned_and_honest():
    row = _canonical_row()
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    assert MODULE.VERSION == "4.0.0"
    assert set(MODULE.AXES) == {"room_rows", "room_cols"}
    assert MODULE.RULE_HASH == "abbcb1f89b47"
    assert _normalized_hash(row["program_solution"]) == MODULE.RULE_HASH
    assert _normalized_hash(base["racket_target"]["target_code"]) == MODULE.RULE_HASH


def test_all_canonical_pairs_are_accepted_and_mirrored_exactly_and_purely():
    assert len(_pairs()) == 3
    for pair in _pairs():
        source = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(source)
        assert MODULE.self_check(source) == []
        assert MODULE.rule_mirror(source) == pair["output"]
        assert source == snapshot


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    ("room_rows", "room_cols"),
    [(1, 2), (1, 4), (2, 1), (4, 1), (2, 2), (4, 4)],
)
def test_axis_boundaries_are_exact_and_observable(difficulty, room_rows, room_cols):
    grid = MODULE.generate(
        1771,
        1991,
        difficulty=difficulty,
        room_rows=room_rows,
        room_cols=room_cols,
    )
    assert MODULE.self_check(grid) == []
    assert MODULE.observe_overrides(grid) == {
        "room_rows": room_rows,
        "room_cols": room_cols,
    }


def test_incompatible_and_unknown_controls_fail_loudly():
    with pytest.raises(ValueError, match="only one room"):
        MODULE.generate(0, 0, room_rows=1, room_cols=1)
    with pytest.raises(ValueError, match="outside 1..4"):
        MODULE.generate(0, 0, room_rows=5)
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(0, 0, texture="warm")
    with pytest.raises(ValueError, match="difficulty"):
        MODULE.generate(0, 0, difficulty="extreme")


def test_generation_is_deterministic_fresh_input_pure_and_global_rng_pure():
    random.seed(918273)
    state = random.getstate()
    first = MODULE.generate(91, 17, difficulty="hard")
    snapshot = copy.deepcopy(first)
    second = MODULE.generate(91, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert random.getstate() == state
    assert MODULE.self_check(first) == []
    assert first == snapshot
    assert MODULE.rule_mirror(first) != first
    assert first == snapshot
    first[0][0] = 9
    assert MODULE.generate(91, 17, difficulty="hard") == snapshot


def test_structural_checker_rejects_targeted_impostors():
    base = MODULE.generate(
        3201, 51, difficulty="medium", room_rows=3, room_cols=3
    )

    border_breach = copy.deepcopy(base)
    border_breach[0][1] = 0

    marker_on_wall = copy.deepcopy(base)
    wall_row, wall_col = _non_intersection_internal_wall(marker_on_wall)
    marker_on_wall[wall_row][wall_col] = 3

    separator_breach = copy.deepcopy(base)
    wall_row, wall_col = _non_intersection_internal_wall(separator_breach)
    separator_breach[wall_row][wall_col] = 0

    door_inside_room = copy.deepcopy(base)
    interior = next(
        (row, col)
        for row, values in enumerate(door_inside_room)
        for col, value in enumerate(values)
        if value == 0
    )
    door_inside_room[interior[0]][interior[1]] = 7

    door_at_intersection = copy.deepcopy(base)
    analysis = MODULE._analysis(door_at_intersection)
    internal_row = analysis["row_heights"][0] + 1
    internal_col = analysis["col_widths"][0] + 1
    door_at_intersection[internal_row][internal_col] = 7

    impostors = {
        "border_breach": border_breach,
        "marker_on_wall": marker_on_wall,
        "separator_breach": separator_breach,
        "door_inside_room": door_inside_room,
        "door_at_intersection": door_at_intersection,
    }
    for name, grid in impostors.items():
        assert MODULE.self_check(grid), name
        assert MODULE.observe_overrides(grid) == {}, name


def test_ordinary_distribution_reaches_all_semantic_branches_and_varies():
    facts = {
        "row_strip": False,
        "col_strip": False,
        "variable_heights": False,
        "variable_widths": False,
        "connected": False,
        "disconnected": False,
        "degree_zero_match": False,
        "degree_zero_mismatch": False,
        "positive_match": False,
        "positive_mismatch": False,
        "wall_9": False,
    }
    frozen_inputs = set()
    frozen_outputs = set()
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        for offset in range(220):
            grid = MODULE.generate(
                40_000 + band_index * 10_000 + offset,
                97 * offset + band_index,
                difficulty=difficulty,
            )
            analysis = MODULE._analysis(grid)
            assert analysis["errors"] == []
            frozen_inputs.add(tuple(map(tuple, grid)))
            frozen_outputs.add(tuple(map(tuple, analysis["output"])))
            facts["row_strip"] |= analysis["room_rows"] == 1
            facts["col_strip"] |= analysis["room_cols"] == 1
            facts["variable_heights"] |= len(set(analysis["row_heights"])) > 1
            facts["variable_widths"] |= len(set(analysis["col_widths"])) > 1
            facts["connected"] |= analysis["connected"]
            facts["disconnected"] |= not analysis["connected"]
            facts["wall_9"] |= analysis["has_wall_9"]
            for room in analysis["rooms"]:
                if room["degree"] == 0 and room["matches"]:
                    facts["degree_zero_match"] = True
                if room["degree"] == 0 and not room["matches"]:
                    facts["degree_zero_mismatch"] = True
                if room["degree"] > 0 and room["matches"]:
                    facts["positive_match"] = True
                if room["degree"] > 0 and not room["matches"]:
                    facts["positive_mismatch"] = True
    assert all(facts.values()), facts
    assert len(frozen_inputs) >= 640
    assert len(frozen_outputs) >= 620


def test_seed_and_sample_index_both_materially_change_generation():
    by_seed = {
        tuple(map(tuple, MODULE.generate(seed, 13, difficulty="medium")))
        for seed in range(80)
    }
    by_sample = {
        tuple(map(tuple, MODULE.generate(13, sample, difficulty="medium")))
        for sample in range(80)
    }
    assert len(by_seed) >= 75
    assert len(by_sample) >= 75


def test_checker_rejects_malformed_types_shapes_and_colors():
    assert MODULE.self_check([])
    assert MODULE.self_check([[1, 1], [1]])
    assert MODULE.self_check([[True, True], [True, True]])
    assert MODULE.self_check([[2, 2], [2, 2]])
    assert MODULE.self_check([[1] * 31 for _ in range(31)])


def test_real_racket_rule_matches_canonical_and_generated_inputs_with_aba_purity():
    source = _canonical_row()["program_solution"]
    bridge = RacketBridge()
    try:
        for pair in _pairs():
            original = copy.deepcopy(pair["input"])
            assert bridge.eval_text(rule_application(source, original)) == pair["output"]
            assert original == pair["input"]

        generated = []
        for band_index, difficulty in enumerate(("easy", "medium", "hard")):
            for offset in range(4):
                grid = MODULE.generate(
                    770_000 + band_index * 100 + offset,
                    301 + offset,
                    difficulty=difficulty,
                )
                generated.append(grid)
                assert bridge.eval_text(rule_application(source, grid)) == MODULE.rule_mirror(grid)

        probe = bridge.eval_text(purity_body(source, generated[0], generated[-1]))
        assert probe == [
            MODULE.rule_mirror(generated[0]),
            MODULE.rule_mirror(generated[0]),
            generated[0],
        ]
    finally:
        bridge.shutdown()
