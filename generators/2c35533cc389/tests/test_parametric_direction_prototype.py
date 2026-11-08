"""Contract tests for the isolated direction-parameter prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge

PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)


def _prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric direction prototype is missing"
    spec = importlib.util.spec_from_file_location(
        "right_hand_echo_parametric_prototype", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_direction_parameter_preserves_canonical_right_and_changes_outputs():
    proto = _prototype()
    assert proto.DEFAULT_DIRECTION == "right"
    assert proto.ALLOWED_DIRECTIONS == ("right", "left")
    grid = proto.make_input(7300, 0)
    right = proto.apply_python(grid, "right")
    left = proto.apply_python(grid, "left")
    assert right != left


def test_complete_episode_uses_one_setting_and_refutes_the_other_direction():
    proto = _prototype()
    for direction in proto.ALLOWED_DIRECTIONS:
        episode = proto.build_episode(7300, direction=direction)
        assert episode["meta"]["direction"] == direction
        assert len(episode["train"]) == 3
        assert proto.parameter_rival_findings(episode) == []


def test_both_exact_racket_programs_match_python_and_diverge():
    proto = _prototype()
    grid = proto.make_input(7300, 1)
    outputs = {}
    with RacketBridge(max_calls_before_restart=32) as bridge:
        for direction in proto.ALLOWED_DIRECTIONS:
            program = proto.program_for(direction)
            outputs[direction] = proto.apply_racket(bridge, program, grid)
            assert outputs[direction] == proto.apply_python(grid, direction)
    assert outputs["right"] != outputs["left"]


def test_materialized_public_challenges_hide_setting_program_and_query_answer(tmp_path):
    proto = _prototype()
    report = proto.materialize(tmp_path, seed_start=7300)
    assert report["status"] == "passed"
    assert {row["direction"] for row in report["episodes"]} == set(
        proto.ALLOWED_DIRECTIONS
    )
    for row in report["episodes"]:
        public = json.loads((tmp_path / row["public_path"]).read_text())
        assert "meta" not in public
        assert "program" not in public
        assert "output" not in public["test"]
        assert len(public["train"]) == 3
