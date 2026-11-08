"""Regression tests for the selected aspect-recolor generator."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from probe import (  # noqa: E402
    canonical,
    color_spans_aspects,
    has_nonrectangle,
    load_generator,
    objects,
    observation,
    orientation,
    python_oracle,
)

gen = load_generator()


def test_rule_pin_matches_canonical_authority():
    assert getattr(gen, "RULE_HASH", None) == "b45100a04df9"


@pytest.mark.parametrize("pair", canonical(), ids=["train0", "train1", "train2", "test0"])
def test_canonical_inputs_are_accepted_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert python_oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("n_blobs,n_colors", [(3, 1), (3, 3), (4, 3), (5, 2), (6, 6)])
def test_joint_exact_controls_in_every_band(band, n_blobs, n_colors):
    requested = {
        "grid_h": 10,
        "grid_w": 12,
        "n_blobs": n_blobs,
        "n_distinct_colors": n_colors,
    }
    grid = gen.generate(29, 17, difficulty=band, **requested)
    assert observation(grid) == requested
    assert gen.observe_overrides(grid) == requested
    assert gen.self_check(grid) == []


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7),
        ("grid_h", 15),
        ("grid_w", 8),
        ("grid_w", 15),
        ("grid_h", True),
        ("grid_w", 10.5),
        ("n_blobs", 2),
        ("n_blobs", 7),
        ("n_distinct_colors", 0),
        ("n_distinct_colors", 7),
        ("n_blobs", "4"),
        ("palette_kind", "warm"),
        ("palette_size", 3),
        ("density", "sparse"),
        ("position_bias", "spread"),
        ("texture", "all_squares"),
    ],
)
def test_invalid_or_removed_controls_reject(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_incompatible_palette_count_has_axis_evidence():
    with pytest.raises(ValueError) as error:
        gen.generate(0, 0, n_blobs=3, n_distinct_colors=4)
    assert set(error.value.incompatible_axes) == {"n_blobs", "n_distinct_colors"}


@pytest.mark.parametrize("n_colors", range(1, 7))
def test_palette_override_alone_selects_enough_objects(n_colors):
    grid = gen.generate(7, 9, n_distinct_colors=n_colors)
    assert observation(grid)["n_distinct_colors"] == n_colors
    assert gen.self_check(grid) == []


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0]], [[0], [1, 2]], [[True, 0]], [[10, 0]], [[1.5]], ["00"], [[], []]],
)
def test_invalid_grids_are_reported_not_crashes(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_inputs_refute_both_canonical_shortcuts(band):
    signatures = set()
    first_aspects = set()
    for index in range(64):
        grid = gen.generate(91000 + index, index * 7 + 2, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert {orientation(cells) for _, cells in objects(grid)} == {"wide", "tall", "square"}
        assert has_nonrectangle(grid)
        assert color_spans_aspects(grid)
        assert python_oracle(grid) != python_oracle(grid, by_color=True)
        assert python_oracle(grid) != python_oracle(grid, fill=True)
        assert grid == gen.generate(91000 + index, index * 7 + 2, difficulty=band)
        before = deepcopy(grid)
        for rival in gen.LESSON_COMPETITORS.values():
            rival(grid)
        assert grid == before
        signatures.add(json.dumps(grid))
        first_aspects.add(orientation(objects(grid)[0][1]))
    assert len(signatures) == 64
    assert first_aspects == {"wide", "tall", "square"}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_retains_an_exact_canonical_size_palette_profile(band):
    canonical_profiles = {(8, 11, 4), (8, 12, 4), (9, 10, 4), (10, 10, 4)}
    observed = set()
    for index in range(20):
        grid = gen.generate(1729, index, difficulty=band)
        observed.add((len(grid), len(grid[0]), len({value for row in grid for value in row})))
    assert observed & canonical_profiles


def test_declared_canonical_shortcuts_fit_every_canonical_pair():
    assert set(gen.CANONICAL_SHORTCUTS) == {"group_by_color", "fill_bounding_boxes"}
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical()), name


def test_forced_constructive_fallback_keeps_counts_and_witnesses(monkeypatch):
    monkeypatch.setattr(gen, "_place_shape", lambda *args, **kwargs: None)
    for n_blobs in range(3, 7):
        grid = gen.generate(
            21,
            n_blobs,
            grid_h=10,
            grid_w=12,
            n_blobs=n_blobs,
            n_distinct_colors=min(3, n_blobs - 1),
        )
        assert observation(grid)["n_blobs"] == n_blobs
        assert gen.self_check(grid) == []
        assert python_oracle(grid) != python_oracle(grid, by_color=True)
        assert python_oracle(grid) != python_oracle(grid, fill=True)
