from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge, RacketBridgeError
from scripts.generator_module_loader import load_module_from_path
from scripts.rule_smoke import purity_body, rule_application

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "b47adc50b675"
GENERATOR_PATH = ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/6bdef6f37fa3/S7_E5__b47adc50b675.json"
)
MODULE = load_module_from_path(f"test_generator_{TASK_ID}_module", GENERATOR_PATH)


def _canonical_rows() -> list[dict]:
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    assert len(rows) == 1
    return rows


def _normalize_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return grid


def _all_pairs() -> list[dict]:
    pairs = []
    for row in _canonical_rows():
        for split in ("train", "test"):
            raw = row.get(split) or []
            if isinstance(raw, dict):
                raw = [raw]
            pairs.extend(
                {"input": _normalize_grid(pair["input"]), "output": _normalize_grid(pair["output"])}
                for pair in raw
            )
    return pairs


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _component_cells(grid: list[list[int]]) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 3
    }


def test_metadata_rule_hash_and_selected_rule_match_canonical() -> None:
    canonical = _canonical_rows()[0]["program_solution"]
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    target = base["racket_target"]
    assert MODULE.VERSION == "4.0.0"
    assert MODULE.RULE_HASH == "df98ae7438e1"
    assert MODULE.RULE_HASH == _normalized_rule_hash(canonical)
    assert target["target_code"] == canonical
    assert target["raw_code"] != canonical


def test_all_canonical_inputs_pass_and_canonical_rule_is_pure_reentrant() -> None:
    canonical = _canonical_rows()[0]["program_solution"]
    pairs = _all_pairs()
    assert len(pairs) == 3
    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            assert MODULE.self_check(pair["input"]) == []
            assert bridge.eval_text(rule_application(canonical, pair["input"])) == pair["output"]
            assert pair["input"] == before
        probe = bridge.eval_text(
            purity_body(canonical, pairs[0]["input"], pairs[1]["input"])
        )
        assert probe[0] == pairs[0]["output"]
        assert probe[1] == pairs[0]["output"]
        assert probe[2] == pairs[0]["input"]
    finally:
        bridge.shutdown()


def test_determinism_fresh_returns_and_process_rng_state() -> None:
    state = random.getstate()
    first = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert MODULE.generate(901, 17, difficulty="hard") == second


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_override_boundaries_are_observable(difficulty: str) -> None:
    cases = (
        {
            "shape_id": 0,
            "transpose": False,
            "grid_h": 5,
            "grid_w": 6,
            "row_offset": 1,
            "col_offset": 1,
        },
        {
            "shape_id": 14,
            "transpose": True,
            "grid_h": 5,
            "grid_w": 6,
            "row_offset": 2,
            "col_offset": 4,
        },
        {
            "shape_id": 12,
            "transpose": False,
            "grid_h": 14,
            "grid_w": 16,
            "row_offset": 12,
            "col_offset": 13,
        },
        {
            "shape_id": 3,
            "transpose": True,
            "grid_h": 14,
            "grid_w": 16,
            "row_offset": 11,
            "col_offset": 14,
        },
    )
    for index, overrides in enumerate(cases):
        grid = MODULE.generate(
            1800 + index,
            700 + index,
            difficulty=difficulty,
            **overrides,
        )
        assert MODULE.self_check(grid) == []
        assert MODULE.observe_overrides(grid) == overrides

    with pytest.raises(ValueError, match="incompatible"):
        MODULE.generate(
            1,
            2,
            difficulty=difficulty,
            transpose=True,
            grid_h=14,
            row_offset=12,
        )
    with pytest.raises(ValueError, match="incompatible"):
        MODULE.generate(
            1,
            2,
            difficulty=difficulty,
            transpose=False,
            grid_w=16,
            col_offset=14,
        )
    with pytest.raises(TypeError, match="unknown override"):
        MODULE.generate(1, 2, difficulty=difficulty, texture="warm")


def test_complete_shape_codomain_is_valid_distinct_and_rule_exact() -> None:
    canonical = _canonical_rows()[0]["program_solution"]
    seen = set()
    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        for transpose in (False, True):
            for shape_id in range(15):
                grid = MODULE.generate(
                    4400 + shape_id,
                    9,
                    difficulty="medium",
                    shape_id=shape_id,
                    transpose=transpose,
                    grid_h=10,
                    grid_w=12,
                    row_offset=3,
                    col_offset=4,
                )
                assert MODULE.self_check(grid) == []
                observed = MODULE.observe_overrides(grid)
                assert observed["shape_id"] == shape_id
                assert observed["transpose"] is transpose
                cells = _component_cells(grid)
                top = min(row for row, _ in cells)
                left = min(col for _, col in cells)
                normalized = frozenset((row - top, col - left) for row, col in cells)
                seen.add(normalized)
                assert bridge.eval_text(rule_application(canonical, grid)) == MODULE.rule_mirror(grid)
    finally:
        bridge.shutdown()
    assert len(seen) == 30


def test_self_check_rejects_targeted_impostors() -> None:
    valid = MODULE.generate(
        53,
        8,
        difficulty="medium",
        shape_id=12,
        transpose=False,
        grid_h=9,
        grid_w=11,
        row_offset=3,
        col_offset=4,
    )
    assert MODULE.self_check(valid) == []

    no_component = [[0 for _ in row] for row in valid]
    assert MODULE.self_check(no_component)

    multiple_components = copy.deepcopy(valid)
    multiple_components[1][1] = 3
    assert "exactly one" in MODULE.self_check(multiple_components)[0]

    at_origin = MODULE.rule_mirror(valid)
    assert "offset" in MODULE.self_check(at_origin)[0]

    wrong_color = copy.deepcopy(valid)
    for row, col in _component_cells(wrong_color):
        wrong_color[row][col] = 5
    assert "only background" in MODULE.self_check(wrong_color)[0]

    too_small = [[0 for _ in row] for row in valid]
    too_small[2][2] = too_small[2][3] = too_small[3][2] = 3
    assert "four to six" in MODULE.self_check(too_small)[0]

    line_shape = [[0 for _ in row] for row in valid]
    for col in range(2, 6):
        line_shape[3][col] = 3
    assert "bounding box" in MODULE.self_check(line_shape)[0]


def test_negative_recombinations_separate_lesson_validity_from_oracle_domain() -> None:
    canonical = _canonical_rows()[0]["program_solution"]
    valid = MODULE.generate(
        91,
        4,
        difficulty="medium",
        shape_id=9,
        transpose=False,
        grid_h=10,
        grid_w=12,
        row_offset=5,
        col_offset=6,
    )

    # The distribution rejects two possible answer-bearing components, while
    # the permissive Racket program still executes by selecting its first object.
    multiple = copy.deepcopy(valid)
    multiple[1][1] = multiple[1][2] = multiple[2][1] = multiple[2][2] = 3
    assert MODULE.self_check(multiple)

    # Recoloring the sole component removes the required green feature from
    # every remaining scene part.  The lesson checker rejects it and the rule's
    # `(first ...)` has no color-3 object, so oracle execution also fails.
    absent = copy.deepcopy(valid)
    for row, col in _component_cells(absent):
        absent[row][col] = 5
    assert MODULE.self_check(absent)

    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        multiple_output = bridge.eval_text(rule_application(canonical, multiple))
        assert isinstance(multiple_output, list) and multiple_output
        with pytest.raises(RacketBridgeError):
            bridge.eval_text(rule_application(canonical, absent))
    finally:
        bridge.shutdown()


def test_archival_raw_rule_has_execution_parity_on_canonical_and_generated_inputs() -> None:
    canonical = _canonical_rows()[0]["program_solution"]
    archival = json.loads(BASE_PATH.read_text(encoding="utf-8"))["racket_target"]["raw_code"]
    inputs = [pair["input"] for pair in _all_pairs()]
    inputs.extend(
        MODULE.generate(8000 + seed, seed, difficulty=band)
        for band in ("easy", "medium", "hard")
        for seed in range(10)
    )
    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        for grid in inputs:
            assert bridge.eval_text(rule_application(archival, grid)) == bridge.eval_text(
                rule_application(canonical, grid)
            )
    finally:
        bridge.shutdown()
