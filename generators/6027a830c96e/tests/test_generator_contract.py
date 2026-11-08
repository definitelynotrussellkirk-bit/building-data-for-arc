"""Portable regressions for Select Panel by Border (6027a830c96e).

The helpers here independently recover exact monochrome frame components and
apply the visible selector/crop rule.  The Racket program remains the selected
label authority; this oracle only protects the generator's input grammar and
semantic teaching contract.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
from typing import Any

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "6027a830c96e"
ROOT = find_root(__file__)
TASK_HOME = next(
    path for path in Path(__file__).resolve().parents
    if (path / "generator.py").is_file()
)
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("selector_frame_generator_under_test", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)

BANDS = (None, "easy", "medium", "hard")


def _components(grid: list[list[int]]) -> list[dict[str, Any]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            todo = [(row, col)]
            cells: set[tuple[int, int]] = set()
            while todo:
                r, c = todo.pop()
                if not (0 <= r < height and 0 <= c < width):
                    continue
                if (r, c) in seen or grid[r][c] != color:
                    continue
                seen.add((r, c))
                cells.add((r, c))
                todo.extend(((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))
            rows = [r for r, _c in cells]
            cols = [c for _r, c in cells]
            result.append({
                "color": color,
                "cells": cells,
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
            })
    return result


def _perimeter(bbox: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    top, left, bottom, right = bbox
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }


def _frames(grid: list[list[int]]) -> list[dict[str, Any]]:
    result = []
    for component in _components(grid):
        top, left, bottom, right = component["bbox"]
        if bottom - top + 1 < 3 or right - left + 1 < 3:
            continue
        perimeter = _perimeter(component["bbox"])
        if all(grid[row][col] == component["color"] for row, col in perimeter):
            component = dict(component)
            component["exact"] = component["cells"] == perimeter
            result.append(component)
    return sorted(result, key=lambda frame: (frame["bbox"][1], frame["bbox"][0]))


def _facts(grid: list[list[int]]) -> dict[str, Any]:
    frames = _frames(grid)
    inside = {
        (row, col)
        for frame in frames
        for row in range(frame["bbox"][0], frame["bbox"][2] + 1)
        for col in range(frame["bbox"][1], frame["bbox"][3] + 1)
    }
    external = [
        (row, col, value)
        for row, line in enumerate(grid)
        for col, value in enumerate(line)
        if value and (row, col) not in inside
    ]
    assert len(external) == 1
    selector = external[0][2]
    selected = [frame for frame in frames if frame["color"] == selector]
    assert len(selected) == 1
    selected_frame = selected[0]
    assert selected_frame["exact"], "the selector must name a pure Racket frame component"
    index = frames.index(selected_frame)
    top, left, bottom, right = selected_frame["bbox"]
    output = [line[left + 1:right] for line in grid[top + 1:bottom]]
    areas = [
        (frame["bbox"][2] - frame["bbox"][0] + 1)
        * (frame["bbox"][3] - frame["bbox"][1] + 1)
        for frame in frames
    ]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": len(frames),
        "selector": selector,
        "frames": frames,
        "selected_index": index,
        "selected_area": areas[index],
        "largest_area": max(areas),
        "output": output,
        "palette_size": len({value for row in grid for value in row}),
    }


def _tight_crop(grid: list[list[int]]) -> list[list[int]]:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    if not cells:
        return []
    top = min(r for r, _c in cells)
    left = min(c for _r, c in cells)
    bottom = max(r for r, _c in cells)
    right = max(c for _r, c in cells)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": _facts(grid)["output"]}


def test_metadata_pins_rule_and_declares_only_observable_controls() -> None:
    assert GEN.RULE_HASH == "ca56dbdca539"
    assert GEN.VERSION == "4.0.0"
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.LESSON_SCHEDULE_PERIOD == 5
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_frames", "selector"}
    assert GEN.HELPFUL_TEXTURES == ()
    assert GEN.DEGENERATE_TEXTURES == ()


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "height,width,n_frames,selector",
    [
        (10, 14, 2, 1),
        (10, 14, 3, 9),
        (12, 17, 2, 9),
        (12, 17, 3, 1),
        (11, 16, 2, 5),
        (11, 16, 3, 5),
    ],
)
def test_joint_exact_controls_round_trip_pixels(
    band: str | None,
    height: int,
    width: int,
    n_frames: int,
    selector: int,
) -> None:
    expected = {
        "grid_h": height,
        "grid_w": width,
        "n_frames": n_frames,
        "selector": selector,
    }
    grid = GEN.generate(
        991,
        height * 1000 + width * 100 + n_frames * 10 + selector,
        difficulty=band,
        **expected,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == expected
    assert {name: _facts(grid)[name] for name in expected} == expected
    assert grid == GEN.generate(
        991,
        height * 1000 + width * 100 + n_frames * 10 + selector,
        difficulty=band,
        **expected,
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": 1},
        {"texture": "default"},
        {"palette_size": 5},
        {"position_bias": "varied"},
        {"grid_h": True},
        {"grid_h": 10.0},
        {"grid_w": "14"},
        {"n_frames": False},
        {"n_frames": 2.0},
        {"selector": "3"},
        {"grid_h": 9},
        {"grid_h": 13},
        {"grid_w": 13},
        {"grid_w": 18},
        {"n_frames": 1},
        {"n_frames": 4},
        {"selector": 0},
        {"selector": 10},
    ],
)
def test_invalid_and_retired_overrides_fail_loudly(kwargs: dict[str, Any]) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("seed", [True, 1.0, "1"])
def test_seed_is_strict_integer(seed: Any) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, 1.0, "1", -1])
def test_sample_index_is_strict_nonnegative_integer(sample_index: Any) -> None:
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


def test_none_means_no_override_and_bad_difficulty_fails() -> None:
    expected = GEN.generate(77, 8, difficulty="medium")
    actual = GEN.generate(
        77,
        8,
        difficulty="medium",
        grid_h=None,
        grid_w=None,
        n_frames=None,
        selector=None,
    )
    assert actual == expected
    with pytest.raises(ValueError):
        GEN.generate(0, 0, difficulty="expert")


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        [[]],
        [[0], [0, 0]],
        [[True] * 14 for _ in range(10)],
        [[1.5] + [0] * 13 for _ in range(10)],
        [[10] + [0] * 13 for _ in range(10)],
        [[0] * 14 for _ in range(9)],
        [[0] * 18 for _ in range(10)],
    ],
)
def test_validator_rejects_malformed_grids_without_throwing(bad: Any) -> None:
    assert GEN.self_check(bad)


def test_all_canonical_pairs_are_owned_and_match_independent_rule() -> None:
    rows = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(rows) == 5
    for pair in rows:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert _facts(pair["input"])["output"] == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_retained_connected_component_counterexample_is_rejected() -> None:
    path = TASK_HOME / "counterexamples" / "own_border_color_merges_frame.json"
    row = json.loads(path.read_text(encoding="utf-8"))
    assert row["task_id"] == TASK
    assert row["rule_hash"] == GEN.RULE_HASH
    assert GEN.self_check(row["input"])
    assert any("frame" in reason.lower() for reason in GEN.self_check(row["input"]))


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_default_schedule_has_exact_canonical_profiles_and_no_single_choice_shortcut(band: str) -> None:
    canonical_profiles = {
        (10, 14, 6),
        (11, 15, 6),
        (10, 17, 7),
        (12, 15, 5),
        (12, 17, 7),
    }
    seen_profiles: set[str] = set()
    frame_counts: set[int] = set()
    selected_indices: set[int] = set()
    selectors: set[int] = set()
    for index in range(40):
        grid = GEN.generate(1200 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        facts = _facts(grid)
        assert (facts["grid_h"], facts["grid_w"], facts["palette_size"]) in canonical_profiles
        assert facts["selected_area"] < facts["largest_area"]
        assert _tight_crop(facts["output"]) != facts["output"]
        seen_profiles.add(GEN.schedule_profile(1200 + index, index, band))
        frame_counts.add(facts["n_frames"])
        selected_indices.add(facts["selected_index"])
        selectors.add(facts["selector"])
    assert seen_profiles == set(GEN.SCHEDULE_PROFILES)
    assert frame_counts == {2, 3}
    assert {0, 1, 2}.issubset(selected_indices)
    assert len(selectors) >= 7


def test_declared_witnesses_really_refute_their_named_rivals() -> None:
    assert set(GEN.SEMANTIC_RIVALS) == {
        "always_leftmost",
        "always_rightmost",
        "always_largest",
        "tight_crop_selected",
    }
    assert set(GEN.SEMANTIC_WITNESSES) == {
        "selected_not_leftmost",
        "selected_not_rightmost",
        "selected_not_largest",
        "full_interior_extent",
    }
    for index in range(5):
        grid = GEN.generate(404, index, difficulty="medium")
        expected = GEN.rule_mirror(grid)
        for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
            if GEN.SEMANTIC_WITNESSES[witness_name](grid):
                assert any(GEN.SEMANTIC_RIVALS[name](grid) != expected for name in rival_names)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_schedule_window_and_query_rotation_is_identifiable(band: str) -> None:
    # Five periodic profiles form four demonstrations plus one query.  Every
    # cyclic start and every held-out query must leave enough evidence to defeat
    # left/right/size/content-crop shortcuts.
    for seed in (0, 1, 17):
        grids = [GEN.generate(seed, index, difficulty=band) for index in range(15)]
        for start in range(10):
            window = grids[start:start + 5]
            for held in range(5):
                demos = [_pair(grid) for index, grid in enumerate(window) if index != held]
                query = _pair(window[held])
                assert GEN.lesson_identifiable(demos, query) == [], (
                    band,
                    seed,
                    start,
                    held,
                    [GEN.schedule_profile(seed, start + i, band) for i in range(5)],
                )
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                        band,
                        seed,
                        start,
                        held,
                        name,
                    )
