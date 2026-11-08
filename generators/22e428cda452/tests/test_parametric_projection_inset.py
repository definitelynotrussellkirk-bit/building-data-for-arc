"""Executable checks for the isolated episode-level projection-inset prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from arc_repl.racket_bridge import RacketBridge


HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"


def _prototype():
    assert PROTOTYPE_PATH.is_file(), "projection-inset prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "projection_inset_prototype", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_preserves_canonical_default_and_changes_only_inset_geometry():
    proto = _prototype()
    assert proto.ALLOWED_PROJECTION_INSETS == (1, 2)
    assert proto.DEFAULT_PROJECTION_INSET == 1

    grid = proto.make_input(variant=0)
    canonical = proto.apply_python(grid, 1)
    inset_two = proto.apply_python(grid, 2)
    assert canonical != inset_two
    assert sorted(value for row in canonical for value in row if value != 7) == sorted(
        value for row in inset_two for value in row if value != 7
    )


def test_complete_episode_selects_one_setting_and_refutes_the_other():
    proto = _prototype()
    for setting in proto.ALLOWED_PROJECTION_INSETS:
        episode = proto.build_episode(seed=431, projection_inset=setting)
        assert episode["meta"]["projection_inset"] == setting
        assert episode["meta"]["setting_selected_once"] is True
        assert len(episode["train"]) == 3
        assert set(episode["test"]) == {"input", "output"}
        assert proto.parameter_rival_findings(episode) == []


def test_racket_programs_match_python_and_distinguish_both_settings():
    proto = _prototype()
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for variant in range(4):
            grid = proto.make_input(variant=variant)
            outputs = {}
            for setting in proto.ALLOWED_PROJECTION_INSETS:
                outputs[setting] = proto.apply_racket(
                    bridge, proto.program_for(setting), grid
                )
                assert outputs[setting] == proto.apply_python(grid, setting)
            assert outputs[1] != outputs[2]
    finally:
        bridge.shutdown()


def test_invalid_seed_and_parameter_scalars_are_rejected():
    proto = _prototype()
    for setting in (True, False, 1.0, "1", 0, 3):
        with pytest.raises((TypeError, ValueError)):
            proto.program_for(setting)
    for seed in (True, False, 1.0, "1", -1):
        with pytest.raises((TypeError, ValueError)):
            proto.build_episode(seed)


def test_materialized_evidence_uses_racket_labels_and_masks_query(tmp_path):
    proto = _prototype()
    report = proto.materialize(tmp_path / "evidence", seed_start=431)
    assert report["status"] == "prototype"
    assert report["complete_episodes"] == 2
    assert report["all_labels_executed_in_racket"] is True
    assert report["all_demonstrations_refute_other_setting"] is True
    assert report["all_queries_distinguish_other_setting"] is True

    public_paths = sorted((tmp_path / "evidence" / "public").glob("challenge-*.json"))
    assert len(public_paths) == 2
    for path in public_paths:
        public = json.loads(path.read_text())
        assert proto.public_filename(public) == path.name
        assert len(public["train"]) == 3
        assert set(public["test"]) == {"input"}
        serialized = json.dumps(public)
        assert "projection_inset" not in serialized
        assert "rule!" not in serialized
