"""Regressions for the 2026-10-21 review repair.

These tests cover the production call contract and the finite teaching schedule.
The separate parametric tests cover only a proposed, non-production prototype.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from statistics import median
import sys

import pytest

from reviewer_support import find_root


TASK_ID = "3ab9aab86992"
ROOT = find_root(__file__)
GENERATOR_SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
GENERATOR_SHA256 = hashlib.sha256(GENERATOR_SOURCE.read_bytes()).hexdigest()


def _load_task_generator():
    dependency_root = ROOT / "shared" / "runtime"
    spec = importlib.util.spec_from_file_location(
        f"review_20261021_{GENERATOR_SHA256}", GENERATOR_SOURCE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    before = list(sys.path)
    try:
        sys.path.insert(0, str(dependency_root))
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = before
    return module


GEN = _load_task_generator()


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_nonliteral_integer_seed(bad_seed):
    with pytest.raises((TypeError, ValueError), match="seed"):
        GEN.generate(bad_seed, 0, difficulty="medium")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index(bad_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        GEN.generate(17, bad_index, difficulty="medium")


def test_multi_axis_rejections_name_the_conflicting_controls():
    with pytest.raises(ValueError) as caught:
        GEN.generate(0, 0, texture="all_corners", n_corners=1)
    assert set(caught.value.incompatible_axes) == {"texture", "n_corners"}


@pytest.mark.parametrize(
    ("difficulty", "expected"),
    [
        ("easy", (1, 2, 4, 4)),
        (None, (2, 3, 4, 4)),
        ("medium", (2, 3, 4, 4)),
        ("hard", (3, 3, 4, 4)),
    ],
)
def test_declared_cardinality_schedule_is_realized(difficulty, expected):
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    seed = 991
    phase = seed % GEN.LESSON_SCHEDULE_PERIOD
    rotated = expected[phase:] + expected[:phase]
    assert tuple(
        GEN.schedule_n_corners(seed, index, difficulty=difficulty)
        for index in range(GEN.LESSON_SCHEDULE_PERIOD)
    ) == rotated
    realized = tuple(
        GEN.observe_overrides(
            GEN.generate(seed, index, difficulty=difficulty)
        )["n_corners"]
        for index in range(GEN.LESSON_SCHEDULE_PERIOD)
    )
    assert realized == rotated


def test_default_seed_sample_correlation_retains_canonical_like_object_density():
    """Mirror the distribution gate's seed/sample-index calling convention."""
    counts = []
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(1, 21):
            grid = GEN.generate(seed, seed, difficulty=difficulty)
            counts.append(GEN.observe_overrides(grid)["n_corners"])
    assert median(counts) >= 3


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_query_rotation_refutes_complete_all_corners(difficulty):
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.SEMANTIC_RIVALS)
    pairs = []
    for sample_index in range(GEN.LESSON_SCHEDULE_PERIOD):
        grid = GEN.generate(431, sample_index, difficulty=difficulty)
        pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})

    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert any(
            GEN.SEMANTIC_RIVALS["complete_all_corners"](pair["input"])
            != pair["output"]
            for pair in demos
        )
        assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("sample_index", range(8))
def test_explicit_cardinality_override_wins_over_schedule(sample_index):
    for requested in range(1, 5):
        grid = GEN.generate(
            81,
            sample_index,
            difficulty="hard",
            n_corners=requested,
            palette_size=1,
        )
        assert GEN.observe_overrides(grid)["n_corners"] == requested
