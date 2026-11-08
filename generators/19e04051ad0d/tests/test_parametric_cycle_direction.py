"""Contract tests for the isolated cycle-direction parameter prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge

PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)


def _prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric cycle-direction prototype is missing"
    spec = importlib.util.spec_from_file_location(
        "cyclic_region_parametric_prototype", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cycle_direction_preserves_canonical_default_and_changes_outputs():
    proto = _prototype()
    assert proto.DEFAULT_DIRECTION == "next"
    assert proto.ALLOWED_DIRECTIONS == ("next", "previous")
    grid = proto.make_input(7300, 0)
    assert proto.apply_python(grid, "next") != proto.apply_python(grid, "previous")


def test_programs_differ_only_at_the_cycle_index_expression():
    proto = _prototype()
    next_program = proto.program_for("next")
    previous_program = proto.program_for("previous")
    assert next_program.count("(remainder (+ i 1) n)") == 1
    assert "(remainder (+ i (- n 1)) n)" not in next_program
    assert previous_program.count("(remainder (+ i (- n 1)) n)") == 1
    assert previous_program == next_program.replace(
        "(remainder (+ i 1) n)", "(remainder (+ i (- n 1)) n)"
    )


def test_complete_episode_uses_one_setting_and_refutes_the_other_direction():
    proto = _prototype()
    for direction in proto.ALLOWED_DIRECTIONS:
        episode = proto.build_episode(7300, direction=direction)
        assert episode["meta"]["cycle_direction"] == direction
        assert len(episode["train"]) == 3
        assert proto.parameter_rival_findings(episode) == []
        for pair in [*episode["train"], episode["test"]]:
            assert pair["output"] == proto.apply_python(pair["input"], direction)


def test_both_exact_racket_programs_match_python_and_diverge():
    proto = _prototype()
    grid = proto.make_input(7300, 1)
    outputs = {}
    with RacketBridge(max_calls_before_restart=32) as bridge:
        for direction in proto.ALLOWED_DIRECTIONS:
            program = proto.program_for(direction)
            outputs[direction] = proto.apply_racket(bridge, program, grid)
            assert outputs[direction] == proto.apply_python(grid, direction)
    assert outputs["next"] != outputs["previous"]


def test_materialized_public_challenges_hide_setting_program_and_query_answer(tmp_path):
    proto = _prototype()
    report = proto.materialize(tmp_path, seed_start=7300)
    assert report["status"] == "passed"
    assert {row["cycle_direction"] for row in report["episodes"]} == set(
        proto.ALLOWED_DIRECTIONS
    )
    for row in report["episodes"]:
        public = json.loads((tmp_path / row["public_path"]).read_text())
        assert "meta" not in public
        assert "program" not in public
        assert "output" not in public["test"]
        assert len(public["train"]) == 3


def test_parameter_and_seed_validation_are_exact():
    proto = _prototype()
    with pytest.raises(TypeError, match="seed"):
        proto.choose_direction(True)
    with pytest.raises(ValueError, match="cycle_direction"):
        proto.program_for("sideways")
