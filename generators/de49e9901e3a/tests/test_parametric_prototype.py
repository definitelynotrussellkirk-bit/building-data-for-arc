from __future__ import annotations

import importlib.util
import pytest

from reviewer_support import find_root


TASK_ID = "de49e9901e3a"
ROOT = find_root(__file__)
PROTOTYPE_PATH = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


def _load_prototype():
    assert PROTOTYPE_PATH.exists(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("de49_parametric_prototype", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parameter_contract_has_canonical_default_and_deterministic_episode_choice():
    proto = _load_prototype()
    assert proto.PARAMETER_NAME == "eligible_objects"
    assert proto.ALLOWED_SETTINGS == ("all", "cross_only")
    assert proto.DEFAULT_SETTING == "all"
    assert proto.choose_setting(123456) == proto.choose_setting(123456)
    assert proto.choose_setting(123456) in proto.ALLOWED_SETTINGS

    for invalid in (None, True, 1, "unknown"):
        with pytest.raises((TypeError, ValueError)):
            proto.build_episode(0, setting=invalid)


def test_each_setting_is_fixed_per_episode_and_training_pairs_distinguish_it():
    proto = _load_prototype()
    episodes = {
        setting: proto.build_episode(20261019, setting=setting)
        for setting in proto.ALLOWED_SETTINGS
    }

    for setting, episode in episodes.items():
        assert episode["meta"]["eligible_objects"] == setting
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == proto.apply_python(pair["input"], setting)

    all_episode = episodes["all"]
    cross_episode = episodes["cross_only"]
    assert [pair["input"] for pair in all_episode["train"]] == [
        pair["input"] for pair in cross_episode["train"]
    ]
    assert all_episode["test"][0]["input"] == cross_episode["test"][0]["input"]
    assert any(
        left["output"] != right["output"]
        for left, right in zip(
            all_episode["train"], cross_episode["train"], strict=True
        )
    )
    assert all_episode["test"][0]["output"] != cross_episode["test"][0]["output"]


def test_public_challenge_omits_hidden_parameter_program_and_query_answer():
    proto = _load_prototype()
    episode = proto.build_episode(424242, setting="cross_only")
    challenge = proto.public_challenge(episode)

    assert set(challenge) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
    assert all(set(pair) == {"input"} for pair in challenge["test"])
    serialized = repr(challenge)
    assert "eligible_objects" not in serialized
    assert "cross_only" not in serialized
    assert "rule!" not in serialized
