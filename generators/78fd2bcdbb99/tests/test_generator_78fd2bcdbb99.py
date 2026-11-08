"""Focused regressions for generator 78fd2bcdbb99."""
from __future__ import annotations

import copy
import importlib
import json
import random

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "78fd2bcdbb99"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.78fd2bcdbb99.generator"
)
BANDS = (None, "easy", "medium", "hard")


def test_all_canonical_pairs_are_accepted_and_exact() -> None:
    assert hasattr(GEN, "rule_mirror")
    root = find_root(__file__)
    labeled = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    assert len(labeled) >= 3
    for pair in labeled:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original

    all_inputs = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            for split in ("train", "test"):
                all_inputs.extend(normalize_grid(pair["input"]) for pair in row[split])
    assert len(all_inputs) > len(labeled)
    assert all(GEN.self_check(grid) == [] for grid in all_inputs)


def test_schedule_covers_both_axes_and_multicolor_in_every_band() -> None:
    assert hasattr(GEN, "semantic_observables")
    for band_index, band in enumerate(BANDS):
        facts = [
            GEN.semantic_observables(
                GEN.generate(10_000 + band_index, index, difficulty=band)
            )
            for index in range(4)
        ]
        assert {row["selected_axis"] for row in facts} == {"lr", "ud"}
        assert 1 in {row["palette_size"] for row in facts}
        assert any(row["palette_size"] >= 2 for row in facts)
        assert all(row["fillable_count"] >= 1 for row in facts)


def test_exact_override_boundaries_and_advertised_missing_count() -> None:
    cases = [
        {
            "grid_h": 4,
            "grid_w": 5,
            "n_missing": 3,
            "symmetry_axis": "ud",
            "palette_size": 3,
            "anchor_corner": True,
            "density": 0.2,
            "color": 7,
        },
        {
            "grid_h": 10,
            "grid_w": 14,
            "n_missing": 1,
            "symmetry_axis": "lr",
            "palette_size": 1,
            "anchor_corner": False,
            "density": 0.6,
            "color": 9,
        },
    ]
    for band in BANDS:
        for index, requested in enumerate(cases):
            grid = GEN.generate(20_000 + index, index, difficulty=band, **requested)
            facts = GEN.semantic_observables(grid)
            assert (len(grid), len(grid[0])) == (
                requested["grid_h"],
                requested["grid_w"],
            )
            assert facts["selected_axis"] == requested["symmetry_axis"]
            assert facts["palette_size"] == requested["palette_size"]
            assert facts["fillable_count"] == requested["n_missing"]
            assert GEN.self_check(grid) == []


def test_invalid_calls_fail_loudly_without_bool_aliases() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=7)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="expert")
    with pytest.raises(ValueError, match="grid_h"):
        GEN.generate(1, 0, grid_h=True)
    with pytest.raises(ValueError, match="symmetry_axis"):
        GEN.generate(1, 0, symmetry_axis="diagonal")
    with pytest.raises(ValueError, match="palette_size"):
        GEN.generate(1, 0, palette_size=4)


def test_determinism_fresh_returns_and_global_rng_isolation() -> None:
    random.seed(20261026)
    state = random.getstate()
    first = GEN.generate(424242, 17, difficulty="hard")
    second = GEN.generate(424242, 17, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert random.getstate() == state
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
    assert GEN.generate(424242, 17, difficulty="hard") == second


def test_hard_defaults_respect_declared_height_maximum() -> None:
    heights = {
        len(GEN.generate(seed, index, difficulty="hard"))
        for seed in range(8)
        for index in range(4)
    }
    assert min(heights) >= 9
    assert max(heights) <= 10
