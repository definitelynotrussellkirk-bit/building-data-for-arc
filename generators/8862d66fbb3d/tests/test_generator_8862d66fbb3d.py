from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.8862d66fbb3d.generator"
)


def _canonical_inputs():
    path = Path("data/canonical/puzzles.jsonl")
    row = next(
        json.loads(line)
        for line in path.open(encoding="utf-8")
        if json.loads(line).get("task_id") == MODULE.TASK_ID
    )
    pairs = list(row["train"])
    test = row["test"]
    pairs.extend(test if isinstance(test, list) else [test])
    return [
        [[int(value) for value in raw_row] for raw_row in pair["input"]]
        for pair in pairs
    ]


def _blank_grid(cmd=1):
    grid = [[0 for _ in range(7)] for _ in range(4)]
    grid[0][0] = cmd
    return grid


def test_rule_hash_and_all_canonical_inputs_are_accepted():
    assert MODULE.RULE_HASH == "6f140febdf35"
    inputs = _canonical_inputs()
    assert len(inputs) == 5
    assert all(MODULE.self_check(grid) == [] for grid in inputs)


def test_declared_axes_are_observable_and_exact():
    cases = [
        {"cmd": 1},
        {"cmd": 8},
        {"left_count": 3},
        {"left_count": 6},
        {"right_count": 3},
        {"right_count": 6},
        {"overlap_count": 1},
        {"overlap_count": 4},
        {"palette_kind": "solid"},
        {"palette_kind": "left_multicolor"},
        {"palette_kind": "right_multicolor"},
        {"palette_kind": "both_multicolor"},
        {
            "cmd": 8,
            "left_count": 6,
            "right_count": 6,
            "overlap_count": 4,
            "palette_kind": "both_multicolor",
        },
    ]
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = MODULE.generate(101 + index, 503 + index, difficulty=band, **overrides)
            observed = MODULE.observe_overrides(grid)
            assert MODULE.self_check(grid, difficulty=band) == []
            assert all(observed[key] == value for key, value in overrides.items())


def test_generated_masks_make_the_command_answer_discriminating():
    for cmd in range(1, 9):
        equivalent = {4, 7} if cmd in (4, 7) else {cmd}
        for seed in range(30):
            grid = MODULE.generate(seed, seed * 19 + cmd, cmd=cmd)
            observed = MODULE.observe_overrides(grid)
            _, left, right, _, _ = MODULE._panel_state(grid)
            target = left & MODULE._transform_mask(right, cmd)
            assert len(target) == observed["overlap_count"]
            assert len(target) < min(len(left), len(right))
            for other in range(1, 9):
                if other not in equivalent:
                    assert left & MODULE._transform_mask(right, other) != target


def test_self_check_rejects_structural_impostors():
    base = MODULE.generate(11, 17, cmd=2)

    no_command = copy.deepcopy(base)
    no_command[0][0] = 0
    assert MODULE.self_check(no_command)

    top_row_noise = copy.deepcopy(base)
    top_row_noise[0][1] = 1
    assert MODULE.self_check(top_row_noise)

    separator_noise = copy.deepcopy(base)
    separator_noise[2][3] = 1
    assert MODULE.self_check(separator_noise)

    shared_palette = copy.deepcopy(base)
    left_color = next(
        shared_palette[1 + r][c]
        for r in range(3)
        for c in range(3)
        if shared_palette[1 + r][c]
    )
    for r in range(3):
        for c in range(3):
            if shared_palette[1 + r][4 + c]:
                shared_palette[1 + r][4 + c] = left_color
    assert MODULE.self_check(shared_palette)

    no_overlap = _blank_grid(cmd=1)
    for c in range(3):
        no_overlap[1][c] = 1
        no_overlap[3][4 + c] = 2
    assert MODULE.self_check(no_overlap)

    hidden_transform = _blank_grid(cmd=3)
    for c in range(3):
        hidden_transform[2][c] = 1
        hidden_transform[2][4 + c] = 2
    assert MODULE.self_check(hidden_transform)


def test_incompatible_exact_counts_reject_loudly():
    with pytest.raises(ValueError, match="incompatible counts"):
        MODULE.generate(0, 0, left_count=3, overlap_count=4)
    with pytest.raises(ValueError, match="incompatible counts"):
        MODULE.generate(0, 0, left_count=6, right_count=6, overlap_count=1)


def test_replay_returns_fresh_objects_without_touching_global_rng():
    random.seed(987654321)
    expected_state = random.getstate()
    first = MODULE.generate(23, 29, difficulty="hard")
    assert random.getstate() == expected_state
    second = MODULE.generate(23, 29, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 0
    assert second[0][0] != 0


def test_sequential_episode_schedule_covers_distinct_transforms():
    witnessed_commands = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(80):
            commands = [
                MODULE.generate(seed, sample_index, difficulty=band)[0][0]
                for sample_index in range(5)
            ]
            witnessed_commands.update(commands)
            assert commands[3] == commands[0]
            assert commands[4] == commands[1]
            transform_classes = {4 if cmd in (4, 7) else cmd for cmd in commands[:3]}
            assert len(transform_classes) == 3
    assert witnessed_commands == set(range(1, 9))
