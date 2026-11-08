"""Focused tests for the isolated half-bar rule-parameter prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import intended_output, load_generator  # noqa: E402

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status

PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"
GENERATOR = load_generator()


def _prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "task_1a92a12bac06_parametric_prototype", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_keeps_canonical_default_and_rejects_bad_values():
    proto = _prototype()
    assert proto.ALLOWED_FILL_SIDES == ("bottom", "top")
    assert proto.ALLOWED_ROUNDINGS == ("floor", "ceil")
    assert proto.DEFAULT_FILL_SIDE == "bottom"
    assert proto.DEFAULT_ROUNDING == "floor"
    assert proto.ALL_SETTINGS == (
        ("bottom", "floor"),
        ("bottom", "ceil"),
        ("top", "floor"),
        ("top", "ceil"),
    )
    with pytest.raises(ValueError):
        proto.program_for("left", "floor")
    with pytest.raises(ValueError):
        proto.program_for("bottom", "nearest")
    with pytest.raises(TypeError):
        proto.choose_setting(True)


def test_canonical_default_python_mirror_matches_existing_rule():
    proto = _prototype()
    for sample_index in range(8):
        grid = GENERATOR.generate(141, sample_index, difficulty="medium")
        assert proto.apply_python(grid, "bottom", "floor") == intended_output(grid)


def test_each_setting_is_episode_fixed_and_all_parameter_rivals_are_taught():
    proto = _prototype()
    for fill_side, rounding in proto.ALL_SETTINGS:
        episode = proto.build_episode(
            seed=9100,
            fill_side=fill_side,
            rounding=rounding,
        )
        assert episode["meta"]["fill_side"] == fill_side
        assert episode["meta"]["rounding"] == rounding
        assert len(episode["train"]) == 3
        assert "output" in episode["test"]
        assert proto.parameter_rival_findings(episode) == []
        for pair in episode["train"] + [episode["test"]]:
            assert GENERATOR.self_check(pair["input"]) == []


def test_all_materialized_racket_settings_match_python_and_diverge_pairwise():
    if not racket_runtime_status()["available"]:
        pytest.skip(racket_runtime_status()["reason"])
    proto = _prototype()
    grid = GENERATOR.generate(317, 2, difficulty="hard")
    outputs = {}
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for setting in proto.ALL_SETTINGS:
            actual = proto.apply_racket(bridge, proto.program_for(*setting), grid)
            assert actual == proto.apply_python(grid, *setting)
            outputs[setting] = actual
    finally:
        bridge.shutdown()
    assert len({json.dumps(value) for value in outputs.values()}) == len(proto.ALL_SETTINGS)
    assert outputs[("bottom", "floor")] == intended_output(grid)


def test_materialize_records_hidden_racket_evidence_and_public_view_is_safe(tmp_path):
    if not racket_runtime_status()["available"]:
        pytest.skip(racket_runtime_status()["reason"])
    proto = _prototype()
    report = proto.materialize(tmp_path, seed_start=9200)
    assert report["status"] == "prototype"
    assert len(report["episodes"]) == len(proto.ALL_SETTINGS)
    assert {tuple(row["setting"][key] for key in ("fill_side", "rounding")) for row in report["episodes"]} == set(proto.ALL_SETTINGS)
    assert all(row["parameter_rival_findings"] == [] for row in report["episodes"])
    assert all(row["program"] and row["program_sha256"] for row in report["episodes"])

    for row in report["episodes"]:
        public = json.loads((tmp_path / row["public_challenge"]).read_text())
        assert set(public) == {"schema", "train", "test"}
        assert set(public["test"]) == {"input"}
        assert "meta" not in public
        assert "program" not in public
