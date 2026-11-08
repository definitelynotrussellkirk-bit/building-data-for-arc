"""Regression tests for the 521473faec65 distribution and teaching repair."""
from __future__ import annotations

from copy import deepcopy

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "521473faec65"
ROOT = find_root(__file__)
gen, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
BANDS = (None, "easy", "medium", "hard")
EXPECTED_RULE_HASH = "4409288b0253"


def components(grid):
    """Independent same-color 4-connected component extractor."""
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = [(row, col)]
            seen.add((row, col))
            cells = []
            for current_row, current_col in queue:
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    point = (next_row, next_col)
                    if (
                        0 <= next_row < height
                        and 0 <= next_col < width
                        and point not in seen
                        and grid[next_row][next_col] == color
                    ):
                        seen.add(point)
                        queue.append(point)
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            result.append(
                {
                    "color": color,
                    "cells": set(cells),
                    "box": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def oracle(grid, *, first_two_only=False, absolute_even=False):
    output = [[0 for _ in row] for row in grid]
    objects = components(grid)
    if first_two_only:
        objects = objects[:2]
    for obj in objects:
        row1, col1, row2, col2 = obj["box"]
        color = obj["color"]
        for row in range(row1, row2 + 1):
            for col in range(col1, col2 + 1):
                keep = (row + col) % 2 == 0 if absolute_even else (
                    (row - row1 + col - col1) % 2 == 0
                )
                if keep:
                    output[row][col] = color
    return output


def anchors(grid):
    return [(obj["box"][0], obj["box"][1]) for obj in components(grid)]


def touches_border(grid, obj):
    row1, col1, row2, col2 = obj["box"]
    return row1 == 0 or col1 == 0 or row2 == len(grid) - 1 or col2 == len(grid[0]) - 1


def test_public_contract_is_truthful_and_pinned():
    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_rects"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "three_odd_anchor",
        "two_even_anchor",
        "three_even_anchor",
        "two_odd_anchor",
    )
    assert not hasattr(gen, "LESSON_SCHEDULE_PERIOD")
    assert [gen.schedule_profile(0, index) for index in range(8)] == list(gen.SCHEDULE_PROFILES) * 2
    assert callable(gen.observe_overrides)
    assert callable(gen.strict_canonical_like)
    assert callable(gen.rule_mirror)
    assert callable(gen.lesson_identifiable)


@pytest.mark.parametrize("pair", canonical_pairs(TASK_ID, root=ROOT, labeled_only=True))
def test_canonical_inputs_are_lawful_and_oracle_matches(pair):
    source = pair["input"]
    assert gen.self_check(source) == []
    assert gen.strict_canonical_like(source) == []
    assert oracle(source) == pair["output"]
    assert gen.rule_mirror(source) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 6, "grid_w": 8, "n_rects": 2},
        {"grid_h": 6, "grid_w": 8, "n_rects": 3},
        {"grid_h": 12, "grid_w": 14, "n_rects": 2},
        {"grid_h": 12, "grid_w": 14, "n_rects": 3},
    ],
)
def test_exact_overrides_work_in_every_band(band, overrides):
    source = gen.generate(73, 5, difficulty=band, **overrides)
    assert gen.self_check(source) == []
    assert gen.observe_overrides(source) == overrides
    assert oracle(source) == gen.rule_mirror(source)



def test_default_two_rectangle_profiles_anchor_canonical_profiles_in_every_band():
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({value for row in pair["input"] for value in row}))
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    }
    for band in BANDS:
        checked = 0
        for index in range(40):
            if not gen.schedule_profile(0, index).startswith("two_"):
                continue
            source = gen.generate(7000 + index, index, difficulty=band)
            profile = (
                len(source),
                len(source[0]),
                len({value for row in source for value in row}),
            )
            assert profile in canonical_profiles, (band, index, profile)
            checked += 1
        assert checked == 20


def test_difficulty_bands_change_default_layouts_but_not_override_legality():
    differences = 0
    for index in range(12):
        outputs = {
            band: gen.generate(8100 + index, index, difficulty=band)
            for band in ("easy", "medium", "hard")
        }
        if len({repr(grid) for grid in outputs.values()}) > 1:
            differences += 1
        for band, source in outputs.items():
            assert gen.self_check(source) == [], (band, index)
    assert differences >= 8


@pytest.mark.parametrize("band", BANDS)
def test_default_distribution_is_lawful_replayable_and_varied(band):
    shapes = set()
    counts = set()
    normalized_layouts = set()
    anchor_parities = set()
    border_flags = set()
    dimensions = set()
    for index in range(96):
        source = gen.generate(1000 + index, index, difficulty=band)
        assert source == gen.generate(1000 + index, index, difficulty=band)
        assert gen.self_check(source) == [], (band, index)
        observed = gen.observe_overrides(source)
        assert observed == {
            "grid_h": len(source),
            "grid_w": len(source[0]),
            "n_rects": len(components(source)),
        }
        objects = components(source)
        shapes.add((len(source), len(source[0])))
        counts.add(len(objects))
        dimensions.update(
            (obj["box"][2] - obj["box"][0] + 1, obj["box"][3] - obj["box"][1] + 1)
            for obj in objects
        )
        anchor_parities.update((row + col) % 2 for row, col in anchors(source))
        border_flags.update(touches_border(source, obj) for obj in objects)
        normalized_layouts.add(
            tuple(sorted((obj["box"][0], obj["box"][1], obj["box"][2], obj["box"][3]) for obj in objects))
        )
    assert counts == {2, 3}
    assert anchor_parities == {0, 1}
    assert border_flags == {False, True}
    assert len(shapes) >= 12
    assert len(dimensions) >= 8
    assert len(normalized_layouts) >= 60


@pytest.mark.parametrize(
    "seed,sample_index,difficulty,overrides",
    [
        (True, 0, None, {}),
        (1.0, 0, None, {}),
        ("1", 0, None, {}),
        (1, True, None, {}),
        (1, 1.0, None, {}),
        (1, "1", None, {}),
        (1, -1, None, {}),
        (1, 0, "impossible", {}),
        (1, 0, None, {"typo_axis": 1}),
        (1, 0, None, {"grid_h": True}),
        (1, 0, None, {"grid_h": 5}),
        (1, 0, None, {"grid_w": 15}),
        (1, 0, None, {"n_rects": 1}),
        (1, 0, None, {"n_rects": 4}),
        (1, 0, None, {"n_rects": 2.0}),
        (1, 0, None, {"n_rects": "2"}),
    ],
)
def test_rejects_invalid_calls(seed, sample_index, difficulty, overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, difficulty=difficulty, **overrides)


def test_none_overrides_preserve_default_semantics():
    baseline = gen.generate(19, 7)
    with_none = gen.generate(19, 7, grid_h=None, grid_w=None, n_rects=None)
    assert with_none == baseline


def test_self_check_rejects_nonrectangles_touching_and_bad_palette():
    valid = gen.generate(42, 3, grid_h=8, grid_w=10, n_rects=2)

    hole = deepcopy(valid)
    obj = components(hole)[0]
    row1, col1, row2, col2 = obj["box"]
    hole[(row1 + row2) // 2][(col1 + col2) // 2] = 0
    assert gen.self_check(hole)

    touching = [[0] * 8 for _ in range(6)]
    for row in range(2):
        for col in range(2):
            touching[row][col] = 2
            touching[row][col + 2] = 3
    assert gen.self_check(touching)

    bad_color = deepcopy(valid)
    bad_color[0][0] = 10
    assert gen.self_check(bad_color)


@pytest.mark.parametrize("name", ["first_two_rectangles_only"])
def test_declared_canonical_shortcut_fits_all_public_pairs(name):
    rival = gen.CANONICAL_SHORTCUTS[name]
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert rival(pair["input"]) == pair["output"]


def test_schedule_and_every_query_rotation_refute_declared_rivals():
    assert set(gen.LESSON_COMPETITORS) >= {
        "first_two_rectangles_only",
        "absolute_even_checkerboard",
    }
    for band in BANDS:
        for start in range(12):
            lesson = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                source = gen.generate(20261012, start + offset, difficulty=band)
                lesson.append({"input": source, "output": oracle(source)})
            for query_index in range(len(lesson)):
                demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                query = lesson[query_index]
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


def test_semantic_witnesses_are_real_disagreements():
    three = gen.generate(7, 0, n_rects=3)
    odd = gen.generate(7, 3, n_rects=2)
    assert gen.SEMANTIC_WITNESSES["third_rectangle_transformed"](three)
    assert gen.SEMANTIC_RIVALS["first_two_rectangles_only"](three) != oracle(three)
    assert gen.SEMANTIC_WITNESSES["local_phase_from_odd_anchor"](odd)
    assert gen.SEMANTIC_RIVALS["absolute_even_checkerboard"](odd) != oracle(odd)
