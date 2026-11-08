from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.coder_synth_verify import _as_pairs, _norm_grid
from scripts.rule_smoke import purity_body, rule_application

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "491a4eb76930"
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.491a4eb76930.generator"
)
BASE_PATHS = (
    ROOT / "data/base/solutions/training/692cd3b6__491a4eb76930.json",
    ROOT / "data/base/solutions/augmented/692cd3b6__57e05b5c4422.json",
)


def _canonical_rows() -> list[dict]:
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    assert rows
    return rows


def _canonical_rule() -> str:
    rules = {row["program_solution"] for row in _canonical_rows()}
    assert len(rules) == 1
    return rules.pop()


def _all_pairs() -> list[dict]:
    pairs = []
    for row in _canonical_rows():
        for pair in _as_pairs(row.get("train")) + _as_pairs(row.get("test")):
            if isinstance(pair, dict):
                pairs.append({
                    "input": _norm_grid(pair.get("input")),
                    "output": _norm_grid(pair.get("output")),
                })
    return pairs


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_metadata_and_task_local_authorities_are_exactly_synchronized() -> None:
    canonical = _canonical_rule()
    assert MODULE.VERSION == "4.0.0"
    assert MODULE.RULE_HASH == "c4ccdf332cee"
    assert MODULE.RULE_HASH == _normalized_rule_hash(canonical)
    for path in BASE_PATHS:
        base = json.loads(path.read_text(encoding="utf-8"))
        assert base["racket_target"]["raw_code"] == canonical
        assert base["racket_target"]["target_code"] == canonical


def test_all_canonical_inputs_are_owned_and_python_mirror_matches() -> None:
    for pair in _all_pairs():
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.strict_canonical_like(pair["input"]) == []
        assert MODULE.analyze_scene(pair["input"])["facts"]["output"] == pair["output"]


def test_canonical_racket_parity_input_purity_and_a_b_a() -> None:
    source = _canonical_rule()
    pairs = _all_pairs()
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            actual = bridge.eval_text(rule_application(source, pair["input"]))
            assert actual == pair["output"]
            assert pair["input"] == before
        probe = bridge.eval_text(
            purity_body(source, pairs[0]["input"], pairs[1]["input"])
        )
        assert probe[0] == pairs[0]["output"]
        assert probe[1] == pairs[0]["output"]
        assert probe[2] == pairs[0]["input"]
    finally:
        bridge.shutdown()


def test_determinism_fresh_returns_and_global_rng_state() -> None:
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
def test_exact_override_boundary_matrix(difficulty: str) -> None:
    for index, overrides in enumerate(
        {
            "grid_h": h,
            "grid_w": w,
            "opening_relation": relation,
        }
        for h in (13, 19)
        for w in (13, 19)
        for relation in MODULE.RELATIONS
    ):
        grid = MODULE.generate(
            1_500 + index,
            7_000 + index,
            difficulty=difficulty,
            **overrides,
        )
        assert MODULE.self_check(grid, meta={"overrides": overrides}) == []
        assert MODULE.observe_overrides(grid) == overrides


def test_each_band_exercises_every_meaningful_branch() -> None:
    for band in ("easy", "medium", "hard"):
        facts = [
            MODULE.analyze_scene(
                MODULE.generate(20_000 + index, 30_000 + index, difficulty=band)
            )["facts"]
            for index in range(160)
        ]
        assert {item["opening_relation"] for item in facts} == set(MODULE.RELATIONS)
        assert {direction for item in facts for direction in item["directions"]} == set(MODULE.DIRECTIONS)
        assert all(item["changed_fraction"] >= 0.10 for item in facts)
        assert sum(item["grid_h"] == item["grid_w"] == 15 for item in facts) >= 45


def test_self_check_rejects_targeted_task_specific_impostors() -> None:
    fixtures = MODULE.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert MODULE.self_check(grid), name


def test_generated_python_mirror_matches_real_racket_oracle() -> None:
    source = _canonical_rule()
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for index in range(48):
            band = ("easy", "medium", "hard")[index % 3]
            grid = MODULE.generate(40_000 + index, 50_000 + index, difficulty=band)
            expected = MODULE.analyze_scene(grid)["facts"]["output"]
            actual = bridge.eval_text(rule_application(source, grid))
            assert actual == expected
    finally:
        bridge.shutdown()


def test_four_consecutive_examples_identify_the_relation_generalization() -> None:
    source = _canonical_rule()
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        pairs = []
        for index in range(4):
            grid = MODULE.generate(61_337, 9_000 + index, difficulty="medium")
            pairs.append({
                "input": grid,
                "output": bridge.eval_text(rule_application(source, grid)),
            })
    finally:
        bridge.shutdown()
    assert {
        MODULE.analyze_scene(pair["input"])["facts"]["opening_relation"]
        for pair in pairs
    } == set(MODULE.RELATIONS)
    assert MODULE.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_negative_recombination_is_rejected_but_racket_executes() -> None:
    source = _canonical_rule()
    grid = MODULE.generate(
        717,
        818,
        difficulty="hard",
        opening_relation="perpendicular",
    )
    analysis = MODULE.analyze_scene(grid)
    row, col = next(iter(analysis["facts"]["shapes"][0]["frame_cells"]))
    assert all(6 not in input_row for input_row in grid)
    foreign = copy.deepcopy(grid)
    foreign[row][col] = 6
    assert MODULE.self_check(foreign)
    assert sum(value == 6 for input_row in foreign for value in input_row) == 1

    bridge = RacketBridge()
    try:
        output = bridge.eval_text(rule_application(source, foreign))
    finally:
        bridge.shutdown()
    assert isinstance(output, list)
    assert len(output) == len(foreign)
    assert all(len(output_row) == len(foreign[0]) for output_row in output)
