"""Regression tests resolving the retained public-identifier/emission-order hold."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import public_challenge_bytes, public_challenge_id

TASK_ID = "f13d23b71bd4"
ROOT = Path(__file__).resolve().parents[3]
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    return _load(PARAMETRIC / "family.py", "_f13_public_family")


@pytest.fixture(scope="module")
def writer():
    return _load(PARAMETRIC / "public_batch.py", "_f13_public_writer")


def test_public_artifact_identity_uses_only_visible_bytes(family, writer):
    episode = family.generate(7, {"fall_policy": "signal_ranked"}, 3, 4)
    artifact = writer.public_artifact(episode, 2)
    public = family.public_turn(episode, 2)

    assert artifact["bytes"] == public_challenge_bytes(public)
    assert artifact["id"] == public_challenge_id(public)
    assert artifact["filename"] == f"challenge-{artifact['id']}.json"

    private_change = copy.deepcopy(episode)
    private_change["seed"] = 999
    private_change["settings"] = {"fall_policy": "all_large"}
    private_change["program_solution"] = "private replacement"
    private_change["test"][2]["output"] = [[9]]
    assert writer.public_artifact(private_change, 2) == artifact

    visible_change = copy.deepcopy(episode)
    visible_change["test"][2]["input"][0][0] = 9
    assert writer.public_artifact(visible_change, 2)["id"] != artifact["id"]


def test_batch_is_planned_then_written_in_visible_filename_order(tmp_path, family, writer):
    episodes = [
        family.generate(19, {"fall_policy": "signal_ranked"}, 3, 4),
        family.generate(3, {"fall_policy": "all_large"}, 3, 4),
    ]
    requests = [(episodes[0], 3), (episodes[1], 0), (episodes[0], 1), (episodes[1], 2)]
    expected = [item["filename"] for item in writer.plan_public_batch(requests)]

    out = tmp_path / "public"
    result = writer.write_public_batch(out, reversed(requests))
    observed = [path.name for path in sorted(out.iterdir())]

    assert observed == sorted(expected)
    assert result["filenames"] == sorted(expected)
    for path in out.iterdir():
        challenge = json.loads(path.read_text())
        assert path.name == f"challenge-{public_challenge_id(challenge)}.json"
        assert path.read_bytes() == public_challenge_bytes(challenge)
        assert all(set(pair) == {"input"} for pair in challenge["test"])


def test_duplicate_visible_id_fails_before_public_emission(tmp_path, family, writer):
    episode = family.generate(5, {"fall_policy": "all_large"}, 3, 4)
    out = tmp_path / "public"
    with pytest.raises(ValueError, match="duplicate visible public challenge id"):
        writer.write_public_batch(out, [(episode, 0), (episode, 0)])
    assert not out.exists()
