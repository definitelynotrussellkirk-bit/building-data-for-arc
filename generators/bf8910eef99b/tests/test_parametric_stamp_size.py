"""Focused tests for the isolated stamp-size rule prototype."""
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
SOURCE = TASK_HOME / "workspace" / "parametric" / "stamp_size.py"


def load_prototype():
    assert SOURCE.is_file(), "parametric stamp-size prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("stamp_size_prototype", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_default_setting_is_exact_canonical_rule_and_seeded_choice_is_episode_stable():
    proto = load_prototype()
    assert proto.DEFAULT_STAMP_SIZE == 2
    assert proto.materialize_program(2) == proto.canonical_record()["program_solution"]
    assert proto.materialize_program(1) != proto.materialize_program(2)
    assert proto.choose_stamp_size(41, "seeded") == proto.choose_stamp_size(41, "seeded")
    assert {proto.choose_stamp_size(seed, "seeded") for seed in range(32)} == set(proto.STAMP_SIZES)


def test_both_settings_execute_identifiable_complete_episodes_in_racket():
    proto = load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        small = proto.generate_episode(700, stamp_size=1, bridge=bridge)
        canonical = proto.generate_episode(700, stamp_size=2, bridge=bridge)

    assert small["parameter"] == {"stamp_size": 1}
    assert canonical["parameter"] == {"stamp_size": 2}
    assert len(small["train"]) == len(canonical["train"]) == 3
    assert len(small["test"]) == len(canonical["test"]) == 1
    assert [pair["input"] for pair in small["train"] + small["test"]] == [
        pair["input"] for pair in canonical["train"] + canonical["test"]
    ]
    assert small["assessment"]["identified"] is True
    assert canonical["assessment"]["identified"] is True
    assert small["assessment"]["query_separates_settings"] is True
    assert canonical["assessment"]["query_separates_settings"] is True


def test_evidence_export_keeps_public_challenges_solver_safe(tmp_path):
    proto = load_prototype()
    report = proto.build_evidence(900, tmp_path)
    assert report["status"] == "pass"
    assert report["episodes_identified"] == 2
    assert report["query_separation_count"] == 2
    assert report["witness_outputs_distinct"] is True

    for path in sorted((tmp_path / "public").glob("*.json")):
        payload = json.loads(path.read_text())
        assert set(payload) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in payload["train"])
        assert all(set(pair) == {"input"} for pair in payload["test"])
        text = path.read_text()
        assert "stamp_size" not in text
        assert "program" not in text
        assert "seed" not in text
