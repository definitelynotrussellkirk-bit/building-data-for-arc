"""Focused regression tests for the repaired canonical generator contract."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root


TASK_ID = "346480121fcb"


def _load_generator():
    path = find_root(__file__) / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"_test_{TASK_ID}_generator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_unknown_and_malformed_overrides_are_rejected():
    generator = _load_generator()
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, misspelled_axis=3)
    with pytest.raises((TypeError, ValueError), match="integer"):
        generator.generate(0, 0, grid_h=True)
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, texture="warm")
    with pytest.raises(ValueError, match="unknown override"):
        generator.generate(0, 0, texture="no_sel")


def test_full_declared_size_and_key_domains_are_honored_at_every_difficulty():
    generator = _load_generator()
    for difficulty in (None, "easy", "medium", "hard"):
        grid = generator.generate(
            11,
            19,
            difficulty=difficulty,
            grid_h=14,
            grid_w=16,
            key=5,
            blob_count=4,
        )
        assert (len(grid), len(grid[0])) == (14, 16)
        assert grid[0][-1] == 5
        assert generator.self_check(grid, difficulty=difficulty, meta={"texture": "default", "blob_count": 4}) == []


def test_easy_generation_no_longer_collapses_to_identity_and_is_deterministic():
    generator = _load_generator()
    keys = set()
    for seed in range(24):
        first = generator.generate(seed, seed % 5, difficulty="easy")
        second = generator.generate(seed, seed % 5, difficulty="easy")
        assert first == second
        keys.add(first[0][-1])
    assert keys - {1}
    assert len(keys) >= 3


def test_generated_samples_satisfy_exact_selector_and_component_contract():
    generator = _load_generator()
    for seed in range(20):
        grid = generator.generate(seed, seed, difficulty=("easy", "medium", "hard")[seed % 3])
        assert generator.self_check(grid, meta={"texture": "default"}) == []


def test_self_check_rejects_two_selector_colored_components():
    generator = _load_generator()
    grid = [[0] * 10 for _ in range(7)]
    grid[0][0] = 4
    grid[0][-1] = 2
    grid[2][1] = 4
    grid[4][7] = 4
    grid[3][4] = 6
    errors = generator.self_check(grid, meta={"texture": "default"})
    assert any("exactly one" in error for error in errors)


def test_every_declared_axis_is_observable_from_the_returned_grid():
    generator = _load_generator()
    assert "texture" not in generator.AXES
    requested = {"grid_h": 11, "grid_w": 15, "key": 4, "blob_count": 3}
    grid = generator.generate(3, 4, **requested)
    assert generator.observe_overrides(grid) == requested
