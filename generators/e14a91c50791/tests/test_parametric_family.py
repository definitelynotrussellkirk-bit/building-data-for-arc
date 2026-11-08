from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"


def load_adapter():
    path = PARAM / "adapter.py"
    spec = importlib.util.spec_from_file_location("e14_parametric_adapter", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def input_fingerprint(grid):
    return json.dumps(grid, separators=(",", ":"))


def test_settings_share_inputs_and_default_program_is_exact():
    adapter = load_adapter()
    left = adapter.generate(17, {"finish": "bbox_only"}, demos=3, queries=4)
    right = adapter.generate(17, {"finish": "largest_orange_cluster"}, demos=3, queries=4)
    assert [p["input"] for p in left["train"] + left["test"]] == [
        p["input"] for p in right["train"] + right["test"]
    ]
    assert adapter.program({"finish": "bbox_only"}).encode() == (PARAM / "canonical.rkt").read_bytes()
    assert left["program_solution"] == adapter.program({"finish": "bbox_only"})


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_supported_counts_are_independent_and_inputs_distinct(demos, queries):
    adapter = load_adapter()
    episode = adapter.generate(5, {"finish": "largest_orange_cluster"}, demos=demos, queries=queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    inputs = [input_fingerprint(p["input"]) for p in episode["train"] + episode["test"]]
    assert len(inputs) == len(set(inputs))
    assert adapter.teaching_check(episode)["status"] == "identified"


def test_queries_are_prefix_stable_and_public_turns_hide_answers_and_future_queries():
    adapter = load_adapter()
    four = adapter.generate(9, {"finish": "bbox_only"}, demos=3, queries=4)
    one = adapter.generate(9, {"finish": "bbox_only"}, demos=3, queries=1)
    assert four["train"] == one["train"]
    assert four["test"][0] == one["test"][0]
    first = adapter.public_turn(four, 0)
    assert first == adapter.public_turn(one, 0)
    assert len(first["test"]) == 1 and "output" not in first["test"][0]
    assert "settings" not in first and "program_solution" not in first
    for index in range(1, 4):
        turn = adapter.public_turn(four, index)
        assert set(turn) == {"test"}
        assert turn == {"test": [{"input": four["test"][index]["input"]}]}


def test_alternative_uses_post_fill_cluster_and_counterfactual_changes_output():
    adapter = load_adapter()
    episode = adapter.generate(0, {"finish": "largest_orange_cluster"}, demos=2, queries=4)
    grid = episode["test"][3]["input"]
    selected = adapter.solve(grid, {"finish": "largest_orange_cluster"})
    wrong = adapter.wrong_intermediate_solve(grid)
    trace = adapter.dependency_trace(grid, {"finish": "largest_orange_cluster"})
    assert selected != wrong
    assert trace["orange_components"] >= 2
    assert trace["largest_orange_cells"] > trace["smallest_orange_cells"]
    assert trace["step_a"] and trace["step_b"] and trace["why_b_depends_on_a"]


def test_fourth_query_is_substantive_30_by_30():
    adapter = load_adapter()
    episode = adapter.generate(23, {"finish": "largest_orange_cluster"}, demos=2, queries=4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(cell != 0 for row in grid for cell in row) >= 25
    out = episode["test"][3]["output"]
    assert sum(cell == 4 for row in out for cell in row) >= 8
    assert sum(cell == 7 for row in out for cell in row) >= 4


@pytest.mark.parametrize("settings", [{}, {"finish": "bogus"}, {"finish": True}, {"finish": "bbox_only", "x": 1}])
def test_invalid_settings_reject(settings):
    adapter = load_adapter()
    with pytest.raises(ValueError):
        adapter.generate(0, settings, demos=2, queries=1)
