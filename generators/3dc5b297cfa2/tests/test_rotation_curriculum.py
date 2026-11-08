"""Regression tests for the retained rotating-query teaching counterexample."""
from __future__ import annotations

import importlib.util
from pathlib import Path

TASK_ID = "3dc5b297cfa2"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("rotation_review_generator", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_retained_three_pair_window_is_identifiable_under_every_query_rotation():
    """The exact audited start must not hide the sole black-branch witness."""
    seed = 2_133_068_724
    pairs = [_pair(seed, sample_index, "easy") for sample_index in (1, 2, 3)]

    for query_index in range(3):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_every_schedule_period_window_keeps_a_black_witness_after_one_holdout():
    period = len(gen.SCHEDULE_PROFILES)
    for start in range(period):
        black_flags = [
            bool(gen.observe_overrides(gen.generate(71, start + offset))["black_shape"])
            for offset in range(3)
        ]
        for query_index in range(3):
            remaining = [flag for index, flag in enumerate(black_flags) if index != query_index]
            assert any(remaining), (start, black_flags, query_index)
