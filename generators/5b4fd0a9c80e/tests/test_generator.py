"""Task-local regressions for the stack-crops-by-area generator."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import random
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
spec = importlib.util.spec_from_file_location("generator_5b4fd0a9c80e", SOURCE)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def test_rule_hash_is_pinned_to_current_authority():
    assert gen.RULE_HASH == "d54b19002e00"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_observable_overrides_in_every_band(band):
    options = {"grid_h": 14, "grid_w": 16, "shape_profile": 2}
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo_axis", 1),
        ("grid_h", 9),
        ("grid_h", 15),
        ("grid_w", 11),
        ("grid_w", 17),
        ("shape_profile", -1),
        ("shape_profile", 4),
        ("grid_h", True),
        ("grid_w", 14.0),
        ("shape_profile", "2"),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def _components(grid):
    seen = set()
    result = []
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < len(grid)
                        and 0 <= nc < len(grid[0])
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            result.append(
                {
                    "color": color,
                    "cells": tuple(sorted(cells)),
                    "size": len(cells),
                    "bbox": (min(rows), min(cols), max(rows), max(cols)),
                }
            )
    return result


def _crop(grid, component):
    top, left, bottom, right = component["bbox"]
    return [row[left : right + 1] for row in grid[top : bottom + 1]]


def _oracle(grid, *, order="area", alignment="center", gap=1):
    components = _components(grid)
    if order == "area":
        components.sort(key=lambda item: (item["size"], item["bbox"][0], item["bbox"][1]))
    elif order == "source":
        components.sort(key=lambda item: (item["bbox"][0], item["bbox"][1]))
    elif order == "color_tie":
        components.sort(key=lambda item: (item["size"], item["color"], item["bbox"][0], item["bbox"][1]))
    elif order == "color_only":
        components.sort(key=lambda item: item["color"])
    elif order == "bbox_area":
        components.sort(
            key=lambda item: (
                (item["bbox"][2] - item["bbox"][0] + 1)
                * (item["bbox"][3] - item["bbox"][1] + 1),
                item["bbox"][0],
                item["bbox"][1],
            )
        )
    elif order == "move_largest_last":
        components.sort(key=lambda item: (item["bbox"][0], item["bbox"][1]))
        largest = max(components, key=lambda item: item["size"])
        components = [item for item in components if item is not largest] + [largest]
    else:
        raise ValueError(order)
    crops = [_crop(grid, component) for component in components]
    width = max(len(crop[0]) for crop in crops)
    height = sum(len(crop) for crop in crops) + gap * (len(crops) - 1)
    result = [[0] * width for _ in range(height)]
    top = 0
    for crop in crops:
        if alignment == "left":
            left = 0
        elif alignment == "right_bias":
            left = (width - len(crop[0]) + 1) // 2
        else:
            left = (width - len(crop[0])) // 2
        for row_index, row in enumerate(crop):
            result[top + row_index][left : left + len(row)] = row
        top += len(crop) + gap
    return result


def test_profiles_collectively_refute_a_broad_executable_rival_set():
    expected_rivals = {
        "left_align",
        "right_bias_center",
        "color_tie_break",
        "color_order",
        "source_order",
        "move_largest_last",
        "bbox_area_sort",
        "omit_separator_rows",
    }
    assert set(gen.SEMANTIC_RIVALS) == expected_rivals
    assert gen.LESSON_COMPETITORS == gen.SEMANTIC_RIVALS
    assert gen.WITNESS_RIVALS == {name: [name] for name in expected_rivals}

    expected_signatures = {
        0: (3, 5, 7),
        1: (4, 4, 6),
        2: (4, 6, 7),
        3: (5, 5, 7),
    }
    always_refuted = {
        "left_align",
        "right_bias_center",
        "color_order",
        "source_order",
        "omit_separator_rows",
    }
    for profile in range(4):
        grid = gen.generate(400 + profile, profile, shape_profile=profile)
        intended = _oracle(grid)
        assert tuple(sorted(item["size"] for item in _components(grid))) == expected_signatures[profile]
        assert gen.rule_mirror(grid) == intended
        assert gen.SEMANTIC_RIVALS["left_align"](grid) == _oracle(grid, alignment="left")
        assert gen.SEMANTIC_RIVALS["right_bias_center"](grid) == _oracle(grid, alignment="right_bias")
        assert gen.SEMANTIC_RIVALS["color_tie_break"](grid) == _oracle(grid, order="color_tie")
        assert gen.SEMANTIC_RIVALS["color_order"](grid) == _oracle(grid, order="color_only")
        assert gen.SEMANTIC_RIVALS["source_order"](grid) == _oracle(grid, order="source")
        assert gen.SEMANTIC_RIVALS["move_largest_last"](grid) == _oracle(grid, order="move_largest_last")
        assert gen.SEMANTIC_RIVALS["bbox_area_sort"](grid) == _oracle(grid, order="bbox_area")
        assert gen.SEMANTIC_RIVALS["omit_separator_rows"](grid) == _oracle(grid, gap=0)
        for name in always_refuted:
            assert gen.SEMANTIC_RIVALS[name](grid) != intended, (profile, name)
            assert gen.SEMANTIC_WITNESSES[name](grid), (profile, name)
        if profile in {1, 3}:
            assert gen.SEMANTIC_RIVALS["color_tie_break"](grid) != intended
        if profile in {0, 2}:
            assert gen.SEMANTIC_RIVALS["move_largest_last"](grid) != intended
            assert gen.SEMANTIC_RIVALS["bbox_area_sort"](grid) != intended


def test_tie_profiles_teach_top_then_left_position_order():
    top_priority = gen.generate(701, 1, shape_profile=1)
    tied = sorted(
        [part for part in _components(top_priority) if part["size"] == 4],
        key=lambda part: (part["bbox"][0], part["bbox"][1]),
    )
    assert tied[0]["bbox"][0] < tied[1]["bbox"][0]
    assert tied[0]["bbox"][1] > tied[1]["bbox"][1]

    left_priority = gen.generate(702, 3, shape_profile=3)
    tied = sorted(
        [part for part in _components(left_priority) if part["size"] == 5],
        key=lambda part: (part["bbox"][0], part["bbox"][1]),
    )
    assert tied[0]["bbox"][0] == tied[1]["bbox"][0]
    assert tied[0]["bbox"][1] < tied[1]["bbox"][1]


def test_left_alignment_is_the_strongest_canonical_shortcut():
    from reviewer_support import canonical_pairs, find_root

    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__), labeled_only=True)
    train = [pair for pair in pairs if pair["split"] == "train"]
    assert len(train) == 4
    assert len(pairs) == 5
    assert all(_oracle(pair["input"]) == pair["output"] for pair in pairs)
    assert all(_oracle(pair["input"], alignment="left") == pair["output"] for pair in pairs)
    witness = gen.generate(811, 0, shape_profile=0)
    assert _oracle(witness, alignment="left") != _oracle(witness)


def _pair(grid):
    return {"input": grid, "output": _oracle(grid)}


def test_generated_consecutive_lessons_are_identifiable():
    for band in [None, "easy", "medium", "hard"]:
        for start in range(gen.LESSON_SCHEDULE_PERIOD):
            grids = [gen.generate(1000 + start, start + offset, difficulty=band) for offset in range(4)]
            demos = [_pair(grid) for grid in grids[: gen.EXAMPLES_NEEDED]]
            query = _pair(grids[gen.EXAMPLES_NEEDED])
            assert gen.lesson_identifiable(demos, query) == []


def test_lesson_identifiable_rejects_wrong_labels_and_surviving_canonical_shortcut():
    grid = gen.generate(2000, 0)
    wrong = _pair(grid)
    wrong["output"] = [[9]]
    reasons = gen.lesson_identifiable([wrong, _pair(gen.generate(2000, 1)), _pair(gen.generate(2000, 2))], _pair(gen.generate(2000, 3)))
    assert any("demo 0 output" in reason for reason in reasons)

    from reviewer_support import canonical_pairs, find_root

    train = [
        pair
        for pair in canonical_pairs(gen.TASK_ID, root=find_root(__file__), labeled_only=True)
        if pair["split"] == "train"
    ]
    reasons = gen.lesson_identifiable(train, {"input": gen.generate(2001, 0)})
    assert any("left_align" in reason and "survives" in reason for reason in reasons)


def test_canonical_pairs_are_owned_by_validator_and_both_oracles():
    from reviewer_support import canonical_pairs, find_root

    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__), labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert _oracle(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_all_declared_joint_overrides_are_exact_constructive_and_semantic():
    for band in [None, "easy", "medium", "hard"]:
        for height in range(10, 15):
            for width in range(12, 17):
                for profile in range(4):
                    options = {"grid_h": height, "grid_w": width, "shape_profile": profile}
                    grid = gen.generate(3000 + profile, height * 100 + width, difficulty=band, **options)
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == options
                    assert gen.rule_mirror(grid) == _oracle(grid)


def test_default_schedule_is_deterministic_diverse_and_refutes_every_rival():
    for band in [None, "easy", "medium", "hard"]:
        grids = [gen.generate(4000 + index, index, difficulty=band) for index in range(64)]
        assert all(grid == gen.generate(4000 + index, index, difficulty=band) for index, grid in enumerate(grids))
        assert all(gen.self_check(grid) == [] for grid in grids)
        assert len({tuple(tuple(row) for row in grid) for grid in grids}) >= 60
        assert {gen.observe_overrides(grid)["shape_profile"] for grid in grids} == {0, 1, 2, 3}
        for start in range(len(grids) - gen.EXAMPLES_NEEDED + 1):
            window = grids[start : start + gen.EXAMPLES_NEEDED]
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(grid) != _oracle(grid) for grid in window), (band, start, name)


def test_generate_does_not_touch_module_random_state():
    random.seed(918273)
    before = random.getstate()
    gen.generate(55, 7, difficulty="hard")
    assert random.getstate() == before


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(10)], [[10] * 12 for _ in range(10)]],
)
def test_self_check_is_diagnostic_on_malformed_values(grid):
    assert gen.self_check(grid)


def test_self_check_rejects_targeted_destructive_mutations():
    grid = gen.generate(5000, 0, shape_profile=0)

    blank = [[0 for _ in row] for row in grid]
    assert gen.self_check(blank)

    too_short = grid[:-2]
    assert gen.self_check(too_short)

    duplicate_color = copy.deepcopy(grid)
    parts = _components(duplicate_color)
    for row, col in parts[0]["cells"]:
        duplicate_color[row][col] = parts[1]["color"]
    assert gen.self_check(duplicate_color)

    undersized = copy.deepcopy(grid)
    tie = next(part for part in _components(undersized) if part["size"] == 3)
    row, col = tie["cells"][0]
    undersized[row][col] = 0
    assert gen.self_check(undersized)

    extra = copy.deepcopy(grid)
    occupied = {(row, col) for part in _components(extra) for row, col in part["cells"]}
    colors = {value for row in extra for value in row if value}
    extra_color = next(color for color in range(1, 10) if color not in colors)
    spot = next(
        (row, col)
        for row in range(len(extra))
        for col in range(len(extra[0]))
        if (row, col) not in occupied
        and all((row + dr, col + dc) not in occupied for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
    )
    extra[spot[0]][spot[1]] = extra_color
    assert gen.self_check(extra)


def test_unknown_difficulty_is_rejected():
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="expert")


def test_difficulty_bands_select_distinct_declared_schedule_profiles():
    bands = ("easy", "medium", "hard")
    grids = {band: gen.generate(6000, 0, difficulty=band) for band in bands}
    assert len({tuple(tuple(row) for row in grid) for grid in grids.values()}) == len(bands)
    for band, grid in grids.items():
        observed = gen.observe_overrides(grid)["shape_profile"]
        assert gen.schedule_profile(6000, 0, band) == gen.SCHEDULE_PROFILES[observed]


def test_retained_left_alignment_counterexample_replays_exactly():
    path = HOME / "counterexamples" / "left-align-vs-center" / "reproducer.json"
    row = json.loads(path.read_text())
    request = row["generation"]
    grid = gen.generate(
        request["seed"],
        request["sample_index"],
        difficulty=request["difficulty"],
        **request["overrides"],
    )
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == row["generator_sha256"]
    assert grid == row["input"]
    assert gen.rule_mirror(grid) == row["racket_output"] == row["intended_python_mirror"]
    assert gen.SEMANTIC_RIVALS["left_align"](grid) == row["left_align_rival"]
    assert row["left_align_rival"] != row["racket_output"]
