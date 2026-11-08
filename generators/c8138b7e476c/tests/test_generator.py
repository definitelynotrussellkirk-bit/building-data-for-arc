from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "c8138b7e476c"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def test_rejects_unknown_override_key():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(3, 4, __typo_axis__=1)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 7, "grid_w": 7, "cells": 4, "n_colors": 2},
        {"grid_h": 13, "grid_w": 12, "cells": 12, "n_colors": 4},
    ],
)
def test_exact_overrides_are_observable_in_every_band(difficulty, options):
    grid = gen.generate(17, 9, difficulty=difficulty, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("grid_h", 8),
        ("grid_h", 7.0),
        ("grid_w", 6),
        ("cells", 3),
        ("cells", True),
        ("n_colors", 1),
        ("n_colors", "2"),
    ],
)
def test_rejects_invalid_exact_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_self_check_rejects_off_center_separator():
    grid = [
        [1, 0, 0],
        [9, 9, 9],
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
    ]
    assert any("center" in message or "equal" in message for message in gen.self_check(grid))


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 0]], [[True] * 7 for _ in range(7)]])
def test_self_check_handles_malformed_grids_without_raising(grid):
    assert gen.self_check(grid)


def test_canonical_inputs_are_lawful_and_python_oracle_matches():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen._mirror_top(pair["input"]) == pair["output"]


def test_semantic_witness_refutes_copy_in_order_rival():
    grid = gen.generate(712, 5, grid_h=9, grid_w=10, cells=5, n_colors=3)
    assert gen.SEMANTIC_WITNESSES["vertical_order_matters"](grid)
    assert gen.SEMANTIC_RIVALS["copy_top_in_order"](grid) != gen._mirror_top(grid)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_distribution_contains_canonical_profiles(difficulty):
    canonical_profiles = {(7, 8, 4), (9, 9, 4), (9, 10, 5)}
    seen = set()
    for index in range(40):
        grid = gen.generate(9000 + index, index, difficulty=difficulty)
        assert gen.self_check(grid) == []
        palette_size = len({value for row in grid for value in row})
        seen.add((len(grid), len(grid[0]), palette_size))
    assert seen & canonical_profiles


def test_deterministic_for_same_request():
    kwargs = {"grid_h": 11, "grid_w": 9, "cells": 8, "n_colors": 4}
    assert gen.generate(81, 13, difficulty="hard", **kwargs) == gen.generate(
        81, 13, difficulty="hard", **kwargs
    )
