"""Behavioral checks for the separate native component-priority family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
ADAPTER_PATH = HOME / "workspace/parametric/adapter.py"
SCAN = {"corner_priority": "scan"}
LARGEST = {"corner_priority": "largest_component"}
DEMO = [[int(x) for x in row] for row in
        ("000333", "110303", "000000", "010440", "110040", "100000")]


def adapter():
    assert ADAPTER_PATH.is_file(), "native corner-priority adapter is missing"
    spec = importlib.util.spec_from_file_location("test_corner_priority_adapter", ADAPTER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def block(output, row, col, scale):
    return [r[col * scale:(col + 1) * scale]
            for r in output[row * scale:(row + 1) * scale]]


def test_largest_neighbor_uses_connected_component_not_whole_color_frequency():
    module = adapter()
    scan = module.transform(DEMO, SCAN)
    largest = module.transform(DEMO, LARGEST)
    assert block(scan, 2, 2, 3) == [[2, 0, 0], [0, 2, 0], [0, 0, 2]]
    assert block(largest, 2, 2, 3) == [[0, 0, 2], [0, 2, 0], [2, 0, 0]]
    # Color 1 has six cells but its separate components have areas two and four.
    # The area-five color-3 component wins at NE. Its tied NW/NE contacts at
    # (2,4) must keep the first direction.
    assert block(largest, 2, 4, 3) == [[2, 0, 0], [0, 2, 0], [0, 0, 2]]


@pytest.mark.parametrize("settings", [SCAN, LARGEST])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_independent_counts_unique_queries_matched_inputs_and_output_bounds(settings, demos):
    module = adapter()
    lesson = module.generate(17, settings, demos, 4)
    assert len(lesson["train"]) == demos and len(lesson["test"]) == 4
    pairs = lesson["train"] + lesson["test"]
    assert len({json.dumps(p["input"]) for p in pairs}) == demos + 4
    assert lesson["program_solution"] == module.program(settings)
    assert all(p["output"] == module.transform(p["input"], settings) for p in pairs)
    assert all(1 <= len(p["output"]) <= 30 and 1 <= len(p["output"][0]) <= 30
               for p in pairs)
    assert (len(lesson["test"][-1]["output"]), len(lesson["test"][-1]["output"][0])) == (30, 30)
    other = module.generate(17, LARGEST if settings == SCAN else SCAN, demos, 4)
    assert [p["input"] for p in pairs] == [p["input"] for p in other["train"] + other["test"]]
    one = module.generate(17, settings, demos, 1)
    assert one["train"] == lesson["train"] and one["test"][0] == lesson["test"][0]
    assert module.teaching_check(lesson)["ok"] is True


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (True, 4), (3, 0), (3, 5), (3, True)])
def test_invalid_count_requests_fail_before_generation(demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(0, SCAN, demos, queries)


@pytest.mark.parametrize("settings", [{}, {"corner_priority": True}, {"corner_priority": "smallest"},
                                     {"corner_priority": "scan", "extra": 1}])
def test_undeclared_settings_fail_closed(settings):
    with pytest.raises(ValueError):
        adapter().program(settings)


def test_default_program_is_exact_canonical_resource():
    module = adapter()
    assert module.program(SCAN) == (ADAPTER_PATH.parent / "canonical.rkt").read_text()


def test_teaching_check_rejects_a_lesson_without_distinguishing_demonstrations():
    module = adapter()
    grid = [[1, 1, 0, 0], [1, 0, 0, 0], [0, 0, 3, 0], [0, 0, 0, 0]]
    lesson = {"train": [{"input": grid, "output": module.transform(grid, SCAN)}],
              "test": [{"input": DEMO, "output": module.transform(DEMO, SCAN)}],
              "program_solution": module.program(SCAN)}
    assert module.teaching_check(lesson)["ok"] is False


def test_large_input_keeps_substantive_regions_within_the_output_limit():
    module = adapter()
    lesson = module.generate(17, LARGEST, 2, 4)
    grid = lesson["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (15, 15)
    assert 100 <= sum(v != 0 for row in grid for v in row) <= 150
    assert len(lesson["test"][3]["output"]) == 30
    assert any(grid[r][c] for r in (0, 14) for c in range(15))


def test_output_overflow_grid_is_rejected_before_allocation():
    module = adapter()
    grid = [[1] * 15 for _ in range(15)]
    grid[0][0], grid[0][1] = 3, 4
    with pytest.raises(ValueError):
        module.transform(grid, LARGEST)
