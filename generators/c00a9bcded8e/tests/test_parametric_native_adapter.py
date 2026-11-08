"""Native contract tests for the c00a9bcded8e parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "c00a9bcded8e"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
ADAPTER_PATH = HOME / "workspace" / "parametric" / "adapter.py"
PROMOTION_PATH = HOME / "workspace" / "parametric" / "promotion.json"
CANONICAL_PATH = HOME / "workspace" / "parametric" / "canonical.rkt"


def _adapter():
    spec = importlib.util.spec_from_file_location("c00_native_parametric", ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    rows = [
        json.loads(line)
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if line
    ]
    matches = [row["program_solution"] for row in rows if row.get("task_id") == TASK_ID]
    assert len(matches) == 1
    return matches[0]


def test_promotion_contract_and_default_program_are_exact():
    promotion = json.loads(PROMOTION_PATH.read_text())
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/c00a9bcded8e/workspace/parametric/adapter.py",
        "parameters": {"finish": ["colors_only", "highlight_largest_rectangle"]},
        "default": {"finish": "colors_only"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/c00a9bcded8e/workspace/parametric/canonical.rkt",
            "generators/c00a9bcded8e/workspace/parametric/highlight_largest_rectangle.rkt",
            "generators/c00a9bcded8e/workspace/parametric/highlight_largest_perimeter.rkt",
        ],
    }
    adapter = _adapter()
    assert CANONICAL_PATH.read_text() == _canonical_source()
    assert adapter.program({"finish": "colors_only"}) == _canonical_source()
    assert adapter.program({"finish": "highlight_largest_rectangle"}) != _canonical_source()


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_are_independent_inputs_are_unique_and_settings_are_matched(demos, queries):
    adapter = _adapter()
    episodes = {
        finish: adapter.generate(73, {"finish": finish}, demos, queries)
        for finish in adapter.SETTINGS
    }
    for finish, episode in episodes.items():
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        assert episode["program_solution"] == adapter.program({"finish": finish})
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == demos + queries
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == adapter.predict(pair["input"], finish)
            observed = adapter.observe(pair["input"])
            assert observed["row_count"] in (2, 3, 4)
            assert observed["rectangles_per_row"] == [3] * observed["row_count"]
            assert observed["largest_area_count"] == 1
            assert observed["largest_perimeter_count"] == 1
            assert observed["largest_area_position"] != observed["largest_perimeter_position"]
    for split in ("train", "test"):
        assert [pair["input"] for pair in episodes["colors_only"][split]] == [
            pair["input"] for pair in episodes["highlight_largest_rectangle"][split]
        ]


def test_two_demos_identify_both_settings_and_refute_plausible_shortcuts():
    adapter = _adapter()
    inputs = adapter.input_banks(431, demos=2)[0]
    for finish in adapter.SETTINGS:
        train = [{"input": grid, "output": adapter.predict(grid, finish)} for grid in inputs]
        report = adapter.certificate(train, adapter.input_banks(431, demos=2)[1])
        assert report["survivors"] == [finish]
        assert report["query_changing_survivors"] == []
    positions = [adapter.observe(grid)["largest_area_position"] for grid in inputs]
    assert len(set(positions)) == 2


def test_four_query_bank_includes_substantive_30x30_boundary_stress():
    adapter = _adapter()
    _, queries = adapter.input_banks(20261025, demos=3)
    assert len(queries) == 4
    large = queries[-1]
    assert len(large) == 30 and len(large[0]) == 30
    observed = adapter.observe(large)
    assert observed["row_count"] == 4
    assert observed["qualified_cells"] >= 180
    assert set(observed["touches"]) == {"bottom", "left", "right", "top"}
    assert adapter.predict(large, "colors_only") != adapter.predict(
        large, "highlight_largest_rectangle"
    )


def test_sequential_explanation_and_wrong_intermediate_disagree():
    adapter = _adapter()
    grid = adapter.input_banks(19, demos=2)[0][0]
    dependency = adapter.explain_dependency(grid)
    assert dependency["largest_area_position"] != dependency["largest_perimeter_position"]
    intended = adapter.predict(grid, "highlight_largest_rectangle")
    wrong = adapter.predict(grid, "highlight_largest_perimeter")
    assert intended != wrong
    assert sum(cell == 9 for row in intended for cell in row) == 1


@pytest.mark.parametrize(
    "args",
    [
        (True, {"finish": "colors_only"}, 2, 4),
        (0, {"finish": "colors_only"}, True, 4),
        (0, {"finish": "colors_only"}, 2, 0),
        (0, {"finish": "unknown"}, 2, 4),
        (0, {}, 2, 4),
    ],
)
def test_invalid_contract_values_are_rejected(args):
    adapter = _adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(*args)
