"""Unit tests for the source-bound lesson/rival census."""
from __future__ import annotations

import importlib.util
from pathlib import Path


PROBE = Path(__file__).resolve().parents[1] / "workspace" / "lesson_probe.py"
spec = importlib.util.spec_from_file_location("lesson_probe_under_test", PROBE)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class _FakeGenerator:
    @staticmethod
    def _identity(grid):
        return [row[:] for row in grid]

    @staticmethod
    def _increment(grid):
        return [[value + 1 for value in row] for row in grid]

    LESSON_COMPETITORS = {
        "identity": _identity.__func__,
        "increment": _increment.__func__,
    }

    @staticmethod
    def lesson_identifiable(demos, query):
        return []


def test_assess_lesson_iterates_declared_rivals_and_detects_survival():
    demos = [
        {"input": [[0]], "output": [[1]]},
        {"input": [[2]], "output": [[3]]},
        {"input": [[4]], "output": [[5]]},
    ]
    query = {"input": [[7]], "output": [[8]]}

    result = probe.assess_lesson(_FakeGenerator, demos, query)

    assert result["rivals"]["identity"] == {
        "demo_refuted": True,
        "query_disagreement": True,
        "query_relevant_survival": False,
    }
    assert result["rivals"]["increment"] == {
        "demo_refuted": False,
        "query_disagreement": False,
        "query_relevant_survival": False,
    }
    assert result["lesson_identifiable_reasons"] == []
