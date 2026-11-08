from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import find_root


TASK = "af9ade3c3e16"
ROOT = find_root(__file__)
HERE = ROOT / "generators" / TASK
PROTOTYPE = HERE / "workspace/parametric/prototype.py"


def _load_family():
    body = PROTOTYPE.read_bytes()
    name = "_test_parametric_af9_" + hashlib.sha256(body).hexdigest()
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
    assert family.program({"finish": "frame_only"}) == canonical
    assert hashlib.sha256(canonical.encode()).hexdigest() == family.CANONICAL_SHA256


def test_two_demo_four_query_episode_is_matched_distinct_and_labeled():
    family = _load_family()
    canonical = family.generate(17, {"finish": "frame_only"}, 2, 4)
    composed = family.generate(17, {"finish": "center_cross"}, 2, 4)
    assert (len(canonical["train"]), len(canonical["test"])) == (2, 4)
    assert _inputs(canonical) == _inputs(composed)
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in _inputs(canonical)]
    assert len(serialized) == len(set(serialized))
    assert [len(composed["test"][-1]["input"]), len(composed["test"][-1]["input"][0])] == [30, 30]
    stress = family.analyze(composed["test"][-1]["input"])
    assert stress["boundary_sides"] == ["bottom", "left", "right", "top"]
    assert stress["frame_count"] == 5 and stress["nonzero_count"] > 150
    for episode in (canonical, composed):
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == family.solve(pair["input"], episode["settings"])


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("finish", ("frame_only", "center_cross"))
def test_every_supported_demo_prefix_rejects_other_setting_and_declared_rivals(demos, finish):
    family = _load_family()
    episode = family.generate(91, {"finish": finish}, demos, 4)
    certificate = family.lesson_certificate(episode["train"], episode["settings"])
    assert certificate["surviving_settings"] == [episode["settings"]]
    assert certificate["surviving_shortcuts"] == []


def test_composed_rule_consumes_selected_frame_bbox_and_counterfactual_changes_output():
    family = _load_family()
    episode = family.generate(0, {"finish": "center_cross"}, 2, 4)
    pair = next(
        pair
        for split in ("train", "test")
        for pair in episode[split]
        if family.analyze(pair["input"])["rank"] != 1
    )
    info = family.intermediate(pair["input"])
    assert info["selected_bbox"] != info["outer_bbox"]
    assert info["cross_cells"]
    assert pair["output"] != family.counterfactual_transform(pair["input"])


def test_public_turn_hides_answers_settings_and_future_queries():
    family = _load_family()
    episode = family.generate(3, {"finish": "center_cross"}, 3, 4)
    view = family.public_turn(episode, 0)
    assert set(view) == {"train", "test"}
    assert len(view["test"]) == 1
    assert set(view["test"][0]) == {"input"}
    assert "settings" not in view and "program_solution" not in view
    assert view["test"][0]["input"] == episode["test"][0]["input"]


@pytest.mark.parametrize("bad", [1, None, {}, {"finish": "unknown"}, {"finish": "frame_only", "x": 1}])
def test_settings_fail_closed(bad):
    family = _load_family()
    with pytest.raises((TypeError, ValueError)):
        family.generate(1, bad, 2, 4)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (2, 0), (2, 5), (True, 4)])
def test_count_limits_fail_closed(demos, queries):
    family = _load_family()
    with pytest.raises((TypeError, ValueError)):
        family.generate(1, {"finish": "frame_only"}, demos, queries)

@pytest.mark.parametrize("seed", [0, 17, 97])
def test_exact_30x30_stress_touches_all_boundaries_for_audit_seeds(seed):
    family = _load_family()
    grid = family.generate(seed, {"finish": "center_cross"}, 2, 4)["test"][-1]["input"]
    analysis = family.analyze(grid)
    assert analysis["shape"] == [30, 30]
    assert analysis["boundary_sides"] == ["bottom", "left", "right", "top"]
