"""Focused regression tests for the corner-legend recoloring sampler."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "13a5c3f25c60"
ROOT = find_root(__file__)
gen, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def intended_output(grid):
    """Independent mirror of the unchanged corner-legend rule."""
    out = deepcopy(grid)
    source = grid[0][0]
    target = grid[0][-1]
    width = len(grid[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (r, c) not in {(0, 0), (0, width - 1)} and value == source:
                out[r][c] = target
    return out


def below_top_row_only(grid):
    """Plausible canonical shortcut: recolor source cells only below row zero."""
    out = deepcopy(grid)
    source = grid[0][0]
    target = grid[0][-1]
    for r in range(1, len(grid)):
        for c, value in enumerate(grid[r]):
            if value == source:
                out[r][c] = target
    return out


def top_row_only(grid):
    """Plausible position shortcut: recolor only non-corner row-zero sources."""
    out = deepcopy(grid)
    source = grid[0][0]
    target = grid[0][-1]
    for c in range(1, len(grid[0]) - 1):
        if grid[0][c] == source:
            out[0][c] = target
    return out


def observed(grid):
    width = len(grid[0])
    source = grid[0][0]
    target = grid[0][-1]
    body = [
        value
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if (r, c) not in {(0, 0), (0, width - 1)}
    ]
    return {
        "grid_h": len(grid),
        "grid_w": width,
        "source_cells": sum(value == source for value in body),
        "distractors": sum(value not in (0, source, target) for value in body),
    }


def lesson(seed, start, band):
    pairs = []
    for offset in range(gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": intended_output(grid)})
    return pairs


def test_pins_unchanged_authority_and_declares_only_exact_observable_axes():
    assert gen.RULE_HASH == "2ba5a8d2d710"
    assert set(gen.AXES) == {"grid_h", "grid_w", "source_cells", "distractors"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.CANONICAL_SHORTCUTS) == {"below_top_row_only"}
    assert set(gen.LESSON_COMPETITORS) == {
        "below_top_row_only",
        "top_row_only",
        "recolor_source_corner",
    }


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK_ID, root=ROOT, labeled_only=True),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_accepts_canonical_inputs_and_independent_oracle_matches(pair):
    assert gen.self_check(deepcopy(pair["input"])) == []
    assert gen.strict_canonical_like(deepcopy(pair["input"])) == []
    assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 7, "grid_w": 8, "source_cells": 2, "distractors": 0},
        {"grid_h": 9, "grid_w": 11, "source_cells": 8, "distractors": 6},
        {"grid_h": 8, "grid_w": 10, "source_cells": 3, "distractors": 2},
    ],
)
def test_exact_overrides_are_constructive_observable_and_deterministic(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(17, 9, difficulty=band, **options)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 6),
        ("grid_h", 10),
        ("grid_w", 7),
        ("grid_w", 12),
        ("source_cells", 1),
        ("source_cells", 9),
        ("distractors", -1),
        ("distractors", 7),
        ("grid_h", True),
        ("source_cells", 3.0),
        ("distractors", "2"),
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("bad", [(True, 0), (1.5, 0), (0, True), (0, -1)])
def test_rejects_nonliteral_seed_or_invalid_sample_index(bad):
    seed, sample_index = bad
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_generated_example_refutes_both_row_partition_shortcuts(band):
    for index in range(64):
        grid = gen.generate(7300 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        width = len(grid[0])
        source = grid[0][0]
        row0_sources = [c for c in range(1, width - 1) if grid[0][c] == source]
        lower_sources = [
            (r, c)
            for r in range(1, len(grid))
            for c, value in enumerate(grid[r])
            if value == source
        ]
        assert row0_sources
        assert lower_sources
        expected = intended_output(grid)
        assert below_top_row_only(grid) != expected
        assert top_row_only(grid) != expected
        assert gen.SEMANTIC_WITNESSES["row0_source"](grid)
        assert gen.SEMANTIC_WITNESSES["below_row0_source"](grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_cyclic_three_demo_lesson_refutes_declared_competitors(band):
    for start in range(16):
        pairs = lesson(314159, start, band)
        for query_index in range(len(pairs)):
            query = pairs[query_index]
            demos = pairs[:query_index] + pairs[query_index + 1 :]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_declared_canonical_shortcut_really_fits_all_canonical_pairs():
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert below_top_row_only(pair["input"]) == pair["output"]
        assert gen.CANONICAL_SHORTCUTS["below_top_row_only"](pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_has_canonical_profiles_in_every_band(band):
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    }
    hits = 0
    for index in range(20):
        grid = gen.generate(9000 + index, 7919 + index * 17, difficulty=band)
        profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        hits += int(profile in canonical_profiles)
    assert hits >= 8


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 8 for _ in range(7)],
        [[0] * 8 for _ in range(7)],
    ],
)
def test_malformed_grids_return_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_lessons_make_target_color_neither_palette_extreme(band):
    """Refute generic first/last-output-color attribution in every ordinary pair."""
    for index in range(64):
        grid = gen.generate(88000 + index, index, difficulty=band)
        colors = sorted({value for row in grid for value in row if value})
        target = grid[0][-1]
        assert len(colors) >= 3
        assert colors[0] < target < colors[-1]
