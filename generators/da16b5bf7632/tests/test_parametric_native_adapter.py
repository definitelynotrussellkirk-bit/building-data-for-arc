"""Focused tests for the native hole-sort parametric family."""
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
    before = list(sys.path)
    sys.path[:0] = [str(PARAMETRIC), str(REPO / "shared" / "runtime")]
    try:
        return importlib.import_module(name)
    finally:
        sys.path[:] = before


def _canonical_program() -> str:
    programs = {
        json.loads(line)["program_solution"]
        for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == "da16b5bf7632"
    }
    assert len(programs) == 1
    return programs.pop()


def test_default_program_is_exact_canonical_bytes():
    adapter = _module("adapter")
    assert adapter.program({"sort_direction": "most_holes_first"}) == _canonical_program()


def test_generate_supports_two_to_six_demos_and_four_distinct_queries():
    adapter = _module("adapter")
    for demos in range(2, 7):
        episode = adapter.generate(17, {"sort_direction": "most_holes_first"}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == demos + 4
        assert (len(episode["test"][-1]["input"]), len(episode["test"][-1]["input"][0])) == (30, 30)


def test_settings_share_inputs_and_visible_demos_distinguish_direction():
    adapter = _module("adapter")
    desc = adapter.generate(29, {"sort_direction": "most_holes_first"}, 3, 4)
    asc = adapter.generate(29, {"sort_direction": "fewest_holes_first"}, 3, 4)
    for split in ("train", "test"):
        assert [pair["input"] for pair in desc[split]] == [pair["input"] for pair in asc[split]]
    assert all(a["output"] != b["output"] for a, b in zip(desc["train"], asc["train"]))


def test_two_demo_teaching_set_rejects_declared_shortcuts_for_both_settings():
    family = _module("hole_sort_family")
    for direction in family.SORT_DIRECTIONS:
        report = family.audit_episode(97, direction, demos=2, queries=4)
        assert report["surviving_rivals"] == []
        assert report["query_count"] == 4
        assert report["has_30x30_query"] is True


def test_large_query_is_structural_not_padding():
    family = _module("hole_sort_family")
    grid = family.sample_query(5, 3)
    facts = family.analyze(grid)
    assert facts["shape"] == [30, 30]
    assert facts["component_count"] == 6
    assert facts["foreground_cells"] >= 50
    assert facts["touches_all_canvas_sides"] is True
    assert facts["packed_shape"][1] >= 25
    assert {0, 1, 2, 3}.issubset(set(facts["hole_counts"]))


def test_public_projection_excludes_private_program_setting_and_query_answers():
    adapter = _module("adapter")
    before = list(sys.path)
    sys.path.insert(0, str(REPO / "shared" / "runtime"))
    try:
        from reviewer_support import public_challenge_bytes
    finally:
        sys.path[:] = before
    episode = adapter.generate(3, {"sort_direction": "fewest_holes_first"}, 2, 4)
    visible = public_challenge_bytes(episode)
    assert b"sort_direction" not in visible
    assert b"program_solution" not in visible
    public = json.loads(visible)
    assert all(set(pair) == {"input"} for pair in public["test"])


def test_invalid_counts_settings_and_typed_values_fail_closed():
    adapter = _module("adapter")
    for settings in (None, {}, {"sort_direction": "ascending"},
                     {"sort_direction": "most_holes_first", "extra": 1}):
        with pytest.raises(ValueError):
            adapter.program(settings)
    for seed, demos, queries in ((True, 2, 4), (0, 1, 4), (0, 7, 4), (0, 2, 0), (0, 2, 5)):
        with pytest.raises(ValueError):
            adapter.generate(seed, {"sort_direction": "most_holes_first"}, demos, queries)


def test_intermediate_records_input_dependent_hole_counts_and_order():
    family = _module("hole_sort_family")
    grid = family.sample_query(11, 1)
    state = family.sort_intermediate(grid, "fewest_holes_first")
    rows = state["ordered_components"]
    assert len(rows) >= 4
    assert all(type(row["holes"]) is int for row in rows)
    assert [row["holes"] for row in rows] == sorted(row["holes"] for row in rows)
    assert len({tuple(row["bbox"]) for row in rows}) == len(rows)
