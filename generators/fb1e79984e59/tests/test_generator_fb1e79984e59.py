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
TASK_ID = "fb1e79984e59"
GENERATOR_PATH = ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
BASE_PATHS = (
    ROOT / "data/base/solutions/training/bda2d7a6__fb1e79984e59.json",
    ROOT / "data/base/solutions/augmented/bda2d7a6__e895f9ea39a5.json",
)
MODULE = load_module_from_path(f"test_generator_{TASK_ID}_module", GENERATOR_PATH)


def _canonical_rows() -> list[dict]:
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    assert len(rows) == 2
    return rows


def _all_pairs() -> list[dict]:
    pairs = []
    for row in _canonical_rows():
        for split in ("train", "test"):
            pairs.extend(row.get(split, []))
    return pairs


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _grid_from_ring_colors(h: int, w: int, colors: list[int]) -> list[list[int]]:
    return [
        [colors[min(r, c, h - 1 - r, w - 1 - c)] for c in range(w)]
        for r in range(h)
    ]


def test_metadata_hash_and_selected_task_rules_match_canonical() -> None:
    rows = _canonical_rows()
    canonical = rows[0]["program_solution"]
    assert all(row["program_solution"] == canonical for row in rows)
    assert MODULE.VERSION == "4.0.0"
    assert MODULE.RULE_HASH == "392773ffe271"
    assert MODULE.RULE_HASH == _normalized_rule_hash(canonical)
    for path in BASE_PATHS:
        base = json.loads(path.read_text(encoding="utf-8"))
        target = base["racket_target"]
        assert target["target_code"] == canonical
        assert target["raw_code"] != canonical
        assert _normalized_rule_hash(target["raw_code"]) == "f8b35efa27dc"


def test_all_canonical_inputs_pass_structural_checker() -> None:
    for pair in _all_pairs():
        assert MODULE.self_check(pair["input"]) == []


def test_canonical_and_archival_rules_have_pair_parity_purity_and_a_b_a() -> None:
    rows = _canonical_rows()
    canonical = rows[0]["program_solution"]
    archival = json.loads(BASE_PATHS[0].read_text(encoding="utf-8"))["racket_target"]["raw_code"]
    pairs = _all_pairs()
    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            canonical_out = bridge.eval_text(rule_application(canonical, pair["input"]))
            archival_out = bridge.eval_text(rule_application(archival, pair["input"]))
            assert canonical_out == pair["output"]
            assert archival_out == canonical_out
            assert pair["input"] == before
        probe = bridge.eval_text(purity_body(canonical, pairs[0]["input"], pairs[1]["input"]))
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
    first[0][0] = (first[0][0] + 1) % 10
    assert MODULE.generate(901, 17, difficulty="hard") == second


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_override_boundary_matrix(difficulty: str) -> None:
    cases = [
        {"grid_h": 5, "grid_w": 18, "ring_pattern": "all_distinct", "include_zero": False},
        {"grid_h": 18, "grid_w": 5, "ring_pattern": "outer_repeat", "include_zero": True},
        {"grid_h": 5, "grid_w": 5, "ring_pattern": "inner_repeat", "include_zero": False},
        {"grid_h": 7, "grid_w": 18, "ring_pattern": "alternating", "include_zero": True},
        {"grid_h": 18, "grid_w": 7, "ring_pattern": "alternating", "include_zero": False},
    ]
    for index, overrides in enumerate(cases):
        grid = MODULE.generate(1500 + index, 7000 + index, difficulty=difficulty, **overrides)
        assert MODULE.self_check(grid, difficulty=difficulty) == []
        assert MODULE.observe_overrides(grid) == overrides
    with pytest.raises(ValueError, match="requires grid_h and grid_w >= 7"):
        MODULE.generate(
            88,
            99,
            difficulty=difficulty,
            grid_h=5,
            grid_w=5,
            ring_pattern="alternating",
        )
    with pytest.raises(ValueError, match="unsupported override"):
        MODULE.generate(88, 99, difficulty=difficulty, palette_seed=3)


def test_six_pair_schedule_covers_all_grammars_and_three_demos_identify_rule() -> None:
    for seed in range(40):
        observations = [
            MODULE.observe_overrides(MODULE.generate(seed, index, difficulty="medium"))
            for index in range(6)
        ]
        assert {item["ring_pattern"] for item in observations} == set(MODULE.RING_PATTERNS)
        assert {item["include_zero"] for item in observations} == {False, True}
        for start in range(6):
            window = [observations[(start + offset) % 6]["ring_pattern"] for offset in range(3)]
            assert "all_distinct" in window
            assert any(pattern in {"outer_repeat", "inner_repeat"} for pattern in window)


def test_repeated_ring_witnesses_rebut_positional_rotation() -> None:
    for pattern in ("outer_repeat", "inner_repeat"):
        grid = MODULE.generate(
            321,
            654,
            difficulty="medium",
            grid_h=7,
            grid_w=9,
            ring_pattern=pattern,
            include_zero=True,
        )
        ring_colors, problems = MODULE._extract_ring_colors(grid)
        assert not problems
        unique = list(dict.fromkeys(ring_colors))
        semantic = [unique[(unique.index(color) - 1) % len(unique)] for color in ring_colors]
        positional = [ring_colors[(index - 1) % len(ring_colors)] for index in range(len(ring_colors))]
        assert semantic != positional


def test_self_check_rejects_four_targeted_structural_impostors() -> None:
    lawful = MODULE.generate(
        312,
        992,
        difficulty="medium",
        grid_h=7,
        grid_w=9,
        ring_pattern="outer_repeat",
        include_zero=True,
    )

    split_ring = copy.deepcopy(lawful)
    split_ring[0][0] = next(color for color in range(10) if color not in {value for row in lawful for value in row})
    assert any("ring depth 0" in err for err in MODULE.self_check(split_ring))

    monochrome = [[4 for _ in row] for row in lawful]
    assert any("fewer than two" in err for err in MODULE.self_check(monochrome))

    unsupported_sequence = _grid_from_ring_colors(7, 9, [2, 2, 5, 7])
    assert any("outside the declared teaching grammar" in err for err in MODULE.self_check(unsupported_sequence))

    invalid_color = copy.deepcopy(lawful)
    invalid_color[1][1] = 10
    assert any("not an ARC color" in err for err in MODULE.self_check(invalid_color))

    ragged = copy.deepcopy(lawful)
    ragged[-1].pop()
    assert "ragged grid" in MODULE.self_check(ragged)


def test_negative_recombination_is_rejected_while_racket_still_executes() -> None:
    canonical = _canonical_rows()[0]["program_solution"]
    grid = MODULE.generate(
        717,
        818,
        difficulty="hard",
        grid_h=11,
        grid_w=13,
        ring_pattern="inner_repeat",
        include_zero=True,
    )
    used = {value for row in grid for value in row}
    foreign = next(color for color in range(10) if color not in used)
    recombined = copy.deepcopy(grid)
    recombined[0][0] = foreign
    assert any("ring depth 0" in err for err in MODULE.self_check(recombined))

    bridge = RacketBridge()
    try:
        output = bridge.eval_text(rule_application(canonical, recombined))
    finally:
        bridge.shutdown()
    assert isinstance(output, list)
    assert len(output) == len(recombined)
    assert all(len(row) == len(recombined[0]) for row in output)
