"""Regression tests for the descending-area object-gallery generator."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    RIVALS,
    bbox_area_output,
    bottom_aligned_output,
    canonical_pairs,
    color_order_output,
    load_generator,
    objects,
    observed,
    racket_outputs,
    rule_output,
    scan_order_output,
    tie_by_color_output,
    ascending_area_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize(
    "pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"]
)
def test_canonical_pairs_are_owned_and_match_independent_rule(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert rule_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_metadata_and_exact_axis_contract_are_pinned():
    assert gen.GENERATOR_ID == "33d2674e3094"
    assert gen.TASK_ID == "33d2674e3094"
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "9f849a344655"
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.AXES) == {"profile", "area_pattern"}
    assert tuple(gen.PROFILES) == ("p8x13", "p9x12", "p10x11")
    assert tuple(gen.AREA_PATTERNS) == ("tie_443", "distinct_653", "distinct_643")
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()
    assert gen.LAWFUL_DEGENERATE_TEXTURES == ()
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", ["p8x13", "p9x12", "p10x11"])
@pytest.mark.parametrize("area_pattern", ["tie_443", "distinct_653", "distinct_643"])
def test_every_joint_override_is_constructive_exact_and_observable(
    band, profile, area_pattern
):
    requested = {"profile": profile, "area_pattern": area_pattern}
    grid = gen.generate(91, 7, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested
    assert rule_output(grid) != grid
    assert gen.rule_mirror(grid) == rule_output(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo_axis", 1),
        ("profile", "p9x13"),
        ("profile", 9),
        ("profile", True),
        ("area_pattern", "distinct"),
        ("area_pattern", 443),
        ("area_pattern", True),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", ["trivial", 0.5, True])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


def test_only_real_canonical_shortcut_is_declared_and_proved():
    pairs = canonical_pairs()
    assert set(gen.CANONICAL_SHORTCUTS) == {"tie_by_color"}
    assert all(tie_by_color_output(pair["input"]) == pair["output"] for pair in pairs)
    assert all(
        gen.CANONICAL_SHORTCUTS["tie_by_color"](pair["input"]) == pair["output"]
        for pair in pairs
    )
    for name, rival in {
        "ascending_area": ascending_area_output,
        "bbox_area": bbox_area_output,
        "scan_order": scan_order_output,
        "color_order": color_order_output,
        "bottom_aligned": bottom_aligned_output,
    }.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in pairs), name


@pytest.mark.parametrize("area_pattern", ["tie_443", "distinct_653", "distinct_643"])
def test_generated_scenes_refute_structural_rivals(area_pattern):
    grid = gen.generate(
        404,
        3,
        profile="p8x13",
        area_pattern=area_pattern,
    )
    expected = rule_output(grid)
    authority_colors = [
        obj["color"]
        for obj in sorted(
            objects(grid),
            key=lambda obj: (-obj["area"], *obj["bbox"]),
        )
    ]
    assert authority_colors != sorted(authority_colors, reverse=True), (
        "descending color must not reproduce authority order",
        authority_colors,
    )
    assert "descending_color_order" in gen.SEMANTIC_RIVALS
    assert gen.SEMANTIC_RIVALS["descending_color_order"](grid) != expected
    for name in ("ascending_area", "bbox_area", "scan_order", "color_order", "bottom_aligned"):
        assert RIVALS[name](grid) != expected, name
        assert gen.SEMANTIC_RIVALS[name](grid) != expected, name
    if area_pattern == "tie_443":
        assert tie_by_color_output(grid) != expected
        assert gen.SEMANTIC_RIVALS["tie_by_color"](grid) != expected
        assert gen.SEMANTIC_WITNESSES["bbox_tie_not_color_tie"](grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_four_example_window_and_query_rotation_is_identifiable(band):
    for start in range(12):
        pairs = []
        for index in range(start, start + 4):
            grid = gen.generate(700 + start, index, difficulty=band)
            pairs.append({"input": grid, "output": rule_output(grid)})
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == [], (
                band,
                start,
                query_index,
            )
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert any(
                    competitor(pair["input"]) != pair["output"] for pair in demos
                ), (band, start, query_index, name)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_is_deterministic_lawful_and_covers_contract(band):
    profiles = set()
    patterns = set()
    inputs = set()
    for index in range(60):
        grid = gen.generate(5000 + index, index, difficulty=band)
        assert grid == gen.generate(5000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == rule_output(grid)
        stats = observed(grid)
        assert stats == gen.observe_overrides(grid)
        profiles.add(stats["profile"])
        patterns.add(stats["area_pattern"])
        inputs.add(tuple(tuple(row) for row in grid))
    assert profiles == set(gen.PROFILES)
    assert patterns == set(gen.AREA_PATTERNS)
    assert len(inputs) >= 45


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 11 for _ in range(8)]],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_validator_rejects_destructive_mutations():
    blank = [[0 for _ in range(13)] for _ in range(8)]
    assert gen.self_check(blank)

    valid = gen.generate(83, 0, profile="p8x13", area_pattern="tie_443")

    missing_cell = deepcopy(valid)
    r, c = next((r, c) for r, row in enumerate(missing_cell) for c, v in enumerate(row) if v)
    missing_cell[r][c] = 0
    assert gen.self_check(missing_cell)

    split_color = deepcopy(valid)
    hits = [(r, c) for r, row in enumerate(split_color) for c, v in enumerate(row) if v]
    r, c = hits[len(hits) // 2]
    split_color[r][c] = next(color for color in range(1, 10) if color not in {v for row in valid for v in row})
    assert gen.self_check(split_color)

    unsupported_shape = [row[:-1] for row in valid]
    assert gen.self_check(unsupported_shape)


def test_rule_mirror_is_pure():
    grid = gen.generate(918, 2, area_pattern="distinct_653")
    original = deepcopy(grid)
    assert gen.rule_mirror(grid) == rule_output(grid)
    assert grid == original


def test_real_racket_reference_matches_independent_oracle():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(700, index, difficulty="hard") for index in range(12)]
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]


def test_declared_mutation_fixtures_are_all_rejected():
    for name, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), name
