"""Focused regression tests for the row-header shift generator repair."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.d4d38f319c8f.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _grid(value):
    return [
        [int(char) for char in row] if isinstance(row, str) else list(row)
        for row in value
    ]


def _canonical_pairs():
    pairs = []
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != gen.TASK_ID:
            continue
        train = row.get("train") or []
        test = row.get("test") or []
        if isinstance(train, dict):
            train = [train]
        if isinstance(test, dict):
            test = [test]
        pairs.extend(train)
        pairs.extend(test)
    return pairs


def _python_rule(grid):
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, row in enumerate(grid):
        shift = row[0]
        out[r][0] = shift
        for c in range(1, w):
            src = c - shift
            if 1 <= src < w and row[src] != 0:
                out[r][c] = row[src]
    return out


def test_all_five_canonical_pairs_and_outputs_pass():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        grid = _grid(pair["input"])
        assert gen.self_check(grid) == []
        assert gen.is_canonical_like(grid)
        assert _python_rule(grid) == _grid(pair["output"])


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_distribution_covers_canonical_prior_and_all_clip_modes(difficulty):
    canonical = 0
    modes = set()
    distinct = set()
    for seed in range(300):
        grid = gen.generate(seed, seed * 11 + 3, difficulty=difficulty)
        assert gen.self_check(grid) == []
        feature = gen.profile_signature(grid)
        modes.add(feature["clip_mode"])
        canonical += gen.is_canonical_like(grid)
        distinct.add(json.dumps(grid, separators=(",", ":")))
    assert canonical >= 80
    assert len(distinct) >= 285
    assert "some" in modes
    if difficulty == "easy":
        assert "none" in modes
    elif difficulty == "hard":
        assert "all_rows" in modes
    else:
        assert modes == {"none", "some", "all_rows"}


@pytest.mark.parametrize(
    "case",
    [
        {
            "grid_h": 4,
            "grid_w": 7,
            "n_cells": 1,
            "max_shift": 1,
            "palette_size": 1,
            "clip_mode": "none",
        },
        {
            "grid_h": 14,
            "grid_w": 20,
            "n_cells": 5,
            "max_shift": 8,
            "palette_size": 9,
            "clip_mode": "all_rows",
        },
        {
            "grid_h": 9,
            "grid_w": 13,
            "n_cells": 3,
            "max_shift": 5,
            "palette_size": 7,
            "clip_mode": "some",
        },
    ],
)
def test_exact_override_axes(case):
    grid = gen.generate(901, 17, difficulty="hard", **case)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == case


@pytest.mark.parametrize(
    "case",
    [
        {"n_cells": 1, "clip_mode": "some"},
        {
            "grid_w": 7,
            "n_cells": 5,
            "max_shift": 3,
            "clip_mode": "none",
        },
        {"grid_h": 4, "n_cells": 1, "palette_size": 9},
    ],
)
def test_incompatible_override_combinations_fail_loudly(case):
    with pytest.raises(ValueError):
        gen.generate(7, 7, difficulty="easy", **case)


def test_self_check_rejects_minimal_and_task_specific_impostors():
    valid = gen.generate(
        88,
        5,
        grid_h=5,
        grid_w=9,
        n_cells=2,
        max_shift=3,
        palette_size=4,
        clip_mode="some",
    )
    assert gen.self_check(valid) == []
    h, w = len(valid), len(valid[0])

    all_background = [[0] * w for _ in range(h)]
    full_one_color = [[4] * w for _ in range(h)]
    singleton = [[0] * w for _ in range(h)]
    singleton[0][0] = 1
    solid_2x2 = [[0] * w for _ in range(h)]
    for r in range(2):
        for c in range(2):
            solid_2x2[r][c] = 2
    short_line = [[0] * w for _ in range(h)]
    short_line[0][:3] = [2, 4, 4]

    zero_header = copy.deepcopy(valid)
    zero_header[0][0] = 0

    uniform_header = copy.deepcopy(valid)
    for row in uniform_header:
        row[0] = 3

    unequal_row_counts = copy.deepcopy(valid)
    cell = next(c for c, value in enumerate(unequal_row_counts[0][1:], 1) if value)
    unequal_row_counts[0][cell] = 0

    no_survivors = [[0] * 7 for _ in range(4)]
    for r in range(4):
        no_survivors[r][0] = 3
        no_survivors[r][6] = r + 1

    for mutation in (
        all_background,
        full_one_color,
        singleton,
        solid_2x2,
        short_line,
        zero_header,
        uniform_header,
        unequal_row_counts,
        no_survivors,
    ):
        assert gen.self_check(mutation)


def test_negative_recombination_is_rejected_but_oracle_remains_total():
    grid = _grid(_canonical_pairs()[0]["input"])
    recombined = copy.deepcopy(grid)
    # Add a third content cell to one row while leaving every other canonical
    # feature intact.  The Racket rule can execute it, but it is outside the
    # generator's equal-row-count teaching grammar.
    recombined[0][2] = 9
    assert gen.self_check(recombined)
    output = _python_rule(recombined)
    assert len(output) == len(recombined)
    assert all(len(row) == len(recombined[0]) for row in output)


def test_determinism_fresh_returns_rng_purity_and_observational_self_check():
    random.seed(20260724)
    state = random.getstate()
    first = gen.generate(77, 9, difficulty="hard")
    after = random.getstate()
    replay = gen.generate(77, 9, difficulty="hard")
    assert state == after
    assert first == replay
    assert first is not replay
    assert all(a is not b for a, b in zip(first, replay))

    snapshot = copy.deepcopy(replay)
    assert gen.self_check(replay) == []
    assert replay == snapshot
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != replay
