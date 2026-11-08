from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "7c2a3ec6c4fb"
for path in (REPO / "src", REPO / "shared" / "runtime"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def load_native():
    path = HERE / "native.py"
    spec = importlib.util.spec_from_file_location("_test_native_7c2a3ec6c4fb", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def catalog_program() -> str:
    from arcpuzzles import Catalog

    record = Catalog(REPO).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def hand_grid() -> list[list[int]]:
    grid = [[0 for _ in range(13)] for _ in range(9)]
    repeated_a = [[9, 1, 1], [1, 2, 1], [1, 1, 1]]
    repeated_b = [[1, 1, 9], [1, 2, 1], [1, 1, 1]]
    singleton = [[1, 2, 1], [1, 1, 1], [1, 1, 9]]

    def paint(pattern: list[list[int]], top: int, left: int) -> None:
        for r, row in enumerate(pattern):
            for c, value in enumerate(row):
                grid[top + r][left + c] = value

    paint(repeated_a, 0, 0)
    paint(repeated_a, 0, 5)
    paint(repeated_b, 0, 10)
    paint(repeated_b, 5, 0)
    paint(singleton, 5, 7)
    return grid


def test_canonical_program_is_exact_selected_source() -> None:
    native = load_native()
    assert native.program({"crop_orientation": "as_found"}) == catalog_program()


def test_unique_crop_then_marker_normalization() -> None:
    native = load_native()
    grid = hand_grid()
    expected = [[1, 2, 1], [1, 1, 1], [1, 1, 9]]
    normalized = [[9, 1, 1], [1, 1, 1], [1, 2, 1]]
    assert native.transform(grid, "as_found") == expected
    assert native.transform(grid, "marker_to_top_left") == normalized
    analysis = native.analyze(grid)
    assert analysis["marker_corner"] == "bottom_right"
    assert analysis["marker_color"] == 9


def test_generated_inputs_are_matched_distinct_and_teaching_complete() -> None:
    native = load_native()
    canonical = native.generate(17, {"crop_orientation": "as_found"}, demos=3, queries=4)
    alternative = native.generate(
        17, {"crop_orientation": "marker_to_top_left"}, demos=3, queries=4
    )
    assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
        p["input"] for p in alternative["train"] + alternative["test"]
    ]
    inputs = [p["input"] for p in alternative["train"] + alternative["test"]]
    encoded = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    assert len(encoded) == len(set(encoded)) == 7
    assert alternative["certificate"]["surviving_settings"] == [
        {"crop_orientation": "marker_to_top_left"}
    ]
    assert alternative["certificate"]["ambiguous_rivals"] == []
    assert all(
        pair["output"] == native.transform(pair["input"], "marker_to_top_left")
        for pair in alternative["train"] + alternative["test"]
    )


def test_large_query_is_real_30_by_30_content() -> None:
    native = load_native()
    episode = native.generate(23, {"crop_orientation": "marker_to_top_left"}, 6, 4)
    grid = episode["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(cells) >= 180
    assert min(r for r, _ in cells) == 0 and max(r for r, _ in cells) == 29
    assert min(c for _, c in cells) == 0 and max(c for _, c in cells) == 29


@pytest.mark.parametrize(
    "seed,demos,queries,settings,error",
    [
        (True, 3, 4, {"crop_orientation": "as_found"}, TypeError),
        (0, 2, 4, {"crop_orientation": "as_found"}, ValueError),
        (0, 3, 0, {"crop_orientation": "as_found"}, ValueError),
        (0, 3, 4, {"crop_orientation": "unknown"}, ValueError),
        (0, 3, 4, {"crop_orientation": "as_found", "extra": 1}, ValueError),
    ],
)
def test_invalid_requests_fail_closed(seed, demos, queries, settings, error) -> None:
    native = load_native()
    with pytest.raises(error):
        native.generate(seed, settings, demos, queries)


def test_counterfactual_program_forces_requested_corner() -> None:
    native = load_native()
    source = native.counterfactual_program("top_left")
    assert "(define row-reverse? #f)" in source
    assert "(define col-reverse? #f)" in source
    assert "(= mr (- ph 1))" not in source
    assert "(= mc (- pw 1))" not in source
