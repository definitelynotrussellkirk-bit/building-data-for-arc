from __future__ import annotations

import hashlib
import importlib.util
import json

import pytest

from reviewer_support import find_root

TASK = "82bce7d23c06"
ROOT = find_root(__file__)
HERE = ROOT / "generators" / TASK
PROTOTYPE = HERE / "workspace/parametric/prototype.py"


def _load_family():
    body = PROTOTYPE.read_bytes()
    name = "_test_parametric_82b_" + hashlib.sha256(body).hexdigest()
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_bytes():
    family = _load_family()
    canonical = (HERE / "workspace/parametric/canonical.rkt").read_text(encoding="utf-8")
    assert family.program({"finish": "project_only"}) == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == family.CANONICAL_SHA256


def test_two_demo_four_query_episode_is_matched_distinct_and_labeled():
    family = _load_family()
    canonical = family.generate(17, {"finish": "project_only"}, 2, 4)
    relay = family.generate(17, {"finish": "component_count_relay"}, 2, 4)
    assert (len(canonical["train"]), len(canonical["test"])) == (2, 4)
    assert _inputs(canonical) == _inputs(relay)
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)]
    assert len(serialized) == len(set(serialized))
    stress = relay["test"][-1]
    assert [len(stress["output"]), len(stress["output"][0])] == [30, 30]
    analysis = family.analyze(stress["input"])
    assert analysis["output_shape"] == [30, 30]
    assert analysis["boundary_sides"] == ["bottom", "left", "right", "top"]
    assert analysis["projected_component_count"] == 3
    assert analysis["nonzero_count"] == 5
    assert analysis["projected_nonzero_count"] > 100
    for episode in (canonical, relay):
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == family.solve(pair["input"], episode["settings"])


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("finish", ("project_only", "component_count_relay"))
def test_every_supported_demo_prefix_rejects_other_setting_and_declared_rivals(demos, finish):
    family = _load_family()
    episode = family.generate(91, {"finish": finish}, demos, 4)
    certificate = family.lesson_certificate(episode["train"], episode["settings"])
    assert certificate["surviving_settings"] == [episode["settings"]]
    assert certificate["surviving_shortcuts"] == []
    assert certificate["query_outputs_used"] is False


def test_relay_consumes_projected_component_count_and_counterfactual_changes_output():
    family = _load_family()
    episode = family.generate(0, {"finish": "component_count_relay"}, 2, 4)
    pair = episode["train"][0]
    info = family.intermediate(pair["input"])
    assert info["projected_component_count"] == 2
    assert info["source_color_run_count"] == 3
    assert info["target_nonzero_rank"] == info["projected_component_count"]
    assert info["target_source_col"] != info["counterfactual_target_source_col"]
    assert pair["output"] != family.counterfactual_transform(pair["input"])


def test_relay_paints_one_projected_diagonal_not_all_cells_of_its_color():
    family = _load_family()
    pair = family.generate(0, {"finish": "component_count_relay"}, 2, 4)["train"][0]
    info = family.intermediate(pair["input"])
    target_color = pair["input"][0][info["target_source_col"]]
    changed = {
        (r, c)
        for r, (before_row, after_row) in enumerate(zip(family.solve(pair["input"], {"finish": "project_only"}), pair["output"]))
        for c, (before, after) in enumerate(zip(before_row, after_row))
        if before != after
    }
    assert changed == {tuple(cell) for cell in info["target_diagonal_cells"]}
    assert all(family.solve(pair["input"], {"finish": "project_only"})[r][c] == target_color for r, c in changed)
    assert any(
        value == target_color and (r, c) not in changed
        for r, row in enumerate(family.solve(pair["input"], {"finish": "project_only"}))
        for c, value in enumerate(row)
    )


def test_public_turn_hides_answers_settings_and_future_queries():
    family = _load_family()
    episode = family.generate(3, {"finish": "component_count_relay"}, 3, 4)
    view = family.public_turn(episode, 0)
    assert set(view) == {"train", "test"}
    assert len(view["test"]) == 1
    assert set(view["test"][0]) == {"input"}
    assert "settings" not in view and "program_solution" not in view
    assert view["test"][0]["input"] == episode["test"][0]["input"]


@pytest.mark.parametrize("bad", [1, None, {}, {"finish": "unknown"}, {"finish": "project_only", "x": 1}])
def test_settings_fail_closed(bad):
    family = _load_family()
    with pytest.raises((TypeError, ValueError)):
        family.generate(1, bad, 2, 4)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (2, 0), (2, 5), (True, 4)])
def test_count_limits_fail_closed(demos, queries):
    family = _load_family()
    with pytest.raises((TypeError, ValueError)):
        family.generate(1, {"finish": "project_only"}, demos, queries)


@pytest.mark.parametrize("seed", [0, 17, 97])
def test_exact_30x30_stress_is_substantive_for_audit_seeds(seed):
    family = _load_family()
    grid = family.generate(seed, {"finish": "component_count_relay"}, 2, 4)["test"][-1]["input"]
    analysis = family.analyze(grid)
    assert analysis["input_shape"] == [1, 6]
    assert analysis["output_shape"] == [30, 30]
    assert analysis["boundary_sides"] == ["bottom", "left", "right", "top"]
    assert analysis["nonzero_count"] == 5
    assert analysis["projected_component_count"] == 3
    assert analysis["source_color_run_count"] == 4
    assert analysis["target_nonzero_rank"] == 3
