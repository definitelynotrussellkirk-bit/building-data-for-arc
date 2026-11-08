"""Task-local regressions for shape-match/majority-key curriculum."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from probe_support import (  # noqa: E402
    canonical_pairs,
    components,
    first_match_only_rival,
    largest_marker_color_rival,
    load_generator,
    marker_counts,
    normalized,
    oracle,
    recolor_all_green_rival,
    same_cell_count_rival,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_and_canonical_authority_are_supported():
    assert getattr(gen, "RULE_HASH", None) == "d5061c3b9df5"
    for pair in canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_boundary_controls_are_realized_in_every_band(band):
    controls = {
        "grid_h": 10,
        "grid_w": 12,
        "template_shape": "zigzag5",
        "n_matches": 2,
        "n_distractors": 2,
        "majority_color": 4,
        "majority_count": 3,
        "n_marker_colors": 3,
    }
    grid = gen.generate(17, 9, difficulty=band, **controls)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == controls


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 9},
        {"grid_w": 19},
        {"template_shape": "circle"},
        {"n_matches": 0},
        {"n_distractors": 3},
        {"majority_color": 3},
        {"majority_count": 4},
        {"n_marker_colors": 4},
        {"grid_h": True},
        {"n_matches": 1.0},
    ],
)
def test_invalid_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_scenes_refute_recolor_all_and_same_size_shortcuts(band):
    for index in range(24):
        grid = gen.generate(200 + index, index, difficulty=band)
        target = normalized(components(grid, 1)[0])
        distractors = [c for c in components(grid, 3) if normalized(c) != target]
        assert distractors, (band, index)
        assert any(len(c) == len(target) for c in distractors), (band, index)
        expected = oracle(grid)
        assert recolor_all_green_rival(grid) != expected
        assert same_cell_count_rival(grid) != expected


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_three_demo_window_refutes_declared_lesson_competitors(band):
    assert set(gen.CANONICAL_SHORTCUTS) <= set(gen.LESSON_COMPETITORS)
    for start in range(12):
        grids = [gen.generate(311, start + offset, difficulty=band) for offset in range(3)]
        demos = [{"input": grid, "output": oracle(grid)} for grid in grids]
        query_grid = gen.generate(311, start + 3, difficulty=band)
        query = {"input": query_grid, "output": oracle(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                band,
                start,
                name,
            )


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_is_lawful_deterministic_and_varied(band):
    shapes = set()
    match_counts = set()
    distractor_counts = set()
    majority_colors = set()
    dimensions = set()
    unique = set()
    for index in range(96):
        grid = gen.generate(9000 + index, index, difficulty=band)
        assert grid == gen.generate(9000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        shapes.add(observed["template_shape"])
        match_counts.add(observed["n_matches"])
        distractor_counts.add(observed["n_distractors"])
        majority_colors.add(observed["majority_color"])
        dimensions.add((len(grid), len(grid[0])))
        unique.add(tuple(map(tuple, grid)))
        saved = deepcopy(grid)
        _ = oracle(grid)
        for rival in gen.LESSON_COMPETITORS.values():
            _ = rival(grid)
        assert grid == saved
    assert len(shapes) >= 5
    assert match_counts == {1, 2}
    assert distractor_counts == {1, 2}
    assert 9 in majority_colors and len(majority_colors) >= 4
    assert len(dimensions) >= 3
    assert len(unique) >= 90


def test_canonical_shortcuts_really_fit_all_canonical_pairs():
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", {})
    assert shortcuts
    for name, rival in shortcuts.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name


def test_semantic_witnesses_are_real_counterexamples():
    witnessed = Counter()
    for index in range(36):
        grid = gen.generate(777, index)
        expected = oracle(grid)
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                witnessed[name] += 1
                assert any(
                    gen.SEMANTIC_RIVALS[rival](grid) != expected
                    for rival in gen.WITNESS_RIVALS[name]
                ), name
    assert set(witnessed) == set(gen.SEMANTIC_WITNESSES)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(10)], [[10] * 12 for _ in range(10)]],
)
def test_malformed_grids_return_reasons_instead_of_raising(grid):
    assert gen.self_check(grid)


def test_generated_marker_contract_is_strict_majority_of_isolated_singletons():
    for index in range(30):
        grid = gen.generate(818, index)
        counts = marker_counts(grid)
        winner = max(counts, key=lambda color: (counts[color], color))
        assert list(counts.values()).count(counts[winner]) == 1
        assert counts[winner] in (2, 3)
        assert all(len(component) == 1 for color in counts for component in components(grid, color))
        assert oracle(grid) != grid


def test_independent_named_rivals_match_generator_contract():
    grid = gen.generate(42, 0, majority_color=4, n_matches=2)
    assert gen.SEMANTIC_RIVALS["recolor_all_green"](grid) == recolor_all_green_rival(grid)
    assert gen.SEMANTIC_RIVALS["same_cell_count"](grid) == same_cell_count_rival(grid)
    assert gen.SEMANTIC_RIVALS["largest_marker_color"](grid) == largest_marker_color_rival(grid)
    assert gen.SEMANTIC_RIVALS["first_match_only"](grid) == first_match_only_rival(grid)
