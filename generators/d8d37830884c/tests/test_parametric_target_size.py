"""Focused tests for the isolated target-component-size prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break

TASK_HOME = Path(__file__).resolve().parents[1]
SOURCE = TASK_HOME / "workspace" / "parametric" / "target_size.py"


def load_prototype():
    assert SOURCE.is_file(), "parametric target-size prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("target_size_prototype", SOURCE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_default_setting_is_exact_canonical_rule_and_seeded_choice_is_stable():
    proto = load_prototype()
    assert proto.DEFAULT_TARGET_SIZE == 6
    assert proto.materialize_program(6) == proto.canonical_record()["program_solution"]
    assert len({proto.materialize_program(size) for size in proto.TARGET_SIZES}) == 3
    assert proto.choose_target_size(41, "seeded") == proto.choose_target_size(41, "seeded")
    assert {proto.choose_target_size(seed, "seeded") for seed in range(128)} == set(proto.TARGET_SIZES)


def test_all_settings_execute_identifiable_complete_episodes_in_racket():
    proto = load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        episodes = {
            size: proto.generate_episode(700, target_size=size, bridge=bridge)
            for size in proto.TARGET_SIZES
        }

    common_inputs = [pair["input"] for pair in episodes[6]["train"] + episodes[6]["test"]]
    for size, episode in episodes.items():
        assert episode["parameter"] == {"target_size": size}
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["assessment"]["identified"] is True
        assert episode["assessment"]["query_separates_settings"] is True
        assert [pair["input"] for pair in episode["train"] + episode["test"]] == common_inputs


def test_shared_input_produces_three_distinct_racket_outputs():
    proto = load_prototype()
    from arc_repl.racket_bridge import RacketBridge

    witness = proto.prototype_input(811, 0)
    with RacketBridge(timeout=10, startup_timeout=60) as bridge:
        outputs = {
            size: proto.execute_program(bridge, proto.materialize_program(size), witness)
            for size in proto.TARGET_SIZES
        }
    assert len({json.dumps(output, separators=(",", ":")) for output in outputs.values()}) == 3


def test_evidence_export_keeps_public_challenges_solver_safe(tmp_path):
    proto = load_prototype()
    report = proto.build_evidence(900, tmp_path)
    assert report["status"] == "pass"
    assert report["episodes_identified"] == len(proto.TARGET_SIZES)
    assert report["query_separation_count"] == len(proto.TARGET_SIZES)
    for path in sorted((tmp_path / "public").glob("*.json")):
        payload = json.loads(path.read_text())
        assert set(payload) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in payload["train"])
        assert all(set(pair) == {"input"} for pair in payload["test"])
        text = path.read_text()
        assert "target_size" not in text
        assert "program" not in text
        assert "seed" not in text
