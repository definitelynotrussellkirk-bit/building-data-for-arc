"""Focused tests for the isolated quarter-turn rule prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge


PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)


def _prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "e69a3b575440_parametric_prototype", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_quarter_turn_parameter_preserves_default_and_changes_command_two_only():
    proto = _prototype()
    assert proto.DEFAULT_QUARTER_TURN == "clockwise"
    assert proto.ALLOWED_QUARTER_TURNS == ("clockwise", "counterclockwise")

    for command in range(1, 9):
        grid = proto.make_input(command, variant=command)
        clockwise = proto.apply_python(grid, "clockwise")
        counterclockwise = proto.apply_python(grid, "counterclockwise")
        if command == 2:
            assert clockwise != counterclockwise
        else:
            assert clockwise == counterclockwise


def test_complete_episode_uses_one_setting_and_teaches_the_parameter():
    proto = _prototype()
    for setting in proto.ALLOWED_QUARTER_TURNS:
        episode = proto.build_episode(seed=7300, quarter_turn=setting)
        assert episode["meta"]["quarter_turn"] == setting
        assert len(episode["train"]) == 8
        assert [pair["input"][0][0] for pair in episode["train"]] == list(range(1, 9))
        assert episode["test"]["input"][0][0] == 2
        assert proto.parameter_rival_findings(episode) == []


def test_both_materialized_racket_programs_match_python_and_diverge():
    proto = _prototype()
    grid = proto.make_input(2, variant=91)
    outputs = {}
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for setting in proto.ALLOWED_QUARTER_TURNS:
            actual = proto.apply_racket(
                bridge, proto.program_for(setting), grid
            )
            expected = proto.apply_python(grid, setting)
            assert actual == expected
            outputs[setting] = actual
    finally:
        bridge.shutdown()
    assert outputs["clockwise"] != outputs["counterclockwise"]


def test_racket_application_does_not_require_staged_scripts_namespace(monkeypatch):
    proto = _prototype()
    import builtins

    real_import = builtins.__import__

    def reject_scripts(name, *args, **kwargs):
        if name == "scripts" or name.startswith("scripts."):
            raise ModuleNotFoundError("scripts namespace intentionally unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", reject_scripts)
    grid = proto.make_input(2, variant=107)
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        assert proto.apply_racket(
            bridge, proto.program_for("clockwise"), grid
        ) == proto.apply_python(grid, "clockwise")
    finally:
        bridge.shutdown()
