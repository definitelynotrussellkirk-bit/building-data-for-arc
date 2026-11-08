from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import importlib
gen = importlib.import_module("puzzle_generators.per_puzzle.204c79678d9d.generator")

ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task missing")


def _lesson(seed: int, start_index: int):
    pairs = []
    for offset in range(gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, start_index + offset, difficulty="medium")
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    return pairs[:-1], pairs[-1]


def test_canonical_inputs_and_outputs_are_accepted():
    row = _canonical_row()
    for split in ("train", "test"):
        for pair in row[split]:
            grid = copy.deepcopy(pair["input"])
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.rule_mirror(grid) == pair["output"]
            assert grid == pair["input"]


def test_declared_override_matrix_is_exact_and_valid():
    for h in (7, 12):
        for w in (8, 14):
            for orientation in gen.ORIENTATIONS:
                for role in gen.DOOR_ROLES:
                    grid = gen.generate(
                        91,
                        17,
                        difficulty="hard",
                        grid_h=h,
                        grid_w=w,
                        orientation=orientation,
                        door_role=role,
                    )
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == {
                        "grid_h": h,
                        "grid_w": w,
                        "orientation": orientation,
                        "door_role": role,
                    }


def test_both_door_semantics_are_real_not_metadata():
    traversed = gen.generate(
        3, 0, grid_h=7, grid_w=9,
        orientation="horizontal", door_role="traversed"
    )
    blocked = gen.generate(
        3, 0, grid_h=7, grid_w=9,
        orientation="horizontal", door_role="blocking_shortcut"
    )
    assert gen._door_traversed(traversed)
    assert gen._door_blocks_shortcut(blocked)
    assert gen.rule_mirror(blocked) != gen._rival_visit_key_door_open(blocked)
    assert gen.rule_mirror(traversed) != gen._rival_door_wall(traversed)


def test_consecutive_lessons_refute_named_rivals():
    for start_index in range(8):
        demos, query = _lesson(400 + start_index, start_index)
        assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(
        10, 2, grid_h=7, grid_w=9,
        orientation="horizontal", door_role="traversed"
    )
    mutations = []

    missing_key = copy.deepcopy(base)
    kr, kc = gen._positions(missing_key, 5)[0]
    missing_key[kr][kc] = 0
    mutations.append(missing_key)

    duplicate_start = copy.deepcopy(base)
    zr, zc = gen._positions(duplicate_start, 0)[0]
    duplicate_start[zr][zc] = 2
    mutations.append(duplicate_start)

    broken_border = copy.deepcopy(base)
    broken_border[0][1] = 0
    mutations.append(broken_border)

    disconnected = copy.deepcopy(base)
    sr, sc = gen._positions(disconnected, 2)[0]
    for dr, dc in gen._DIR4:
        rr, cc = sr + dr, sc + dc
        if 0 <= rr < len(disconnected) and 0 <= cc < len(disconnected[0]):
            if disconnected[rr][cc] == 0:
                disconnected[rr][cc] = 8
    mutations.append(disconnected)

    open_field = [[8] * 9 for _ in range(7)]
    for r in range(1, 6):
        for c in range(1, 8):
            open_field[r][c] = 0
    open_field[1][1], open_field[1][7] = 2, 3
    open_field[5][1], open_field[1][4] = 5, 6
    mutations.append(open_field)

    for mutation in mutations:
        assert gen.self_check(mutation), mutation


def test_replay_freshness_and_global_rng_purity():
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(44, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(44, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after
    first[1][1] = 9
    assert gen.generate(44, 9, difficulty="hard") == second
