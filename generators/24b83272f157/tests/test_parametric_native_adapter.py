"""Focused tests for the native contact-degree parametric family."""
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
        if json.loads(line).get("task_id") == "24b83272f157"
    }
    assert len(programs) == 1
    return programs.pop()


def test_default_program_is_exact_canonical_bytes():
    adapter = _module("adapter")
    assert adapter.program({"finish": "degree_palette"}) == _canonical_program()


def test_generate_supports_two_to_six_demos_and_four_distinct_queries():
    adapter = _module("adapter")
    for demos in range(2, 7):
        episode = adapter.generate(17, {"finish": "degree_palette"}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == demos + 4
        assert (len(episode["test"][-1]["input"]), len(episode["test"][-1]["input"][0])) == (30, 30)


def test_settings_share_inputs_and_visible_demos_distinguish_finish():
    adapter = _module("adapter")
    palette = adapter.generate(29, {"finish": "degree_palette"}, 3, 4)
    highlight = adapter.generate(29, {"finish": "highlight_max_degree"}, 3, 4)
    for split in ("train", "test"):
        assert [pair["input"] for pair in palette[split]] == [pair["input"] for pair in highlight[split]]
    assert all(a["output"] != b["output"] for a, b in zip(palette["train"], highlight["train"]))


def test_two_demo_teaching_set_rejects_declared_shortcuts_for_both_settings():
    family = _module("contact_degree_family")
    for finish in family.FINISHES:
        report = family.audit_episode(97, finish, demos=2, queries=4)
        assert report["surviving_rivals"] == []
        assert report["query_count"] == 4
        assert report["has_30x30_query"] is True


def test_minimum_lesson_never_collapses_to_highest_input_color_across_seed_census():
    family = _module("contact_degree_family")
    failures = []
    for seed in range(256):
        report = family.audit_episode(
            seed, "highlight_max_degree", demos=2, queries=4
        )
        if "highest_input_color" in report["surviving_rivals"]:
            failures.append(seed)
    assert failures == []


def test_large_query_is_structural_not_padding():
    family = _module("contact_degree_family")
    grid = family.sample_query(5, 3)
    facts = family.analyze(grid)
    assert facts["shape"] == [30, 30]
    assert 7 <= facts["component_count"] <= 10
    assert facts["foreground_cells"] >= 20
    assert facts["touches_all_canvas_sides"] is True
    assert len(set(facts["degrees"])) >= 3
    assert facts["max_degree"] >= 3
    assert set(facts["max_degree_indices"]) != set(facts["largest_object_indices"])


def test_highlight_finish_recolors_exactly_the_max_degree_class():
    family = _module("contact_degree_family")
    grid = family.sample_demo(23, 0)
    output = family.solve(grid, "highlight_max_degree")
    state = family.contact_intermediate(grid)
    selected = set(state["max_degree_indices"])
    for index, component in enumerate(state["components"]):
        values = {output[row][col] for row, col in component["cells"]}
        assert values == ({9} if index in selected else {component["color"]})


def test_public_projection_excludes_private_program_setting_and_query_answers():
    adapter = _module("adapter")
    before = list(sys.path)
    sys.path.insert(0, str(REPO / "shared" / "runtime"))
    try:
        from reviewer_support import public_challenge_bytes
    finally:
        sys.path[:] = before
    episode = adapter.generate(3, {"finish": "highlight_max_degree"}, 2, 4)
    visible = public_challenge_bytes(episode)
    assert b"highlight_max_degree" not in visible
    assert b"program_solution" not in visible
    public = json.loads(visible)
    assert all(set(pair) == {"input"} for pair in public["test"])


def test_invalid_counts_settings_and_typed_values_fail_closed():
    adapter = _module("adapter")
    for settings in (None, {}, {"finish": "largest"},
                     {"finish": "degree_palette", "extra": 1}):
        with pytest.raises(ValueError):
            adapter.program(settings)
    for seed, demos, queries in ((True, 2, 4), (0, 1, 4), (0, 7, 4), (0, 2, 0), (0, 2, 5)):
        with pytest.raises(ValueError):
            adapter.generate(seed, {"finish": "degree_palette"}, demos, queries)


def test_intermediate_records_contact_graph_degrees_and_maximum():
    family = _module("contact_degree_family")
    grid = family.sample_query(11, 1)
    state = family.contact_intermediate(grid)
    assert len(state["components"]) == len(state["degrees"])
    assert state["max_degree"] == max(state["degrees"])
    assert state["max_degree_indices"] == [
        index for index, degree in enumerate(state["degrees"])
        if degree == state["max_degree"]
    ]
    assert all(index not in neighbors for index, neighbors in enumerate(state["graph"]))
