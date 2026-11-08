"""Focused regression tests for generator 20014c9d3729."""

from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import itertools
import random

import pytest

from src.core.canonical_pairs import load_task_pairs


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", Path(__file__).resolve().parents[1] / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_20014c9d3729_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_pairs():
    for ancestor in Path(__file__).resolve().parents:
        for relative in (
            Path("shared/data/canonical/puzzles.jsonl"),
            Path("data/canonical/puzzles.jsonl"),
        ):
            canonical = ancestor / relative
            if canonical.is_file():
                return load_task_pairs(gen.TASK_ID, canonical=canonical)
    raise FileNotFoundError("could not locate canonical puzzles.jsonl")


def test_rule_pin_and_all_public_pairs_are_accepted_and_solved():
    assert gen.RULE_HASH == "0149d1fbd1ae"
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_unknown_override_and_invalid_difficulty_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=7)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 8,
            "grid_w": 9,
            "n_colors": 2,
            "total_objects": 5,
            "threshold_counterexample": False,
        },
        {
            "grid_h": 16,
            "grid_w": 18,
            "n_colors": 4,
            "total_objects": 8,
            "threshold_counterexample": True,
        },
        {
            "grid_h": 8,
            "grid_w": 9,
            "n_colors": 4,
            "total_objects": 5,
            "threshold_counterexample": True,
        },
    ],
)
def test_exact_override_boundaries_are_observable_in_every_band(band, overrides):
    grid = gen.generate(1007, 13, difficulty=band, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides


def test_threshold_axis_is_semantic_not_cosmetic():
    ordinary = gen.generate(
        91,
        0,
        grid_h=9,
        grid_w=10,
        n_colors=3,
        total_objects=5,
        threshold_counterexample=False,
    )
    counterexample = gen.generate(
        91,
        1,
        grid_h=9,
        grid_w=10,
        n_colors=3,
        total_objects=5,
        threshold_counterexample=True,
    )
    rival = gen.SEMANTIC_RIVALS["fixed_size_threshold_four"]
    assert rival(ordinary) == gen.rule_mirror(ordinary)
    assert rival(counterexample) != gen.rule_mirror(counterexample)
    assert gen.SEMANTIC_WITNESSES["relative_size_not_absolute"](counterexample)


def test_default_schedule_puts_a_decisive_witness_in_every_two_examples():
    for band in (None, "easy", "medium", "hard"):
        for start in range(12):
            grids = [gen.generate(77, index, difficulty=band) for index in range(start, start + 2)]
            assert any(
                gen.SEMANTIC_WITNESSES["relative_size_not_absolute"](grid)
                for grid in grids
            )


def test_all_boundary_cross_products_construct_valid_exact_scenes():
    # The smallest canvas with the largest object count is the packing stress case.
    for band, h, w, n_colors, n_objects, counterexample in itertools.product(
        (None, "easy", "medium", "hard"),
        (8, 16),
        (9, 18),
        (2, 4),
        (5, 8),
        (False, True),
    ):
        overrides = {
            "grid_h": h,
            "grid_w": w,
            "n_colors": n_colors,
            "total_objects": n_objects,
            "threshold_counterexample": counterexample,
        }
        grid = gen.generate(381, 5, difficulty=band, **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides


def test_broad_default_sweep_is_lawful_and_deterministic():
    for band in (None, "easy", "medium", "hard"):
        for index in range(40):
            first = gen.generate(5000 + index, index, difficulty=band)
            second = gen.generate(5000 + index, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert gen.self_check(first) == []
            observed = gen.observe_overrides(first)
            assert 8 <= observed["grid_h"] <= 16
            assert 9 <= observed["grid_w"] <= 18
            assert 2 <= observed["n_colors"] <= 4
            assert 5 <= observed["total_objects"] <= 8


def test_generation_does_not_touch_global_random_state():
    random.seed(123456)
    before = random.getstate()
    gen.generate(222, 8, difficulty="easy")
    assert random.getstate() == before


def test_self_check_rejects_ambiguous_or_malformed_inputs():
    base = gen.generate(
        12,
        4,
        grid_h=8,
        grid_w=9,
        n_colors=2,
        total_objects=5,
        threshold_counterexample=False,
    )

    ragged = copy.deepcopy(base)
    ragged[0].pop()
    assert any("rectangular" in error for error in gen.self_check(ragged))

    invalid = copy.deepcopy(base)
    invalid[0][0] = 10
    assert any("ARC colors" in error for error in gen.self_check(invalid))

    blank = [[0 for _ in row] for row in base]
    assert gen.self_check(blank)
