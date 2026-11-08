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
TASK_ID = "496bcaf83a46"
GENERATOR_PATH = ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
BASE_PATH = ROOT / "data/base/solutions/banks/3c7b85b8eeb1/H40__496bcaf83a46.json"
MODULE = load_module_from_path(f"test_generator_{TASK_ID}_module", GENERATOR_PATH)


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _norm_grid(grid) -> list[list[int]]:
    return [[int(value) for value in row] if isinstance(row, str) else list(row) for row in grid]


def _all_pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"]
    pairs = list(row["train"]) + (list(test) if isinstance(test, list) else [test])
    return [{"input": _norm_grid(pair["input"]), "output": _norm_grid(pair["output"])} for pair in pairs]


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_metadata_rule_hash_and_task_local_sources_are_synchronized() -> None:
    row = _canonical_row()
    canonical = row["program_solution"]
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    assert MODULE.VERSION == "2.0.0"
    assert MODULE.RULE_HASH == "703485a20938"
    assert MODULE.RULE_HASH == _normalized_rule_hash(canonical)
    assert base["racket_target"]["raw_code"] == canonical
    assert base["racket_target"]["target_code"] == canonical


def test_all_canonical_inputs_pass_structural_checker() -> None:
    for pair in _all_pairs():
        assert MODULE.self_check(pair["input"]) == []


def test_canonical_racket_parity_input_purity_and_a_b_a() -> None:
    row = _canonical_row()
    source = row["program_solution"]
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


def test_determinism_fresh_returns_and_process_rng_state() -> None:
    state = random.getstate()
    first = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert MODULE.generate(901, 17, difficulty="hard") == second


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_override_boundary_matrix(difficulty: str) -> None:
    cases = [
        {"grid_h": h, "grid_w": w, "n_frames": n}
        for h in (11, 20)
        for w in (13, 24)
        for n in (2, 4)
    ]
    for index, overrides in enumerate(cases):
        grid = MODULE.generate(1500 + index, 7000 + index, difficulty=difficulty, **overrides)
        assert MODULE.self_check(grid, meta={"overrides": overrides}) == []
        assert MODULE.observe_overrides(grid) == overrides


def test_schedule_covers_unique_ties_and_seed_color_distractors() -> None:
    rows = []
    for band in ("easy", "medium", "hard"):
        for index in range(240):
            grid = MODULE.generate(20_000 + index, index, difficulty=band)
            analysis = MODULE._analyze(grid)
            assert not analysis["errors"]
            rows.append((band, analysis))
    assert any(a["winner_count"] == 1 for _, a in rows)
    assert any(a["winner_count"] == 2 for _, a in rows)
    assert any(a["distractors"] for band, a in rows if band == "hard")
    assert {len(a["frames"]) for _, a in rows} == {2, 3, 4}


def test_self_check_rejects_four_targeted_structural_impostors() -> None:
    base = MODULE.generate(312, 992, difficulty="medium", n_frames=3)
    analysis = MODULE._analyze(base)
    assert not analysis["errors"]

    broken_border = copy.deepcopy(base)
    r, c = next(iter(analysis["frames"][0]["border"]))
    broken_border[r][c] = 0
    assert any("complete rectangular border" in err for err in MODULE.self_check(broken_border))

    stray_seed = copy.deepcopy(base)
    occupied = set().union(*(f["border"] | f["inside"] for f in analysis["frames"]))
    spot = next((r, c) for r, row in enumerate(stray_seed) for c, v in enumerate(row) if v == 0 and (r, c) not in occupied)
    stray_seed[spot[0]][spot[1]] = 8
    assert any("outside eligible frames" in err for err in MODULE.self_check(stray_seed))

    empty_frame = copy.deepcopy(base)
    for r, c in analysis["frames"][0]["inside"]:
        if empty_frame[r][c] == 8:
            empty_frame[r][c] = 0
    assert any("at least one seed" in err for err in MODULE.self_check(empty_frame))

    all_tied = MODULE.generate(713, 814, difficulty="easy", n_frames=2)
    tie_analysis = MODULE._analyze(all_tied)
    counts = [f["seed_count"] for f in tie_analysis["frames"]]
    loser = counts.index(min(counts))
    target = max(counts)
    tied = copy.deepcopy(all_tied)
    available = [cell for cell in tie_analysis["frames"][loser]["inside"] if tied[cell[0]][cell[1]] == 0]
    for r, c in available[: target - counts[loser]]:
        tied[r][c] = 8
    assert any("all eligible frames tie" in err for err in MODULE.self_check(tied))


def test_negative_recombination_is_rejected_while_racket_still_executes() -> None:
    row = _canonical_row()
    grid = MODULE.generate(717, 818, difficulty="hard", n_frames=3)
    analysis = MODULE._analyze(grid)
    used = {v for line in grid for v in line}
    foreign = next(color for color in range(1, 10) if color not in used)
    victim = next(cell for frame in analysis["frames"] for cell in frame["inside"] if grid[cell[0]][cell[1]] == 8)
    recombined = copy.deepcopy(grid)
    recombined[victim[0]][victim[1]] = foreign
    errors = MODULE.self_check(recombined)
    assert errors
    assert any("complete rectangular border" in err or "belong to an eligible frame" in err for err in errors)

    bridge = RacketBridge()
    try:
        output = bridge.eval_text(rule_application(row["program_solution"], recombined))
    finally:
        bridge.shutdown()
    assert isinstance(output, list)
    assert len(output) == len(recombined)
    assert all(len(out_row) == len(recombined[0]) for out_row in output)


def test_default_three_demo_schedule_exposes_decisive_branches_before_query() -> None:
    for seed in range(30):
        analyses = [MODULE._analyze(MODULE.generate(seed, index)) for index in range(4)]
        assert all(not analysis["errors"] for analysis in analyses)
        demos, query = analyses[:3], analyses[3]
        assert any(analysis["winner_count"] == 2 for analysis in demos)
        assert any(analysis["distractors"] for analysis in demos)
        assert any(analysis["winner_count"] == 1 for analysis in demos)
        assert query["winner_count"] == 1
