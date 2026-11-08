"""Task-local regression tests for generator 9349fabc466a."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    candidate = os.environ.get("GENERATOR_UNDER_TEST")
    path = Path(candidate) if candidate else HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _pairs():
    return canonical_pairs(gen.TASK_ID, root=find_root(__file__), labeled_only=True)


@pytest.mark.parametrize("pair", _pairs(), ids=lambda p: p.get("split", "canonical"))
def test_canonical_examples_match_independent_python_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen._reference_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_shape": "5x5"},
        {"n_colors": 1},
        {"n_colors": 4},
        {"n_colors": True},
        {"palette_kind": "unknown"},
    ],
)
def test_invalid_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band):
    expected = {"grid_shape": "7x9", "n_colors": 3, "palette_kind": "high"}
    grid = gen.generate(17, 9, difficulty=band, **expected)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == expected


def test_default_distribution_covers_canonical_profiles_and_all_witnesses():
    canonical_profiles = {(5, 7, 3), (7, 9, 3), (8, 8, 3)}
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(8000 + i, 300 + i, difficulty=band) for i in range(40)]
        assert any((len(g), len(g[0]), len({v for row in g for v in row})) in canonical_profiles
                   for g in grids)
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            assert any(predicate(g) for g in grids), (band, name)


def test_declared_canonical_shortcuts_fit_canonical_and_are_refuted_by_generation():
    pairs = _pairs()
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
        assert any(
            rival(grid) != gen._reference_output(grid)
            for grid in (gen.generate(9100 + i, i, difficulty="hard") for i in range(80))
        ), name


def test_every_four_pair_lesson_is_identifiable_under_all_query_rotations():
    # The production materializer consumes consecutive accepted indices.  Every
    # four-pair window must retain a comprehensive teaching example after any
    # one pair is held out as query.
    for start in range(12):
        lesson = []
        for index in range(start, start + 4):
            grid = gen.generate(12001, index, difficulty="medium")
            lesson.append({"input": grid, "output": gen._reference_output(grid)})
        for query_index in range(4):
            query = lesson[query_index]
            demos = [pair for i, pair in enumerate(lesson) if i != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (start, query_index)


def test_generation_is_deterministic_and_realizes_every_requested_color():
    for n_colors in (2, 3):
        grid = gen.generate(73, 11, grid_shape="18x18", n_colors=n_colors,
                            palette_kind="mid")
        assert grid == gen.generate(73, 11, grid_shape="18x18", n_colors=n_colors,
                                    palette_kind="mid")
        assert len({v for row in grid for v in row if v}) == n_colors
        assert gen.self_check(grid) == []
