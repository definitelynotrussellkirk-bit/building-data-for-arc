"""Focused regression suite for generator e4c4a1290088."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

import pytest

TASK_ID = "e4c4a1290088"
HOME = Path(__file__).resolve().parents[1]
LIBRARY = next(
    (path for path in Path(__file__).resolve().parents if (path / "shared/runtime").is_dir()),
    None,
)
if LIBRARY is not None:
    sys.path.insert(0, str(LIBRARY / "shared/runtime"))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    candidate = os.environ.get("GENERATOR_UNDER_TEST")
    path = Path(candidate).resolve() if candidate else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("review_e4c4a1290088", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def _signature(grid):
    observed = gen.observe_overrides(grid)
    return observed["grid_h"], observed["grid_w"], observed["n_labels"]


def test_source_binding_and_axis_surface_are_exact():
    assert gen.RULE_HASH == "b1a9cb7a0f30"
    assert gen.VERSION == "3.0.0"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_labels"}
    assert tuple(gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS) == ()


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_accepts_every_canonical_pair_and_mirrors_the_rule(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.oracle_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 6, "grid_w": 18, "n_labels": 5},
        {"grid_h": 18, "grid_w": 6, "n_labels": 2},
        {"grid_h": 11, "grid_w": 13, "n_labels": 4},
    ],
)
def test_exact_overrides_are_honored_in_every_band(band, overrides):
    grid = gen.generate(173, 29, difficulty=band, **overrides)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 5},
        {"grid_h": 19},
        {"grid_w": True},
        {"grid_w": 8.5},
        {"n_labels": 1},
        {"n_labels": 6},
        {"n_labels": "3"},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_grids_are_deterministic_and_refute_named_shortcuts(band):
    for index in range(32):
        grid = gen.generate(9001, index, difficulty=band)
        assert grid == gen.generate(9001, index, difficulty=band)
        assert gen.self_check(grid) == []
        expected = gen.oracle_output(grid)
        assert expected != grid
        observed = gen.observe_overrides(grid)
        assert observed["grid_h"] == len(grid)
        assert observed["grid_w"] == len(grid[0])
        assert 2 <= observed["n_labels"] <= 5
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(grid) != expected, (band, index, name)
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            assert witness(grid), (band, index, name)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_curriculum_covers_all_official_profiles_in_every_band(band):
    official = {(6, 6, 3), (7, 7, 2), (8, 8, 3)}
    observed = {_signature(gen.generate(77, index, difficulty=band)) for index in range(12)}
    assert official <= observed


def test_two_demo_lessons_are_semantically_identifiable():
    grids = [gen.generate(404, index, difficulty="medium") for index in range(3)]
    pairs = [{"input": grid, "output": gen.oracle_output(grid)} for grid in grids]
    assert gen.EXAMPLES_NEEDED == 2
    assert gen.lesson_identifiable(pairs[:2], pairs[2]) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in pairs[:2]), name


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 6 for _ in range(6)]],
)
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)
