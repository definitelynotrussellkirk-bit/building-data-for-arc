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
    spec = importlib.util.spec_from_file_location("generator_e7c4af96e258", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = load_generator()


def test_exact_axes_are_honored_and_observable_across_difficulty_bands():
    requested = {"grid_h": 20, "grid_w": 22, "marker_count": 3, "texture": "standard"}
    for difficulty in (None, "easy", "medium", "hard"):
        grid = gen.generate(101, 7, difficulty=difficulty, **requested)
        assert (len(grid), len(grid[0])) == (20, 22)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == requested


def test_request_validation_rejects_unknown_types_ranges_and_difficulty():
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, not_a_declared_axis=1)
    with pytest.raises(TypeError, match="grid_h"):
        gen.generate(0, 0, grid_h=True)
    with pytest.raises(ValueError, match="marker_count"):
        gen.generate(0, 0, marker_count=0)
    with pytest.raises(ValueError, match="texture"):
        gen.generate(0, 0, texture="bogus")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")


def test_structural_impostor_is_rejected():
    grid = [[0] * 15 for _ in range(13)]
    grid[3][3] = 2
    grid[4][4] = 4
    grid[10][10] = 4
    errors = gen.self_check(grid)
    assert errors
    assert any("red" in error or "marker" in error or "source" in error for error in errors)


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


def test_self_check_rejects_symmetric_marker_impostor():
    grid = [[0] * 15 for _ in range(13)]
    red = ((0, 0), (1, 0), (1, 1))
    symmetric_marker = ((0, 2), (0, 3), (1, 2), (1, 3))
    for r, c in red:
        grid[2 + r][2 + c] = 2
    for r, c in symmetric_marker:
        grid[2 + r][2 + c] = 4
        grid[8 + r][8 + c] = 4

    errors = gen.self_check(grid)

    assert errors
    assert any("marker" in error.lower() and "asymmetric" in error.lower() for error in errors)
