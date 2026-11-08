"""Tests for the separate proposed window-rule prototype, not canonical approval."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


TASK_ID = "2f7883fbd26f"
HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = HOME / "workspace" / "parametric" / "prototype.py"


def _prototype():
    assert PROTOTYPE.is_file(), "task-local parametric prototype must exist"
    spec = importlib.util.spec_from_file_location("window_rule_parametric", PROTOTYPE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_instantiation_is_exact_and_shared_witness_separates_all_settings() -> None:
    proto = _prototype()
    root = find_root(__file__)
    canonical = proto.canonical_program(root)
    assert proto.instantiate(canonical) == canonical

    witness = proto.fixture_inputs(17)[0]
    expected = {
        (2, 1): [[1, 1, 0, 0, 0]],
        (2, 2): [[1, 1, 1, 1, 0]],
        (3, 1): [[0, 0, 0, 0, 0]],
        (3, 2): [[1, 0, 0, 0, 0]],
    }
    with RacketBridge() as bridge:
        outputs = {
            setting: proto.execute(
                witness,
                proto.instantiate(
                    canonical,
                    window_size=setting[0],
                    target_color=setting[1],
                ),
                bridge,
            )
            for setting in proto.SETTINGS
        }
    assert outputs == expected
    assert len({json.dumps(output) for output in outputs.values()}) == len(proto.SETTINGS)


def test_default_program_reproduces_every_canonical_label_in_live_racket() -> None:
    proto = _prototype()
    root = find_root(__file__)
    canonical = proto.canonical_program(root)
    with RacketBridge() as bridge:
        for pair in canonical_pairs(TASK_ID, root=root):
            assert proto.execute(pair["input"], canonical, bridge) == pair["output"]


def test_each_seeded_setting_is_fixed_for_the_episode_and_all_rivals_are_refuted() -> None:
    proto = _prototype()
    root = find_root(__file__)
    canonical = proto.canonical_program(root)
    with RacketBridge() as bridge:
        for setting in proto.SETTINGS:
            seed = proto.first_seed_for_setting(setting)
            episode = proto.generate_episode(seed, canonical=canonical, bridge=bridge)
            assert (episode["parameters"]["window_size"], episode["parameters"]["target_color"]) == setting
            assert len(episode["train"]) == 3
            assert len(episode["test"]) == 1
            assert episode["demonstrations_refute"] == [
                {"window_size": rival[0], "target_color": rival[1]}
                for rival in proto.SETTINGS
                if rival != setting
            ]
            assert all(rival["status"] == "distinguished" for rival in episode["rivals"])
            assert all(rival["demo_differences"] for rival in episode["rivals"])
            assert all(rival["query_differs"] for rival in episode["rivals"])


def test_public_challenge_masks_rule_parameters_program_and_query_outputs() -> None:
    proto = _prototype()
    root = find_root(__file__)
    canonical = proto.canonical_program(root)
    with RacketBridge() as bridge:
        episode = proto.generate_episode(0, canonical=canonical, bridge=bridge)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public)
    assert "parameters" not in serialized
    assert "program" not in serialized


def test_invalid_parameters_are_rejected_before_program_generation() -> None:
    proto = _prototype()
    canonical = proto.canonical_program(find_root(__file__))
    with pytest.raises(ValueError, match="window_size"):
        proto.instantiate(canonical, window_size=4)
    with pytest.raises(ValueError, match="target_color"):
        proto.instantiate(canonical, target_color=3)
    with pytest.raises(ValueError, match="setting"):
        proto.first_seed_for_setting((4, 1))


def test_cli_materializes_hash_bound_complete_public_and_private_evidence(tmp_path: Path) -> None:
    proto = _prototype()
    out = tmp_path / "parametric-evidence"
    completed = subprocess.run(
        [sys.executable, str(PROTOTYPE), "--out", str(out)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout

    report = json.loads((out / "report.json").read_text())
    assert report["status"] == "prototype"
    assert report["task_id"] == TASK_ID
    assert report["complete_episodes"] == len(proto.SETTINGS) == 4
    assert report["default_program_exact"] is True
    assert report["all_labels_and_rivals_executed_in_racket"] is True
    assert report["all_demonstrations_refute_other_declared_settings"] is True

    seen = set()
    for index in range(len(proto.SETTINGS)):
        public = json.loads((out / "public" / f"episode-{index}.json").read_text())
        private = json.loads((out / "private" / f"episode-{index}.json").read_text())
        program_path = out / "private" / f"episode-{index}.rkt"
        program = program_path.read_text()
        assert public == proto.public_challenge(private)
        assert all("output" not in pair for pair in public["test"])
        assert hashlib.sha256(program.encode()).hexdigest() == private["program_sha256"]
        assert program == private["program"]
        seen.add((private["parameters"]["window_size"], private["parameters"]["target_color"]))
    assert seen == set(proto.SETTINGS)

    witness = json.loads((out / "private" / "witness.json").read_text())
    assert len({json.dumps(value) for value in witness["outputs"].values()}) == len(proto.SETTINGS)
