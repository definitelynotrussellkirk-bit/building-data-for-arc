from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.generator_module_loader import load_module_from_path
from scripts.rule_smoke import purity_body, rule_application

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "50385c1a773f"
GENERATOR_PATH = ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/f4facb1306bd/H113__50385c1a773f.json"
)
MODULE = load_module_from_path(f"test_generator_{TASK_ID}_module", GENERATOR_PATH)


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _all_pairs() -> list[dict]:
    row = _canonical_row()
    return list(row["train"]) + list(row["test"])


def test_metadata_rule_hash_and_task_local_sources_are_synchronized() -> None:
    row = _canonical_row()
    canonical = row["program_solution"]
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    assert MODULE.VERSION == "4.0.0"
    assert MODULE.RULE_HASH == "326ba9cc3a3b"
    assert MODULE.RULE_HASH == _normalized_rule_hash(canonical)
    assert base["racket_target"]["raw_code"] == canonical
    assert base["racket_target"]["target_code"] == canonical


def test_all_canonical_inputs_pass_structural_checker() -> None:
    for pair in _all_pairs():
        assert MODULE.self_check(pair["input"]) == []


def test_canonical_racket_parity_input_purity_and_a_b_a() -> None:
    row = _canonical_row()
    source = row["program_solution"]
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for pair in _all_pairs():
            before = copy.deepcopy(pair["input"])
            actual = bridge.eval_text(rule_application(source, pair["input"]))
            assert actual == pair["output"]
            assert pair["input"] == before
        probe = bridge.eval_text(
            purity_body(source, row["train"][0]["input"], row["train"][1]["input"])
        )
        assert probe[0] == row["train"][0]["output"]
        assert probe[1] == row["train"][0]["output"]
        assert probe[2] == row["train"][0]["input"]
    finally:
        bridge.shutdown()


def test_determinism_fresh_returns_and_process_rng_state() -> None:
    global_state = random.getstate()
    first = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == global_state
    second = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == global_state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    replay = MODULE.generate(901, 17, difficulty="hard")
    assert replay == second


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_override_boundary_matrix(difficulty: str) -> None:
    cases = [
        {
            "grid_h": h,
            "grid_w": w,
            "n_deflectors": n_deflectors,
            "termination": termination,
            "n_wall_components": n_walls,
        }
        for h in (8, 16)
        for w in (9, 16)
        for n_deflectors in (1, 3)
        for termination in ("wall", "boundary")
        for n_walls in (1, 2)
    ]
    for index, overrides in enumerate(cases):
        grid = MODULE.generate(
            1500 + index,
            7000 + index,
            difficulty=difficulty,
            **overrides,
        )
        assert MODULE.self_check(grid) == []
        assert MODULE.observe_overrides(grid) == overrides


def test_each_band_exercises_every_meaningful_branch() -> None:
    for band in ("easy", "medium", "hard"):
        analyses = [
            MODULE._analysis(MODULE.generate(20_000 + i, 30_000 + i, difficulty=band))
            for i in range(120)
        ]
        assert {item["termination"] for item in analyses} == {"wall", "boundary"}
        assert {item["n_wall_components"] for item in analyses} == {1, 2}
        assert {kind for item in analyses for kind in item["mirror_kinds"]} == {3, 4}
        assert all(not item["errors"] for item in analyses)
        assert len({json.dumps(MODULE.generate(20_000 + i, 30_000 + i, difficulty=band)) for i in range(120)}) >= 110


def test_self_check_rejects_four_targeted_structural_impostors() -> None:
    base = MODULE.generate(
        312,
        991,
        difficulty="medium",
        n_deflectors=1,
        termination="wall",
        n_wall_components=1,
    )
    analysis = MODULE._analysis(base)

    duplicate_source = copy.deepcopy(base)
    added = False
    for r, row in enumerate(duplicate_source):
        for c, value in enumerate(row):
            if value == 0 and (r, c) not in analysis["path"]:
                duplicate_source[r][c] = 2
                added = True
                break
        if added:
            break
    assert any("exactly one source" in err for err in MODULE.self_check(duplicate_source))

    unreachable_mirror = copy.deepcopy(base)
    added = False
    for r, row in enumerate(unreachable_mirror):
        for c, value in enumerate(row):
            if value == 0 and (r, c) not in analysis["path"]:
                unreachable_mirror[r][c] = 3
                added = True
                break
        if added:
            break
    assert any("not on the traced beam" in err for err in MODULE.self_check(unreachable_mirror))

    canonical_bent_wall = copy.deepcopy(_canonical_row()["train"][1]["input"])
    canonical_bent_wall[5][0] = 5
    assert any("not a straight" in err for err in MODULE.self_check(canonical_bent_wall))

    short_segment = [[0 for _ in range(9)] for _ in range(8)]
    short_segment[5][1] = 2
    short_segment[5][2] = 3
    short_segment[1][2] = 5
    assert any("at least two black cells" in err for err in MODULE.self_check(short_segment))


def test_negative_recombination_is_rejected_while_racket_still_executes() -> None:
    row = _canonical_row()
    grid = MODULE.generate(
        717,
        818,
        difficulty="hard",
        n_deflectors=2,
        termination="boundary",
        n_wall_components=1,
    )
    analysis = MODULE._analysis(grid)
    mirror_r, mirror_c, _ = analysis["hit_mirrors"][0]
    assert all(6 not in input_row for input_row in grid)
    foreign_feature = copy.deepcopy(grid)
    foreign_feature[mirror_r][mirror_c] = 6
    errors = MODULE.self_check(foreign_feature)
    assert errors
    assert any("colors outside" in err for err in errors)

    bridge = RacketBridge()
    try:
        output = bridge.eval_text(rule_application(row["program_solution"], foreign_feature))
    finally:
        bridge.shutdown()
    assert isinstance(output, list)
    assert len(output) == len(foreign_feature)
    assert all(len(out_row) == len(foreign_feature[0]) for out_row in output)
