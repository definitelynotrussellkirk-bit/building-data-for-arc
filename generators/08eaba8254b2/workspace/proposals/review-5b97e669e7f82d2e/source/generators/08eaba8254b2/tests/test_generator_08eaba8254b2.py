from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]
REPO = TASK_HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load_generator():
    path = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_08eaba8254b2", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = load_generator()


def test_authority_pin_and_exact_axes_are_honored_across_difficulty_bands():
    assert gen.RULE_HASH == "5679cfe5ff27"
    requested = {
        "grid_w": 30,
        "xor_target": 8,
        "top_color": 1,
        "bot_color": 2,
        "sep_color": 4,
        "texture": "standard",
    }
    for difficulty in (None, "easy", "medium", "hard"):
        grid = gen.generate(101, 7, difficulty=difficulty, **requested)
        assert (len(grid), len(grid[0])) == (9, 30)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == requested


def test_request_validation_rejects_unknown_types_ranges_and_difficulty():
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, bogus_axis=1)
    with pytest.raises(TypeError, match="grid_w"):
        gen.generate(0, 0, grid_w=True)
    with pytest.raises(ValueError, match="grid_w"):
        gen.generate(0, 0, grid_w=2)
    with pytest.raises(ValueError, match="xor_target"):
        gen.generate(0, 0, xor_target=9)
    with pytest.raises(ValueError, match="top_color"):
        gen.generate(0, 0, top_color=0)
    with pytest.raises(ValueError, match="texture"):
        gen.generate(0, 0, texture="checker")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")


def test_exact_xor_target_is_realized_at_narrow_boundary():
    for seed in range(8):
        grid = gen.generate(seed, 0, grid_w=3, xor_target=8, texture="standard")
        actual = sum(
            (grid[r][c] == 0) != (grid[r + 5][c] == 0)
            for r in range(4)
            for c in range(3)
        )
        assert actual == 8
        assert gen.observe_overrides(grid)["xor_target"] == 8


def test_structural_impostor_is_rejected():
    grid = [[0] * 4 for _ in range(9)]
    grid[4] = [4] * 4
    grid[0][0] = 1
    errors = gen.self_check(grid)
    assert errors
    assert any("panel" in error or "occupancy" in error or "foreground" in error for error in errors)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261026)
    state = random.getstate()
    first = gen.generate(99, 3, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(99, 3, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert first != second
