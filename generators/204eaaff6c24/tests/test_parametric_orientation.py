"""Focused tests for the isolated output-orientation prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break

TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = TASK_HOME / "workspace" / "parametric" / "output_orientation.py"


def load_prototype():
    assert SOURCE.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("output_orientation_prototype", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_default_setting_is_exact_canonical_rule_and_seeded_choice_is_episode_stable():
    proto = load_prototype()
    assert proto.DEFAULT_ORIENTATION == "horizontal"
    assert proto.materialize_program("horizontal") == proto.canonical_record()["program_solution"]
    assert proto.materialize_program("vertical") != proto.materialize_program("horizontal")
    assert proto.choose_orientation(41, "seeded") == proto.choose_orientation(41, "seeded")
    assert {proto.choose_orientation(seed, "seeded") for seed in range(32)} == set(proto.ORIENTATIONS)


def test_both_settings_execute_identifiable_complete_episodes_in_racket():
    proto = load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        for index, orientation in enumerate(proto.ORIENTATIONS):
            episode = proto.generate_episode(700 + index, orientation=orientation, bridge=bridge)
            assert episode["parameter"] == {"output_orientation": orientation}
            assert len(episode["train"]) == 3
            assert len(episode["test"]) == 1
            assert episode["assessment"]["identified"] is True
            assert episode["assessment"]["query_separates_settings"] is True
            assert all(len(pair["output"]) != len(pair["output"][0]) for pair in episode["train"])


def test_shared_witness_outputs_differ_by_orientation():
    proto = load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    witness = [[0, 4, 0], [4, 0, 0], [0, 0, 0]]
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        horizontal = proto.execute_program(bridge, proto.materialize_program("horizontal"), witness)
        vertical = proto.execute_program(bridge, proto.materialize_program("vertical"), witness)
    assert horizontal == [[4, 4]]
    assert vertical == [[4], [4]]


def test_evidence_export_keeps_public_challenges_solver_safe(tmp_path):
    proto = load_prototype()
    report = proto.build_evidence(900, tmp_path)
    assert report["status"] == "pass"
    assert report["episodes_identified"] == 2
    for path in sorted((tmp_path / "public").glob("*.json")):
        payload = json.loads(path.read_text())
        assert set(payload) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in payload["train"])
        assert all(set(pair) == {"input"} for pair in payload["test"])
        text = path.read_text()
        assert "output_orientation" not in text
        assert "program" not in text
        assert "seed" not in text
