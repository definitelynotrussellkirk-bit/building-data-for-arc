from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

TASK_ID = "07dbda8c31c9"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def _grid(value):
    return [[int(ch) for ch in row] for row in value]


def test_rule_hash_and_authorities_are_exactly_pinned():
    row = _canonical_row()
    source = row["program_solution"]
    expected = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    base = json.loads(
        (ROOT / "data/base/solutions/banks/f2c80d62966a/E32__07dbda8c31c9.json").read_text()
    )
    racket = base["racket_target"]
    assert expected == MODULE.RULE_HASH == "bd0e3c33843a"
    assert source == racket["raw_code"] == racket["target_code"]


def test_every_canonical_input_is_accepted():
    row = _canonical_row()
    pairs = list(row["train"]) + [row["test"]]
    assert len(pairs) == 5
    for pair in pairs:
        assert MODULE.self_check(_grid(pair["input"])) == []


def test_three_demo_schedule_is_contrastive_for_every_seed_and_band():
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            observed = [
                MODULE.observe_overrides(MODULE.generate(seed, index, difficulty=band))["texture"]
                for index in range(MODULE.EXAMPLES_NEEDED)
            ]
            assert observed == ["plain", "decoy_colors", "blob"]


def test_single_axis_boundaries_are_exact_and_observable():
    cases = [
        {"grid_h": 4}, {"grid_h": 12}, {"grid_w": 4}, {"grid_w": 30},
        {"n_red": 2}, {"n_red": 28},
        {"texture": "plain"}, {"texture": "decoy_colors"}, {"texture": "blob"},
    ]
    for band in ("easy", "medium", "hard"):
        for seed, case in enumerate(cases):
            grid = MODULE.generate(seed, seed * 17 + 3, difficulty=band, **case)
            observed = MODULE.observe_overrides(grid)
            for name, value in case.items():
                assert observed[name] == value
            assert MODULE.self_check(grid) == []


def test_incompatible_exact_axes_reject_loudly():
    with pytest.raises(ValueError, match="incompatible exact axes"):
        MODULE.generate(0, 0, difficulty="easy", grid_h=4, grid_w=4, n_red=28, texture="plain")
    with pytest.raises(ValueError, match="incompatible exact axes"):
        MODULE.generate(0, 0, difficulty="easy", n_red=2, texture="blob")


def test_self_check_rejects_targeted_impostors():
    impostors = {
        "short_line": [[0, 2, 0, 0]],
        "solid_2x2": [[2, 2], [2, 2]],
        "no_red": [[0] * 4 for _ in range(4)],
        "one_decoy": [[2, 0, 0, 0], [0, 3, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        "mixed_red_topology": [[2, 2, 0, 0], [0, 0, 0, 0], [0, 0, 2, 0], [0, 0, 0, 0]],
        "all_red": [[2] * 4 for _ in range(4)],
    }
    for name, grid in impostors.items():
        assert MODULE.self_check(grid), name


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(99173)
    before = random.getstate()
    first = MODULE.generate(123, 7, difficulty="hard")
    after = random.getstate()
    second = MODULE.generate(123, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    mutated = copy.deepcopy(first)
    mutated[0][0] = (mutated[0][0] + 1) % 10
    assert second != mutated or first != second


def test_linked_semantics_200_draws_per_band():
    for band in ("easy", "medium", "hard"):
        counts = {texture: 0 for texture in MODULE.TEXTURES}
        for index in range(200):
            grid = MODULE.generate(50_000 + index, index, difficulty=band)
            observed = MODULE.observe_overrides(grid)
            assert MODULE.self_check(grid) == []
            assert observed["n_red"] == sum(value == 2 for row in grid for value in row)
            counts[observed["texture"]] += 1
        assert all(counts[texture] >= 66 for texture in MODULE.TEXTURES)
