"""Semantic regressions for generator 48732ebd41f9.

The oracle below is intentionally independent of generator internals.  It
reimplements the public Racket primitive's row-band scan: among maximal
horizontal zero runs with height >= 2, choose the first one with greatest area.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import os
import json
from pathlib import Path
import random

import pytest


TASK_ID = "48732ebd41f9"
ROOT = Path(__file__).resolve().parents[3]


def _load_generator():
    candidate = os.environ.get("GENERATOR_UNDER_TEST")
    path = Path(candidate) if candidate else ROOT / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_row() -> dict:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _pairs() -> list[dict]:
    row = _canonical_row()
    return [pair for split in ("train", "test") for pair in row[split]]


def _zero_rectangles(grid: list[list[int]]) -> list[tuple[int, int, int, int, int]]:
    height = len(grid)
    width = len(grid[0])
    rectangles: list[tuple[int, int, int, int, int]] = []
    for top in range(height):
        valid = [True] * width
        for bottom in range(top, height):
            for col in range(width):
                if grid[bottom][col] != 0:
                    valid[col] = False
            rect_h = bottom - top + 1
            if rect_h < 2:
                continue
            start = None
            for col in range(width + 1):
                if col < width and valid[col]:
                    if start is None:
                        start = col
                elif start is not None:
                    rectangles.append(
                        (top, start, bottom, col - 1, rect_h * (col - start))
                    )
                    start = None
    return rectangles


def _largest_rect(grid: list[list[int]]) -> tuple[int, int, int, int, int]:
    rectangles = _zero_rectangles(grid)
    assert rectangles, "test oracle expected at least one height>=2 zero rectangle"
    max_area = max(rect[4] for rect in rectangles)
    return next(rect for rect in rectangles if rect[4] == max_area)


def _max_area_rectangles(grid: list[list[int]]) -> list[tuple[int, int, int, int, int]]:
    rectangles = _zero_rectangles(grid)
    if not rectangles:
        return []
    max_area = max(rect[4] for rect in rectangles)
    return [rect for rect in rectangles if rect[4] == max_area]


def _rule_output(grid: list[list[int]]) -> list[list[int]]:
    top, left, bottom, right, _ = _largest_rect(grid)
    output = deepcopy(grid)
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            if output[row][col] == 0:
                output[row][col] = 6
    return output


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_pin_canonical_ownership_and_independent_oracle() -> None:
    row = _canonical_row()
    expected_hash = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == expected_hash == "9d5297512997"

    for pair in _pairs():
        original = deepcopy(pair["input"])
        assert len(_max_area_rectangles(original)) == 1
        assert gen.self_check(original) == []
        assert _rule_output(original) == pair["output"]
        assert original == pair["input"]


def test_selected_racket_authorities_are_exactly_synchronized() -> None:
    row = _canonical_row()
    base = json.loads(
        (ROOT / "shared/data/base/solutions/training/3eda0437__48732ebd41f9.json")
        .read_text(encoding="utf-8")
    )
    target = base["racket_target"]
    assert target["target_code"] == row["program_solution"]
    assert target["raw_code"] != target["target_code"]


def test_declared_four_slot_schedule_covers_every_profile() -> None:
    expected = (
        "canonical_core",
        "interior_rivals",
        "edge_rivals",
        "accent_rivals",
    )
    assert tuple(gen.SCHEDULE_PROFILES) == expected
    assert gen.EXAMPLES_NEEDED == 4
    for start in range(12):
        observed = {
            gen.schedule_profile(123, start + offset, difficulty="medium")
            for offset in range(4)
        }
        assert observed == set(expected)


def test_default_draws_are_lawful_diverse_and_not_full_height_shortcuts() -> None:
    target_shapes: set[tuple[int, int]] = set()
    non_full_height = 0
    total = 0
    for band in ("easy", "medium", "hard"):
        for index in range(64):
            grid = gen.generate(4000 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(4000 + index, index, difficulty=band)
            maxima = _max_area_rectangles(grid)
            assert len(maxima) == 1
            target = maxima[0]
            target_h = target[2] - target[0] + 1
            target_w = target[3] - target[1] + 1
            target_shapes.add((target_h, target_w))
            non_full_height += target_h < len(grid)
            total += 1
            output = _rule_output(grid)
            assert output != grid
            assert sum(
                before != after
                for row_before, row_after in zip(grid, output)
                for before, after in zip(row_before, row_after)
            ) == target[4]
    assert len(target_shapes) >= 4
    assert non_full_height >= int(total * 0.75)


def test_every_band_has_exact_canonical_profile_and_three_color_support() -> None:
    canonical_profiles = {_profile(pair["input"]) for pair in _pairs()}
    assert canonical_profiles == {
        (2, 20, 2),
        (3, 30, 3),
        (4, 20, 2),
        (4, 24, 2),
    }
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(7000 + index, index, difficulty=band) for index in range(20)]
        assert any(_profile(grid) in canonical_profiles for grid in grids)
        assert any(len({value for row in grid for value in row}) == 3 for grid in grids)


def test_exact_overrides_are_honored_and_observable_in_every_band() -> None:
    requested = {
        "grid_h": 8,
        "grid_w": 30,
        "fg_color": 9,
        "target_h": 4,
        "target_w": 7,
        "target_location": "interior",
        "palette_mode": "accent",
    }
    for band in (None, "easy", "medium", "hard"):
        grid = gen.generate(17, 9, difficulty=band, **requested)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == requested
        assert grid == gen.generate(17, 9, difficulty=band, **requested)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"grid_h": True},
        {"grid_h": 1},
        {"grid_w": 13},
        {"fg_color": 6},
        {"target_h": 1},
        {"target_w": 2},
        {"target_w": 9},
        {"target_location": "random"},
        {"palette_mode": "three"},
        {"grid_h": 2, "target_h": 3},
        {"grid_h": 2, "target_h": 2, "target_location": "interior"},
    ],
)
def test_invalid_unknown_and_incompatible_overrides_are_rejected(overrides) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_semantic_witnesses_have_real_rival_disagreements() -> None:
    grids = [gen.generate(91, index, difficulty="medium") for index in range(4)]
    for name, witness in gen.SEMANTIC_WITNESSES.items():
        matching = [grid for grid in grids if witness(grid)]
        assert matching, name
        for rival_name in gen.WITNESS_RIVALS[name]:
            assert any(
                gen.SEMANTIC_RIVALS[rival_name](grid) != _rule_output(grid)
                for grid in matching
            ), (name, rival_name)
    assert set(gen.CANONICAL_SHORTCUTS) <= set(gen.SEMANTIC_RIVALS)
    assert set(gen.LESSON_COMPETITORS) <= set(gen.SEMANTIC_RIVALS)


def test_validator_rejects_malformed_ambiguous_and_output_colored_inputs() -> None:
    assert gen.self_check(None)
    assert gen.self_check([])
    assert gen.self_check([[0], [0, 1]])
    assert gen.self_check([[1] * 14 for _ in range(4)])

    minimal = [[1] * 14 for _ in range(4)]
    for row in range(2):
        for col in range(2):
            minimal[row][col] = 0
    assert gen.self_check(minimal), "canonical evidence starts at width-3 targets"

    tie = [[1] * 14 for _ in range(4)]
    for top, left in ((0, 1), (2, 8)):
        for row in range(top, top + 2):
            for col in range(left, left + 3):
                tie[row][col] = 0
    assert len(_max_area_rectangles(tie)) == 2
    assert gen.self_check(tie)

    output_colored = gen.generate(3, 2)
    output_colored[0][0] = 6
    assert gen.self_check(output_colored)


def test_generation_is_fresh_deterministic_and_global_rng_pure() -> None:
    random.seed(48732)
    state = random.getstate()
    first = gen.generate(37, 11, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(37, 11, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
    assert gen.generate(37, 11, difficulty="hard") == second


def test_default_training_draws_vary_irrelevant_foreground_identity() -> None:
    colors = {
        gen.observe_overrides(gen.generate(12000 + index, index, difficulty="medium"))["fg_color"]
        for index in range(64)
    }
    assert 1 in colors
    assert len(colors) >= 4, colors


@pytest.mark.parametrize("grid_h", [2, 3])
def test_short_height_pin_adapts_unpinned_target_before_typed_draw(grid_h: int) -> None:
    grid = gen.generate(
        2,
        1,  # interior_rivals profile before adaptation
        difficulty="easy",
        grid_h=grid_h,
        fg_color=5,
    )
    observed = gen.observe_overrides(grid)
    assert observed["grid_h"] == grid_h
    assert observed["fg_color"] == 5
    assert observed["target_h"] == 2
    assert observed["target_location"] == "edge"


def test_short_interior_canvas_incompatibility_is_declared_for_checker() -> None:
    expected = {"grid_h": (2, 3), "target_location": "interior"}
    assert expected in gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS
    for grid_h in expected["grid_h"]:
        with pytest.raises(ValueError) as captured:
            gen.generate(
                0,
                0,
                difficulty="medium",
                grid_h=grid_h,
                target_location="interior",
            )
        assert set(captured.value.incompatible_axes) >= {
            "grid_h",
            "target_location",
        }


def test_canonical_shortcut_registry_only_contains_canonical_fitting_rules():
    pairs = _pairs()
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
