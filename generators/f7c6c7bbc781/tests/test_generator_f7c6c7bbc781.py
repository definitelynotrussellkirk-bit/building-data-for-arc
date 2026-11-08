from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.f7c6c7bbc781 import generator as gen


def _canonical_row() -> dict:
    path = Path(__file__).resolve().parents[1] / "data/canonical/puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("content_hash") == gen.TASK_ID:
            return row
    raise AssertionError(f"missing canonical row for {gen.TASK_ID}")


def test_exact_even_dimension_overrides_are_honored() -> None:
    grid = gen.generate(7, 3, difficulty="hard", grid_h=4, grid_w=18)
    assert (len(grid), len(grid[0])) == (4, 18)
    assert gen.observe_overrides(grid) == {"grid_h": 4, "grid_w": 18}


def test_odd_or_unknown_overrides_reject_loudly() -> None:
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="easy", grid_h=5)
    with pytest.raises(TypeError):
        gen.generate(0, 0, difficulty="easy", nonexistent_axis=1)


def test_self_check_rejects_off_diagonal_ring_corruption() -> None:
    grid = gen.generate(11, 2, difficulty="medium", grid_h=10, grid_w=12)
    assert gen.self_check(grid) == []
    impostor = copy.deepcopy(grid)
    impostor[0][1] = impostor[1][1]
    errors = gen.self_check(impostor)
    assert errors
    assert any("ring" in error or "onion" in error for error in errors)


def test_canonical_pairs_are_valid_and_python_mirror_matches() -> None:
    row = _canonical_row()
    for split in ("train", "test"):
        for pair in row[split]:
            original = copy.deepcopy(pair["input"])
            assert gen.self_check(pair["input"]) == []
            assert gen.rule_mirror(pair["input"]) == pair["output"]
            assert pair["input"] == original


def test_replay_fresh_returns_and_global_rng_purity() -> None:
    state_before = random.getstate()
    first = gen.generate(123, 9, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(123, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert state_after == state_before
    first[0][0] = 0
    assert second[0][0] != 0


def test_default_lessons_are_nonidentity_clean_onions() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(20):
            grid = gen.generate(seed, seed % 7, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.rule_mirror(grid) != grid
