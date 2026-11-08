"""Reviewer-authored regressions for the 3.0.1 request/lesson repair."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))
_SPEC = importlib.util.spec_from_file_location(
    "review_repairs_generator_603bd7fff5df", SOURCE
)
assert _SPEC is not None and _SPEC.loader is not None
GEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GEN)


def test_generate_rejects_invalid_request_scalars_before_drawing():
    for seed in (True, False, 1.0, 1.75, "1"):
        with pytest.raises((TypeError, ValueError), match="seed"):
            GEN.generate(seed, 0, difficulty="easy")

    for sample_index in (True, False, 1.0, 1.75, "1", -1):
        with pytest.raises((TypeError, ValueError), match="sample_index"):
            GEN.generate(991, sample_index, difficulty="easy")

    for difficulty in (True, False, 0, 1.0, "__invalid_difficulty__"):
        with pytest.raises((TypeError, ValueError), match="difficulty"):
            GEN.generate(991, 0, difficulty=difficulty)


def test_every_cyclic_four_pair_rotation_is_identifiable():
    """Regression for review-ae7bce401b5111fe's rotation counterexample."""
    for band in ("easy", "medium", "hard"):
        for start in range(len(GEN.SCHEDULE_PROFILES)):
            rows = []
            for offset in range(4):
                grid = GEN.generate(1234, start + offset, difficulty=band)
                rows.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for query_index in range(4):
                demos = [row for index, row in enumerate(rows) if index != query_index]
                assert GEN.lesson_identifiable(demos, rows[query_index]) == [], (
                    band,
                    start,
                    query_index,
                    [GEN.observe_overrides(row["input"]) for row in rows],
                    GEN.lesson_identifiable(demos, rows[query_index]),
                )


def test_declares_machine_readable_twelve_slot_lesson_period():
    assert GEN.LESSON_SCHEDULE_PERIOD == len(GEN.SCHEDULE_PROFILES) == 12
