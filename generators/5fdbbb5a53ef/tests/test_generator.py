"""Portable regressions for the typed shape/color relation-matrix sampler."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "5fdbbb5a53ef"
HERE = Path(__file__).resolve()
TASK_HOME = HERE.parent.parent


def _load_generator():
    source = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("typed_relation_generator", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _norm(cells):
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return frozenset((row - min_row, col - min_col) for row, col in cells)


def _rotate(cells):
    return [(col, -row) for row, col in cells]


def _rotations(shape):
    current = list(shape)
    result = set()
    for _ in range(4):
        result.add(_norm(current))
        current = _rotate(current)
    return result


def _frames(grid):
    height, width = len(grid), len(grid[0])
    frames = []
    for top in range(height - 4):
        for left in range(width - 4):
            border = [
                grid[row][col]
                for row in range(top, top + 5)
                for col in range(left, left + 5)
                if row in (top, top + 4) or col in (left, left + 4)
            ]
            if border != [9] * 16:
                continue
            cells = []
            colors = set()
            for row in range(3):
                for col in range(3):
                    value = grid[top + 1 + row][left + 1 + col]
                    if value:
                        cells.append((row, col))
                        colors.add(value)
            if cells:
                frames.append(
                    {
                        "top": top,
                        "left": left,
                        "shape": _norm(cells),
                        "color": next(iter(colors)),
                        "colors": colors,
                    }
                )
    return frames


def _layout(grid):
    frames = _frames(grid)
    top_band = min(frame["top"] for frame in frames)
    left_band = min(frame["left"] for frame in frames)
    tops = sorted(
        (frame for frame in frames if frame["top"] == top_band),
        key=lambda frame: frame["left"],
    )
    lefts = sorted(
        (
            frame
            for frame in frames
            if frame["left"] == left_band and frame["top"] != top_band
        ),
        key=lambda frame: frame["top"],
    )
    return {
        "top_count": len(tops),
        "left_count": len(lefts),
        "row_offset": top_band,
        "col_offset": left_band,
    }, tops, lefts


def _oracle(grid):
    _, tops, lefts = _layout(grid)
    output = []
    for left in lefts:
        row = []
        for top in tops:
            same_shape = top["shape"] in _rotations(left["shape"])
            same_color = top["color"] == left["color"]
            row.append(8 if same_shape and same_color else 6 if same_shape else 3 if same_color else 0)
        output.append(row)
    return output


def _palette_roles(input_grid, output_grid):
    before = {value for row in input_grid for value in row if value}
    after = {value for row in output_grid for value in row if value}
    return (len(before & after), len(after - before), len(before - after))


@pytest.fixture(scope="module")
def canonical():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def test_rule_authority_is_pinned() -> None:
    assert gen.RULE_HASH == "b12aeca2f818"


def test_canonical_inputs_are_accepted_and_oracle_matches(canonical) -> None:
    assert len(canonical) == 5
    for pair in canonical:
        assert _oracle(pair["input"]) == pair["output"]
        assert gen.self_check(deepcopy(pair["input"])) == []
        assert hasattr(gen, "strict_canonical_like")
        assert gen.strict_canonical_like(deepcopy(pair["input"])) == []


def test_easy_2x2_relations_are_not_a_fixed_position_template() -> None:
    selected = []
    for sample_index in range(512):
        grid = gen.generate(0, sample_index, difficulty="easy")
        layout, _, _ = _layout(grid)
        if layout["top_count"] == layout["left_count"] == 2:
            selected.append((grid, _oracle(grid)))
            if len(selected) == 64:
                break

    assert len(selected) == 64
    assert len({json.dumps(grid) for grid, _ in selected}) == 64
    # Row and column order must both vary; the four 2x2 permutations should occur.
    assert len({json.dumps(output) for _, output in selected}) == 4


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"top_count": 4, "left_count": 3, "row_offset": 2, "col_offset": 1},
        {"top_count": 3, "left_count": 2, "row_offset": 0, "col_offset": 2},
    ],
)
def test_exact_layout_overrides_are_observable_in_every_band(band, requested) -> None:
    grid = gen.generate(193, 17, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert _layout(grid)[0] == requested
    assert hasattr(gen, "observe_overrides")
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "override",
    [
        {"typo_axis": 1},
        {"top_count": 1},
        {"top_count": 5},
        {"left_count": 1},
        {"left_count": 4},
        {"row_offset": -1},
        {"row_offset": 3},
        {"col_offset": -1},
        {"col_offset": 3},
        {"top_count": 4, "col_offset": 2},
        {"top_count": True},
        {"left_count": 2.0},
        {"row_offset": "1"},
    ],
)
def test_invalid_or_incompatible_overrides_are_rejected(override) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **override)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_invalid_sample_index_scalars_are_rejected(sample_index) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, sample_index, difficulty="easy")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_first_twenty_draws_include_a_canonical_size_and_palette_profile(band) -> None:
    grids = [gen.generate(8801, index, difficulty=band) for index in range(20)]
    assert any(
        len(grid) == 25
        and len(grid[0]) == 25
        and len({value for row in grid for value in row}) in {5, 6}
        and _layout(grid)[0]
        == {"top_count": 3, "left_count": 3, "row_offset": 2, "col_offset": 2}
        for grid in grids
    )


def test_schedule_is_seed_sensitive_without_a_short_fixed_period() -> None:
    assert getattr(gen, "LESSON_SCHEDULE_PERIOD", None) is None
    sequences = []
    for seed in (0, 1):
        sequence = [gen.schedule_profile(seed, index, "easy") for index in range(128)]
        assert set(sequence) == {"canonical_support", "broad"}
        assert all(
            any(sequence[index] != sequence[index + period] for index in range(128 - period))
            for period in range(1, 17)
        )
        sequences.append(sequence)
    assert sequences[0] != sequences[1]


def test_canonical_support_schedule_overlaps_canonical_palette_roles(canonical) -> None:
    canonical_roles = {
        _palette_roles(pair["input"], pair["output"]) for pair in canonical
    }
    generated_roles = set()
    for band in ("easy", "medium", "hard"):
        for sample_index in range(64):
            if gen.schedule_profile(8801, sample_index, band) != "canonical_support":
                continue
            grid = gen.generate(8801, sample_index, difficulty=band)
            generated_roles.add(_palette_roles(grid, _oracle(grid)))
    assert generated_roles & canonical_roles


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_inputs_teach_shape_color_and_joint_matches(band) -> None:
    for index in range(40):
        grid = gen.generate(700 + index, index, difficulty=band)
        values = {value for row in _oracle(grid) for value in row}
        assert {3, 6, 8} <= values
        assert gen.self_check(grid) == []


def test_fixed_position_competitor_and_lesson_hook_are_executable() -> None:
    assert hasattr(gen, "LESSON_COMPETITORS")
    assert "fixed_position_template" in gen.LESSON_COMPETITORS
    assert hasattr(gen, "lesson_identifiable")
    competitor = gen.LESSON_COMPETITORS["fixed_position_template"]
    fixed = [[8, 3], [6, 0]]
    fixed_demos = []
    changed_query = None

    for sample_index in range(1024):
        grid = gen.generate(991, sample_index, difficulty="easy", top_count=2, left_count=2)
        output = _oracle(grid)
        assert competitor(deepcopy(grid)) == fixed
        pair = {"input": grid, "output": output}
        if output == fixed and len(fixed_demos) < 3:
            fixed_demos.append(pair)
        elif output != fixed and changed_query is None:
            changed_query = pair
        if len(fixed_demos) == 3 and changed_query is not None:
            break

    assert len(fixed_demos) == 3
    assert changed_query is not None
    reasons = gen.lesson_identifiable(fixed_demos, changed_query)
    assert any("fixed_position_template" in reason for reason in reasons)


@pytest.mark.parametrize(
    "bad_grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(8)]],
)
def test_malformed_inputs_are_rejected_without_exceptions(bad_grid) -> None:
    assert gen.self_check(bad_grid)


def test_replay_is_deterministic_and_call_order_independent() -> None:
    expected = gen.generate(1201, 17, difficulty="hard")
    for index in range(100):
        gen.generate(index, index * 7, difficulty="easy")
    assert gen.generate(1201, 17, difficulty="hard") == expected
