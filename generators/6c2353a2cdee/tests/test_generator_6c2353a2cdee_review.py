from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

TASK_DIR = Path(__file__).resolve().parents[1]
REPO = TASK_DIR.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_6c2353a2cdee", TASK_DIR / "generator.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PANEL_STARTS = (0, 6, 12)


def _canonical_record() -> dict:
    source = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical record not found")


def _panel_cells(grid, panel_index: int) -> set[tuple[int, int]]:
    left = PANEL_STARTS[panel_index]
    return {
        (row, col)
        for row in range(5)
        for col in range(5)
        if grid[row][left + col] != 0
    }


def _component_count(cells: set[tuple[int, int]]) -> int:
    unseen = set(cells)
    count = 0
    while unseen:
        count += 1
        start = min(unseen)
        unseen.remove(start)
        stack = [start]
        while stack:
            row, col = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (row + dr, col + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    stack.append(nxt)
    return count


def _codes(grid) -> tuple[int, int, int]:
    result = []
    for left in PANEL_STARTS:
        nonzero = [value for value in grid[6][left : left + 5] if value != 0]
        assert len(nonzero) == 1
        result.append(nonzero[0])
    return tuple(result)


def test_selected_rule_hash_is_pinned() -> None:
    assert gen.RULE_HASH == "9fc3fd333ca6"


def test_canonical_examples_pass_task_self_check() -> None:
    record = _canonical_record()
    for split in ("train", "test"):
        for index, pair in enumerate(record[split]):
            assert gen.self_check(pair["input"]) == [], (split, index)


def test_python_rule_mirror_matches_every_canonical_output() -> None:
    record = _canonical_record()
    for split in ("train", "test"):
        for index, pair in enumerate(record[split]):
            assert gen.rule_mirror(pair["input"]) == pair["output"], (split, index)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_draws_are_connected_compact_canonical_templates(difficulty) -> None:
    for sample_index in range(16):
        grid = gen.generate(137, sample_index, difficulty=difficulty)
        assert gen.self_check(grid) == []
        assert grid[5] == [0] * 17
        assert grid[6][5] == grid[6][11] == 0
        assert set(_codes(grid)) <= {1, 2, 3, 4}
        assert len(set(_codes(grid))) == 3
        for panel_index in range(3):
            cells = _panel_cells(grid, panel_index)
            assert 5 <= len(cells) <= 8
            assert _component_count(cells) == 1
            assert {row for row, _ in cells} == {1, 2, 3}


def test_self_check_rejects_extra_code_cell() -> None:
    grid = gen.generate(19, 0)
    grid[6][0] = 4 if grid[6][0] == 0 else 3
    assert any("exactly one code" in error for error in gen.self_check(grid))


def test_self_check_rejects_disconnected_panel() -> None:
    grid = gen.generate(19, 0)
    left = PANEL_STARTS[0]
    color = next(grid[row][left + col] for row in range(5) for col in range(5) if grid[row][left + col])
    for row in range(5):
        for col in range(5):
            grid[row][left + col] = 0
    grid[1][left + 1] = color
    grid[3][left + 3] = color
    assert any("connected" in error for error in gen.self_check(grid))


def test_unknown_override_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(5, 0, typo_axis=3)


@pytest.mark.parametrize("axis,panel_index", [("panel0_cells", 0), ("panel1_cells", 1), ("panel2_cells", 2)])
@pytest.mark.parametrize("value", [5, 8])
def test_panel_cell_overrides_are_exact(axis: str, panel_index: int, value: int) -> None:
    grid = gen.generate(31, 2, **{axis: value})
    assert len(_panel_cells(grid, panel_index)) == value
    assert gen.self_check(grid, meta={"overrides": {axis: value}}) == []


def test_four_example_schedule_covers_every_transform_code() -> None:
    for start in range(8):
        seen = set()
        omitted = []
        for sample_index in range(start, start + 4):
            grid = gen.generate(101, sample_index)
            codes = set(_codes(grid))
            seen.update(codes)
            omitted.append(({1, 2, 3, 4} - codes).pop())
        assert seen == {1, 2, 3, 4}
        assert set(omitted) == {1, 2, 3, 4}


def test_each_ordinary_draw_exposes_count_palette_and_named_rivals() -> None:
    for sample_index in range(20):
        grid = gen.generate(211, sample_index)
        output = gen.rule_mirror(grid)
        assert {2, 4, 8} <= {value for row in output for value in row}
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert rival(grid) != output, (sample_index, name)


def test_generated_four_demo_lesson_is_identifiable() -> None:
    demos = []
    for sample_index in range(4):
        grid = gen.generate(307, sample_index)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(307, 4)
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []


def test_observe_overrides_recovers_all_exact_axes() -> None:
    grid = gen.generate(401, 3, panel0_cells=5, panel1_cells=6, panel2_cells=8)
    assert gen.observe_overrides(grid) == {
        "panel0_cells": 5,
        "panel1_cells": 6,
        "panel2_cells": 8,
    }


def test_difficulty_bands_change_default_template_sizes() -> None:
    for sample_index in range(12):
        easy = gen.generate(509, sample_index, difficulty="easy")
        hard = gen.generate(509, sample_index, difficulty="hard")
        assert easy != hard
        assert all(len(_panel_cells(easy, i)) <= 6 for i in range(3))
        assert all(len(_panel_cells(hard, i)) >= 7 for i in range(3))
