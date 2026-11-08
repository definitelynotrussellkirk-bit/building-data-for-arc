from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
TASK_ID = "95f82d34a755"
for path in (REPO / "src", REPO / "shared" / "runtime"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))


def load_native():
    path = HERE / "native.py"
    spec = importlib.util.spec_from_file_location("_test_native_95f82d34a755", path)
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
    return [
        [0, 8, 7, 4, 2],
        [3, 5, 0, 6, 0],
        [4, 0, 1, 0, 2],
        [2, 3, 0, 8, 0],
        [7, 0, 4, 0, 9],
    ]


def test_canonical_program_is_exact_selected_source() -> None:
    native = load_native()
    assert native.program({"match_alignment": "in_place"}) == catalog_program()


def test_equality_field_then_first_match_alignment() -> None:
    native = load_native()
    grid = hand_grid()
    canonical = [
        [0, 0, 0, 0],
        [0, 0, 4, 0],
        [0, 0, 0, 2],
        [0, 7, 0, 0],
    ]
    aligned = [
        [4, 0, 0, 0],
        [0, 2, 0, 0],
        [0, 0, 0, 7],
        [0, 0, 0, 0],
    ]
    assert native.transform(grid, "in_place") == canonical
    assert native.transform(grid, "first_match_to_origin") == aligned
    assert native.analyze(grid)["first_match"] == [1, 2]


def test_generated_inputs_are_matched_distinct_and_teaching_complete() -> None:
    native = load_native()
    canonical = native.generate(29, {"match_alignment": "in_place"}, demos=3, queries=4)
    alternative = native.generate(
        29, {"match_alignment": "first_match_to_origin"}, demos=3, queries=4
    )
    assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
        p["input"] for p in alternative["train"] + alternative["test"]
    ]
    inputs = [p["input"] for p in alternative["train"] + alternative["test"]]
    encoded = [json.dumps(grid, separators=(",", ":")) for grid in inputs]
    assert len(encoded) == len(set(encoded)) == 7
    assert alternative["certificate"]["surviving_settings"] == [
        {"match_alignment": "first_match_to_origin"}
    ]
    assert alternative["certificate"]["ambiguous_rivals"] == []
    assert all(
        pair["output"] == native.transform(pair["input"], "first_match_to_origin")
        for pair in alternative["train"] + alternative["test"]
    )


def test_large_query_is_real_30_by_30_header_problem() -> None:
    native = load_native()
    episode = native.generate(31, {"match_alignment": "first_match_to_origin"}, 6, 4)
    grid = episode["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    analysis = native.analyze(grid)
    assert analysis["first_match"] == [8, 9]
    assert analysis["match_count"] >= 80
    assert len({v for row in analysis["field"] for v in row if v}) >= 3


@pytest.mark.parametrize(
    "seed,demos,queries,settings,error",
    [
        (False, 3, 4, {"match_alignment": "in_place"}, TypeError),
        (0, 2, 4, {"match_alignment": "in_place"}, ValueError),
        (0, 3, 5, {"match_alignment": "in_place"}, ValueError),
        (0, 3, 4, {"match_alignment": "unknown"}, ValueError),
        (0, 3, 4, {"match_alignment": "in_place", "extra": 1}, ValueError),
    ],
)
def test_invalid_requests_fail_closed(seed, demos, queries, settings, error) -> None:
    native = load_native()
    with pytest.raises(error):
        native.generate(seed, settings, demos, queries)


def test_counterfactual_program_forces_requested_anchor() -> None:
    native = load_native()
    source = native.counterfactual_program((0, 0))
    assert "(ar 0)" in source
    assert "(ac 0)" in source
    assert "(ar (first anchor))" not in source
    assert "(ac (second anchor))" not in source
