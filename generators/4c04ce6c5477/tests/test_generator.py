"""Regression and semantic-distribution tests for 4c04ce6c5477."""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    analyze,
    area_output,
    canonical_pairs,
    height_output,
    left_to_right_output,
    load_generator,
    numeric_color_output,
    observed,
    top_to_bottom_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_and_exact_axis_surface():
    assert gen.RULE_HASH == "cf026680a0b6"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_blobs"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_examples_are_accepted_and_match_height_rule(pair):
    assert gen.self_check(pair["input"]) == []
    assert height_output(pair["input"]) == pair["output"]
    assert gen.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 7, "grid_w": 10, "n_blobs": 5},
        {"grid_h": 8, "grid_w": 12, "n_blobs": 3},
        {"grid_h": 16, "grid_w": 18, "n_blobs": 2},
    ],
)
def test_exact_overrides_are_constructive_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid, difficulty=band) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 6),
        ("grid_h", 17),
        ("grid_w", 9),
        ("grid_w", 19),
        ("n_blobs", 1),
        ("n_blobs", 6),
        ("grid_h", True),
        ("grid_w", 12.5),
        ("n_blobs", "3"),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_deterministic_valid_and_refutes_shortcuts(band):
    counts = {
        "area": 0,
        "left": 0,
        "top": 0,
        "color": 0,
        "wide": 0,
        "nonrectangle": 0,
    }
    shapes: set[tuple[int, int, int]] = set()
    palettes: set[tuple[int, ...]] = set()

    for index in range(128):
        grid = gen.generate(3100 + index, index * 13, difficulty=band)
        assert grid == gen.generate(3100 + index, index * 13, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        facts = analyze(grid)
        intended = height_output(grid)
        counts["area"] += area_output(grid) != intended
        counts["left"] += left_to_right_output(grid) != intended
        counts["top"] += top_to_bottom_output(grid) != intended
        counts["color"] += numeric_color_output(grid) != intended
        counts["wide"] += any(obj["width"] > 1 for obj in facts["components"])
        counts["nonrectangle"] += any(
            obj["area"] < obj["height"] * obj["width"]
            for obj in facts["components"]
        )
        shapes.add((facts["height"], facts["width"], len(facts["components"])))
        palettes.add(tuple(sorted(obj["color"] for obj in facts["components"])))

    assert counts["area"] == 128
    assert counts["left"] >= 112
    assert counts["top"] >= 96
    assert counts["color"] >= 112
    assert counts["wide"] >= 120
    assert counts["nonrectangle"] >= 96
    assert len(shapes) >= 24
    assert len(palettes) >= 80


def test_area_witness_strictly_outsizes_tallest_for_replay_and_axis_domain():
    # Regression: seed 0 / sample 53 used to let the 2x2 tallest branch fill
    # its box, tying the one-row area witness at four cells.
    replay = gen.generate(0, 53, grid_h=7, grid_w=10, n_blobs=2)
    objects = sorted(analyze(replay)["components"], key=lambda obj: -obj["height"])
    assert objects[1]["area"] > objects[0]["area"]

    # The strict inequality is constructive, so sample every advertised exact
    # axis tuple in every difficulty route rather than relying on frequency.
    for band_index, band in enumerate((None, "easy", "medium", "hard")):
        for grid_h in range(7, 17):
            for grid_w in range(10, 19):
                for n_blobs in range(2, 6):
                    grid = gen.generate(
                        9100 + band_index * 1000 + grid_h * 37 + grid_w,
                        n_blobs * 101,
                        difficulty=band,
                        grid_h=grid_h,
                        grid_w=grid_w,
                        n_blobs=n_blobs,
                    )
                    ranked = sorted(
                        analyze(grid)["components"], key=lambda obj: -obj["height"]
                    )
                    assert ranked[1]["area"] > ranked[0]["area"]


def test_semantic_hooks_name_real_counterexamples():
    for index in range(32):
        grid = gen.generate(8100 + index, index, difficulty="medium")
        assert gen.SEMANTIC_WITNESSES["height_not_area"](grid)
        assert gen.SEMANTIC_RIVALS["largest_area_first"](grid) == area_output(grid)
        assert gen.SEMANTIC_RIVALS["largest_area_first"](grid) != height_output(grid)


def test_lesson_identifiable_rejects_a_surviving_shortcut():
    pair = canonical_pairs()[0]
    reasons = gen.lesson_identifiable([pair], canonical_pairs()[2])
    assert any("left_to_right" in reason or "largest_area_first" in reason for reason in reasons)


def test_self_check_rejects_ties_mixed_components_and_malformed_grids():
    tied = [
        [1, 0, 2],
        [1, 0, 2],
    ]
    mixed = [
        [1, 2, 0],
        [1, 2, 3],
    ]
    duplicate_color = [
        [1, 0, 1],
        [1, 0, 0],
        [1, 0, 0],
    ]
    for grid in (tied, mixed, duplicate_color, None, [], [[]], [[0], [0, 1]]):
        assert gen.self_check(grid)
