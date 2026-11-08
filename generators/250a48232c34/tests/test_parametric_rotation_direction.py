from __future__ import annotations

import importlib.util
import json

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "250a48232c34"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name, filename):
    path = HOME / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ADAPTER = _load("parametric_250_adapter", "adapter.py")
PROTOTYPE = _load("parametric_250_prototype", "prototype.py")


def _canonical_program():
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line]
    matches = [row for row in rows if row.get("task_id") == TASK_ID]
    assert len(matches) == 1
    return matches[0]["program_solution"]


def _inputs(episode):
    return [pair["input"] for pair in [*episode["train"], *episode["test"]]]


def test_default_program_is_exact_canonical_and_counterclockwise_is_distinct():
    canonical = _canonical_program()
    assert ADAPTER.program({"rotation_direction": "clockwise"}) == canonical
    assert ADAPTER.program({"rotation_direction": "counterclockwise"}) != canonical


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("queries", range(1, 5))
def test_counts_inputs_and_setting_contrast(demos, queries):
    cw = ADAPTER.generate(19, {"rotation_direction": "clockwise"}, demos, queries)
    ccw = ADAPTER.generate(19, {"rotation_direction": "counterclockwise"}, demos, queries)
    assert len(cw["train"]) == len(ccw["train"]) == demos
    assert len(cw["test"]) == len(ccw["test"]) == queries
    assert _inputs(cw) == _inputs(ccw)
    frozen = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(cw)]
    assert len(frozen) == len(set(frozen))
    assert all(
        left["output"] != right["output"]
        for left, right in zip([*cw["train"], *cw["test"]], [*ccw["train"], *ccw["test"]])
    )


def test_every_scene_uses_all_rotation_colors_and_asymmetric_template():
    for seed in range(16):
        episode = ADAPTER.generate(seed, {"rotation_direction": "clockwise"}, 2, 4)
        for pair in [*episode["train"], *episode["test"]]:
            facts = PROTOTYPE.inspect_scene(pair["input"])
            assert [color for _r, _c, color in facts["anchors"]] == [1, 2, 3, 4]
            assert PROTOTYPE.rotate(facts["template"], 1) != PROTOTYPE.rotate(facts["template"], 3)


def test_fourth_query_is_distributed_30_by_30_stress():
    episode = ADAPTER.generate(7, {"rotation_direction": "clockwise"}, 3, 4)
    pair = episode["test"][-1]
    assert (len(pair["input"]), len(pair["input"][0])) == (30, 30)
    facts = PROTOTYPE.inspect_scene(pair["input"])
    assert len(facts["template"]) >= 6
    rows = [r for r, _c, _color in facts["anchors"]]
    cols = [c for _r, c, _color in facts["anchors"]]
    assert max(rows) - min(rows) >= 24
    assert max(cols) - min(cols) >= 24


def test_bounded_rival_audit_has_no_harmful_survivors():
    report = PROTOTYPE.bounded_audit(seeds=range(16), demos=2, queries=4)
    assert report["episodes"] == 32
    assert report["harmful_survivors"] == []


def test_dependency_trace_exposes_rotated_cell_intermediate():
    episode = ADAPTER.generate(3, {"rotation_direction": "counterclockwise"}, 2, 4)
    trace = PROTOTYPE.dependency_trace(
        episode["test"][0]["input"], {"rotation_direction": "counterclockwise"}
    )
    assert trace["step_a"] == "extract_template_and_rotate_for_each_anchor"
    assert trace["step_b"] == "stamp_each_rotated_template_at_its_anchor"
    assert len(trace["intermediate"]["rotated_cells_by_color"]) == 4
    assert trace["output"] == episode["test"][0]["output"]
    assert trace["counterfactual_clockwise_output"] != trace["output"]


def test_invalid_settings_and_requests_fail_closed():
    with pytest.raises(ValueError):
        ADAPTER.program({"rotation_direction": "sideways"})
    with pytest.raises(ValueError):
        ADAPTER.program({"rotation_direction": "clockwise", "extra": 1})
    with pytest.raises(ValueError):
        ADAPTER.generate(True, {"rotation_direction": "clockwise"}, 3, 4)
    with pytest.raises(ValueError):
        ADAPTER.generate(0, {"rotation_direction": "clockwise"}, 1, 4)
    with pytest.raises(ValueError):
        ADAPTER.generate(0, {"rotation_direction": "clockwise"}, 3, 5)
