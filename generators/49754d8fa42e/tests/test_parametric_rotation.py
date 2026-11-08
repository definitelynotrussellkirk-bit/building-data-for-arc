from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from reviewer_support import find_root

TASK_ID = "49754d8fa42e"
ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
VERIFY_PATH = ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "verify.py"


def _load_prototype():
    assert PROTOTYPE_PATH.exists(), "parametric rotation prototype has not been implemented"
    name = "parametric_rotation_49754d8fa42e"
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("task_id") == TASK_ID:
            return record["program_solution"]
    raise AssertionError("canonical record missing")


def test_parameter_contract_and_exact_canonical_default():
    proto = _load_prototype()
    assert proto.PARAMETER_NAME == "quarter_turns_clockwise"
    assert proto.ALLOWED_SETTINGS == (0, 1, 2, 3)
    assert proto.DEFAULT_SETTING == 0
    assert proto.program_for(0) == _canonical_program()
    assert len({proto.program_for(turns) for turns in proto.ALLOWED_SETTINGS}) == 4
    assert all(proto.program_for(turns).startswith("(rule!") for turns in proto.ALLOWED_SETTINGS)

    assert proto.choose_setting(12345) == proto.choose_setting(12345)
    assert proto.choose_setting(12345) in proto.ALLOWED_SETTINGS
    for bad_seed in (True, 1.5, "1", None):
        with pytest.raises((TypeError, ValueError)):
            proto.build_episode(bad_seed)
    for invalid in (None, True, -1, 4, 1.5, "1"):
        with pytest.raises((TypeError, ValueError)):
            proto.build_episode(0, setting=invalid)


def test_complete_episodes_fix_one_setting_and_distinguish_every_rotation():
    proto = _load_prototype()
    episodes = {
        turns: proto.build_episode(20261020, setting=turns)
        for turns in proto.ALLOWED_SETTINGS
    }
    baseline = episodes[0]
    baseline_inputs = [pair["input"] for pair in baseline["train"] + baseline["test"]]

    assert len(baseline["train"]) == 5
    assert len(baseline["test"]) == 2
    assert {proto.mode_color(pair["input"]) for pair in baseline["train"]} == {1, 2, 3}
    assert all(proto.mode_color(pair["input"]) in (2, 3) for pair in baseline["test"])

    for turns, episode in episodes.items():
        assert episode["meta"][proto.PARAMETER_NAME] == turns
        assert [pair["input"] for pair in episode["train"] + episode["test"]] == baseline_inputs
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == proto.apply_python(pair["input"], turns)
        for rival in proto.ALLOWED_SETTINGS:
            if rival == turns:
                continue
            assert any(
                pair["output"] != proto.apply_python(pair["input"], rival)
                for pair in episode["train"]
            )
            assert all(
                pair["output"] != proto.apply_python(pair["input"], rival)
                for pair in episode["test"]
            )


def test_public_challenge_omits_hidden_rule_and_query_answers():
    proto = _load_prototype()
    episode = proto.build_episode(314159, setting=3)
    challenge = proto.public_challenge(episode)
    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    serialized = json.dumps(challenge, sort_keys=True)
    assert proto.PARAMETER_NAME not in serialized
    assert "rule!" not in serialized
    assert "program" not in serialized


def test_retained_verifier_executes_all_racket_programs_and_all_rivals(tmp_path):
    assert VERIFY_PATH.exists(), "parametric Racket verifier has not been implemented"
    out_path = tmp_path / "verification.json"
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "src"), str(ROOT / "shared" / "runtime"), env.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    completed = subprocess.run(
        [sys.executable, str(VERIFY_PATH), "--out", str(out_path)],
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads(out_path.read_text(encoding="utf-8"))
    assert report["status"] == "passed"
    assert report["canonical_default_exact_match"] is True
    assert set(map(int, report["programs"])) == {0, 1, 2, 3}
    assert set(map(int, report["episodes"])) == {0, 1, 2, 3}
    for episode in report["episodes"].values():
        assert set(map(int, episode["train_disagreements_by_rival"])) == (
            {0, 1, 2, 3} - {episode["selected_setting"]}
        )
        assert all(episode["query_disagrees_by_rival"].values())
