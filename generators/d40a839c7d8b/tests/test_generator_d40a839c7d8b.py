from __future__ import annotations

import json
import random
from pathlib import Path

from puzzle_generators.per_puzzle.d40a839c7d8b import generator as gen


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "d40a839c7d8b"
BASE_PATH = ROOT / "data/base/solutions/training/d406998b__d40a839c7d8b.json"


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _background_grid_like(grid: list[list[int]], bg: int = 0) -> list[list[int]]:
    return [[bg for _ in row] for row in grid]


def test_rule_hash_and_task_local_authorities_match_canonical() -> None:
    canonical = _canonical_row()
    base = json.loads(BASE_PATH.read_text())
    rule = canonical["program_solution"]
    assert gen.RULE_HASH == "c7049cdbce74"
    assert base["racket_target"]["target_code"] == rule
    assert base["racket_target"]["raw_code"] == rule


def test_self_check_accepts_every_canonical_input() -> None:
    canonical = _canonical_row()
    inputs = [pair["input"] for split in ("train", "test") for pair in canonical[split]]
    assert len(inputs) == 5
    assert [gen.self_check(grid) for grid in inputs] == [[] for _ in inputs]


def test_self_check_rejects_targeted_minimal_impostors() -> None:
    lawful = gen.generate(101, 3, difficulty="medium")
    h, w = len(lawful), len(lawful[0])
    bg = lawful[0][0]

    full_one_color = [[5] * w for _ in range(h)]
    short_line = _background_grid_like(lawful, bg)
    for c in range(min(4, w)):
        short_line[h // 2][c] = 5
    solid_2x2 = _background_grid_like(lawful, bg)
    for r in range(2):
        for c in range(2):
            solid_2x2[r][c] = 5
    no_trigger = [row[:] for row in lawful]
    trigger = (w + 1) % 2
    for r in range(h):
        for c in range(w):
            if c % 2 == trigger and no_trigger[r][c] == 5:
                no_trigger[r][c] = bg
    preexisting_green = [row[:] for row in lawful]
    preexisting_green[0][0] = 3

    impostors = {
        "full_one_color": full_one_color,
        "short_line": short_line,
        "solid_2x2": solid_2x2,
        "no_trigger_gray": no_trigger,
        "preexisting_green": preexisting_green,
    }
    for name, grid in impostors.items():
        assert gen.self_check(grid), name


def test_boundary_override_regression_and_exact_observation() -> None:
    # The pre-repair generator rejected grid_h=3 in the easy band and silently
    # failed exact-axis observation.  This single witness exercises every exact
    # observable axis at a lawful boundary combination.
    grid = gen.generate(
        0,
        3,
        difficulty="easy",
        grid_h=3,
        grid_w=18,
        gray_count=24,
        gray_layout="column",
        bg_color=9,
        decoy_palette_size=6,
    )
    assert gen.observe_overrides(grid) == {
        "grid_h": 3,
        "grid_w": 18,
        "gray_count": 24,
        "bg_color": 9,
        "decoy_palette_size": 6,
    }
    assert gen.self_check(grid) == []


def test_default_lesson_schedule_identifies_width_dependent_parity() -> None:
    pairs = []
    for sample_index in range(4):
        grid = gen.generate(987654321, sample_index, difficulty="medium")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    assert [len(pair["input"][0]) % 2 for pair in pairs] == [0, 1, 0, 1]
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_deterministic_replay_fresh_returns_and_global_rng_purity() -> None:
    random.seed(424242)
    before = random.getstate()
    first = gen.generate(17, 11, difficulty="hard")
    after = random.getstate()
    second = gen.generate(17, 11, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
