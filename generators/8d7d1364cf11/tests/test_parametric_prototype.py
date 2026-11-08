"""Focused contract tests for the proposed episode-level rule prototype."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "8d7d1364cf11"
ROOT = find_root(__file__)
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype module is missing"
    spec = importlib.util.spec_from_file_location("parametric_prototype_8d7d", PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()


def _canonical_program() -> str:
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical program missing")


def test_prototype_declares_two_bounded_episode_constant_parameters():
    proto = _load_prototype()
    assert proto.PARAMETERS == {
        "anchor_mode": ("matching_cell", "template_origin"),
        "canvas_mode": ("clear", "preserve_input"),
    }
    assert proto.DEFAULT_SETTING == "matching_cell__clear"
    assert set(proto.SETTING_IDS) == {
        "matching_cell__clear",
        "matching_cell__preserve_input",
        "template_origin__clear",
        "template_origin__preserve_input",
    }
    assert _normalized_hash(proto.program_for(proto.DEFAULT_SETTING)) == _normalized_hash(
        _canonical_program()
    )
    assert len({_normalized_hash(proto.program_for(setting)) for setting in proto.SETTING_IDS}) == 4
    assert {proto.choose_setting(seed) for seed in range(16)} == set(proto.SETTING_IDS)


def test_each_setting_builds_a_complete_pairwise_distinguishing_episode():
    proto = _load_prototype()
    for setting in proto.SETTING_IDS:
        episode = proto.build_episode(seed=20261019, setting=setting, n_train=3, n_test=1)
        assert episode["setting_id"] == setting
        assert episode["parameters"] == proto.parameters_for(setting)
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["program"] == proto.program_for(setting)
        assert proto.episode_errors(episode) == []
        for pair in episode["train"] + episode["test"]:
            assert proto.apply_python(pair["input"], setting) == pair["output"]
        for pair in episode["train"]:
            expected = pair["output"]
            assert all(
                proto.apply_python(pair["input"], rival) != expected
                for rival in proto.SETTING_IDS
                if rival != setting
            )

        public = proto.public_challenge(episode)
        assert set(public) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert "parameters" not in public and "program" not in public


def test_canonical_setting_preserves_all_canonical_labels():
    proto = _load_prototype()
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    assert all(
        proto.apply_python(pair["input"], proto.DEFAULT_SETTING) == pair["output"]
        for pair in pairs
    )


@pytest.mark.parametrize("bad_seed", [True, 1.0, "1"])
def test_choose_setting_rejects_non_integer_seed(bad_seed):
    proto = _load_prototype()
    with pytest.raises(TypeError):
        proto.choose_setting(bad_seed)


def test_invalid_setting_is_rejected():
    proto = _load_prototype()
    with pytest.raises(ValueError):
        proto.program_for("not-a-setting")
