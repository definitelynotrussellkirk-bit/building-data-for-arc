"""Native contract tests for the 22e428cda452 parametric family."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "22e428cda452"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
CANONICAL_PATH = PARAMETRIC / "canonical.rkt"


def _adapter():
    spec = importlib.util.spec_from_file_location("projection_total_native", ADAPTER_PATH)
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
        "adapter": "generators/22e428cda452/workspace/parametric/adapter.py",
        "parameters": {
            "finish": ["project_only", "highlight_most_projected_color"]
        },
        "default": {"finish": "project_only"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/22e428cda452/workspace/parametric/canonical.rkt",
            "generators/22e428cda452/workspace/parametric/highlight_most_projected_color.rkt",
            "generators/22e428cda452/workspace/parametric/highlight_most_source_markers.rkt",
        ],
    }
    adapter = _adapter()
    assert CANONICAL_PATH.read_text() == _canonical_source()
    assert adapter.program({"finish": "project_only"}) == _canonical_source()
    assert adapter.program({"finish": "highlight_most_projected_color"}) != _canonical_source()


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_inputs_labels_and_matched_settings(demos, queries):
    adapter = _adapter()
    episodes = {
        finish: adapter.generate(73, {"finish": finish}, demos, queries)
        for finish in adapter.SETTINGS
    }
    for finish, episode in episodes.items():
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        assert episode["program_solution"] == adapter.program({"finish": finish})
        pairs = episode["train"] + episode["test"]
        encoded = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
        assert len(set(encoded)) == len(encoded)
        for pair in pairs:
            assert pair["output"] == adapter.predict(pair["input"], finish)
            state = adapter.observe(pair["input"])
            assert state["source_marker_count"] in (3, 4)
            assert state["top_marker_count"] in (1, 2)
            assert state["bottom_marker_count"] == 2
            assert state["largest_projected_count"] == 1
            assert state["projected_nonbackground_cells"] in (10, 11, 13, 14)
            assert set(state["touches"]) == {"bottom", "left", "right", "top"}
    for split in ("train", "test"):
        assert [pair["input"] for pair in episodes["project_only"][split]] == [
            pair["input"]
            for pair in episodes["highlight_most_projected_color"][split]
        ]


def test_two_demos_identify_both_settings_and_refute_declared_shortcuts():
    adapter = _adapter()
    demos, queries = adapter.input_banks(431, demos=2)
    for finish in adapter.SETTINGS:
        train = [{"input": grid, "output": adapter.predict(grid, finish)} for grid in demos]
        report = adapter.certificate(train, queries)
        assert report["survivors"] == [finish]
        assert report["query_changing_survivors"] == []
    states = [adapter.observe(grid) for grid in demos]
    assert [state["winner_has_top_marker"] for state in states] == [True, False]
    assert states[0]["largest_projected_color"] != states[0]["most_source_markers_color"]
    assert states[1]["largest_projected_color"] == states[1]["most_source_markers_color"]


def test_four_query_bank_includes_30x30_all_corner_stress():
    adapter = _adapter()
    _, queries = adapter.input_banks(20261025, demos=3)
    assert len(queries) == 4
    large = queries[-1]
    assert len(large) == 30 and len(large[0]) == 30
    state = adapter.observe(large)
    assert state["source_marker_count"] == 4
    assert state["top_marker_count"] == 2
    assert state["bottom_marker_count"] == 2
    assert state["projected_nonbackground_cells"] == 14
    assert adapter.predict(large, "project_only") != adapter.predict(
        large, "highlight_most_projected_color"
    )


def test_wrong_source_count_intermediate_changes_the_final_output():
    adapter = _adapter()
    grid = adapter.input_banks(19, demos=2)[0][0]
    dependency = adapter.explain_dependency(grid)
    assert dependency["largest_projected_color"] != dependency["most_source_markers_color"]
    intended = adapter.predict(grid, "highlight_most_projected_color")
    wrong = adapter.predict(grid, "highlight_most_source_markers")
    assert intended != wrong
    assert sum(cell == 1 for row in intended for cell in row) == 4
    assert sum(cell == 1 for row in wrong for cell in row) == 3


@pytest.mark.parametrize(
    "args",
    [
        (True, {"finish": "project_only"}, 2, 4),
        (0, {"finish": "project_only"}, True, 4),
        (0, {"finish": "project_only"}, 2, 0),
        (0, {"finish": "unknown"}, 2, 4),
        (0, {}, 2, 4),
    ],
)
def test_invalid_contract_values_are_rejected(args):
    adapter = _adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(*args)
