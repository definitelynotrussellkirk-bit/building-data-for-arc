"""Focused tests for the native sort-direction parametric family."""
from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys

import pytest

TASK = Path(__file__).resolve().parents[1]
REPO = TASK.parents[1]
PARAMETRIC = TASK / "workspace" / "parametric"

def _module(name: str):
    sys.modules.pop(name, None)
    paths = [str(PARAMETRIC), str(REPO / "shared" / "runtime")]
    before = list(sys.path)
    sys.path[:0] = paths
    try:
        return importlib.import_module(name)
    finally:
        sys.path[:] = before


def _canonical_program() -> str:
    programs = {
        json.loads(line)["program_solution"]
        for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == "78143e5d7ed1"
    }
    assert len(programs) == 1
    return programs.pop()


def test_default_program_is_exact_canonical_bytes():
    adapter = _module("adapter")
    assert adapter.program({"sort_direction": "smallest_first"}) == _canonical_program()


def test_generate_supports_two_to_six_demos_and_four_distinct_queries():
    adapter = _module("adapter")
    for demos in range(2, 7):
        episode = adapter.generate(17, {"sort_direction": "smallest_first"}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        all_inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs}) == demos + 4
        assert (len(episode["test"][-1]["input"]), len(episode["test"][-1]["input"][0])) == (30, 30)


def test_settings_share_inputs_and_every_demo_distinguishes_direction():
    adapter = _module("adapter")
    small = adapter.generate(29, {"sort_direction": "smallest_first"}, 3, 4)
    large = adapter.generate(29, {"sort_direction": "largest_first"}, 3, 4)
    for split in ("train", "test"):
        assert [pair["input"] for pair in small[split]] == [pair["input"] for pair in large[split]]
    assert all(a["output"] != b["output"] for a, b in zip(small["train"], large["train"]))


def test_two_demo_teaching_set_rejects_declared_shortcuts_for_both_settings():
    family = _module("sort_pack_family")
    for direction in family.SORT_DIRECTIONS:
        report = family.audit_episode(97, direction, demos=2, queries=4)
        assert report["surviving_rivals"] == []
        assert report["query_count"] == 4
        assert report["has_30x30_query"] is True


def test_large_query_is_structural_not_padding():
    family = _module("sort_pack_family")
    grid = family.sample_query(5, 3)
    facts = family.analyze(grid)
    assert facts["shape"] == [30, 30]
    assert facts["component_count"] == 7
    assert facts["foreground_cells"] >= 40
    assert facts["touches_all_canvas_sides"] is True
    assert facts["packed_shape"][1] >= 25


def test_public_projection_excludes_private_program_setting_and_query_answers():
    adapter = _module("adapter")
    runtime = str(REPO / "shared" / "runtime")
    sys.path.insert(0, runtime)
    try:
        from reviewer_support import public_challenge_bytes
    finally:
        sys.path.remove(runtime)

    episode = adapter.generate(3, {"sort_direction": "largest_first"}, 2, 4)
    visible = public_challenge_bytes(episode)
    assert b"sort_direction" not in visible
    assert b"program_solution" not in visible
    public = json.loads(visible)
    assert all(set(pair) == {"input"} for pair in public["test"])


def test_invalid_counts_settings_and_typed_values_fail_closed():
    adapter = _module("adapter")
    bad_settings = [None, {}, {"sort_direction": "ascending"},
                    {"sort_direction": "smallest_first", "extra": 1}]
    for settings in bad_settings:
        with pytest.raises(ValueError):
            adapter.program(settings)
    for seed, demos, queries in [(True, 2, 4), (0, 1, 4), (0, 7, 4), (0, 2, 0), (0, 2, 5)]:
        with pytest.raises(ValueError):
            adapter.generate(seed, {"sort_direction": "smallest_first"}, demos, queries)


def test_intermediate_records_input_dependent_full_sort_keys():
    family = _module("sort_pack_family")
    grid = family.sample_query(11, 1)
    state = family.sort_intermediate(grid, "largest_first")
    assert len(state["ordered_components"]) >= 4
    assert all(len(row["key"]) == 4 for row in state["ordered_components"])
    assert state["ordered_components"] == sorted(
        state["ordered_components"], key=lambda row: tuple(row["key"]), reverse=True
    )
