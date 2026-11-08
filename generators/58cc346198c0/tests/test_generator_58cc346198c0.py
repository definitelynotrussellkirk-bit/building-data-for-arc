"""Focused regression tests for generator 58cc346198c0."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))
SPEC = importlib.util.spec_from_file_location(
    "review_58cc346198c0", REPO / "generators" / "58cc346198c0" / "generator.py"
)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def canonical_pairs(task_id: str) -> list[dict]:
    for line in (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["task_id"] == task_id:
            return [*row["train"], *row["test"]]
    raise AssertionError(f"missing canonical task {task_id}")


def test_all_canonical_inputs_are_accepted() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    assert [gen.self_check(pair["input"]) for pair in pairs] == [[], [], [], []]


def test_unknown_override_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override axis"):
        gen.generate(0, 0, difficulty="easy", misspelled_axis=1)


@pytest.mark.parametrize("family", ["l_shape", "zigzag", "irregular", "mixed"])
@pytest.mark.parametrize("palette_pattern", ["distinct", "repeat_pair"])
def test_boundary_overrides_are_exact_and_observable(
    family: str, palette_pattern: str
) -> None:
    grid = gen.generate(
        41,
        7,
        difficulty="hard",
        grid_h=7,
        grid_w=9,
        object_count=4,
        shape_family=family,
        palette_pattern=palette_pattern,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": 7,
        "grid_w": 9,
        "object_count": 4,
        "shape_family": family,
        "palette_pattern": palette_pattern,
    }


def test_repeat_pair_palette_refutes_grouping_objects_by_color() -> None:
    grid = gen.generate(
        73,
        9,
        difficulty="hard",
        grid_h=14,
        grid_w=15,
        object_count=4,
        shape_family="mixed",
        palette_pattern="repeat_pair",
    )
    components = gen._components(grid)
    counts = Counter(color for color, _ in components)

    assert sorted(counts.values()) == [1, 1, 2]
    assert gen._per_color_bbox(grid) != gen._expected_output(grid)


def test_irregular_family_is_not_a_small_fixed_template_bank() -> None:
    shapes = set()
    sizes = set()
    for sample_index in range(80):
        grid = gen.generate(
            211,
            sample_index,
            difficulty="hard",
            grid_h=14,
            grid_w=15,
            object_count=2,
            shape_family="irregular",
            palette_pattern="distinct",
        )
        for _, cells in gen._components(grid):
            shape = gen._normalize(cells)
            shapes.add(shape)
            sizes.add(len(shape))

    assert max(sizes) >= 8
    assert len(shapes) >= 24


def test_default_lessons_refute_shape_specific_shortcuts() -> None:
    # Any two consecutive positions contain mixed shapes and repeated colors.
    for start in range(len(gen.SCHEDULE_PROFILES)):
        demos = []
        for offset in range(gen.EXAMPLES_NEEDED):
            grid = gen.generate(123, start + offset, difficulty="medium")
            demos.append({"input": grid, "output": gen._expected_output(grid)})
        query_grid = gen.generate(123, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        query = {"input": query_grid, "output": gen._expected_output(query_grid)}
        assert any(
            gen._per_color_bbox(demo["input"]) != demo["output"] for demo in demos
        )
        assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_targeted_impostors() -> None:
    line_objects = [[0] * 9 for _ in range(7)]
    line_objects[1][1:5] = [2, 2, 2, 2]
    line_objects[5][4:8] = [3, 3, 3, 3]
    assert any("bbox" in error for error in gen.self_check(line_objects))

    full_rectangles = [[0] * 9 for _ in range(7)]
    for row in (1, 2):
        for col in (1, 2, 3):
            full_rectangles[row][col] = 2
    for row in (4, 5):
        for col in (5, 6, 7):
            full_rectangles[row][col] = 3
    assert any("fills its bbox" in error for error in gen.self_check(full_rectangles))

    touching_colors = [[0] * 9 for _ in range(7)]
    touching_colors[1][1:4] = [2, 2, 2]
    touching_colors[2][1] = 2
    touching_colors[2][2:5] = [3, 3, 3]
    touching_colors[3][4] = 3
    assert any("touch" in error for error in gen.self_check(touching_colors))

    repeated_color = gen.generate(
        9,
        0,
        difficulty="easy",
        object_count=4,
        palette_pattern="distinct",
    )
    components = gen._components(repeated_color)
    assert len(components) == 4
    first_color, _ = components[0]
    second_color, second_cells = components[1]
    assert first_color != second_color
    for row, col in second_cells:
        repeated_color[row][col] = first_color
    assert gen.self_check(repeated_color) == []

    third_color, _ = gen._components(repeated_color)[2]
    fourth_color, fourth_cells = gen._components(repeated_color)[3]
    assert third_color != fourth_color
    for row, col in fourth_cells:
        repeated_color[row][col] = third_color
    assert any("exactly one repeated pair" in error for error in gen.self_check(repeated_color))


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(9917)
    state = random.getstate()
    first = gen.generate(72, 5, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(72, 5, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second, strict=True))
    changed = copy.deepcopy(first)
    changed[0][0] = 9 if changed[0][0] != 9 else 8
    assert second != changed
