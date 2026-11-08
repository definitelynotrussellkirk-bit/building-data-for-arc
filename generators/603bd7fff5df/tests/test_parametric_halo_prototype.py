from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

GENERATOR_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = GENERATOR_ROOT / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.exists(), "parametric halo prototype is missing"
    spec = importlib.util.spec_from_file_location(
        "review_parametric_603bd7fff5df", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_halo_setting_is_canonical_and_all_programs_are_distinct():
    proto = _load_prototype()
    assert proto.DEFAULT_HALO_DEPTH == 1
    assert proto.HALO_DEPTHS == (0, 1, 2)
    assert proto.program_for(1) == proto.CANONICAL_PROGRAM
    assert len({proto.normalized_program_hash(depth) for depth in proto.HALO_DEPTHS}) == 3


def test_each_episode_holds_one_depth_fixed_and_teaches_every_declared_rival():
    proto = _load_prototype()
    for depth in proto.HALO_DEPTHS:
        episode = proto.build_episode(20261020, halo_depth=depth, n_train=3, n_test=1)
        assert proto.episode_errors(episode) == []
        assert episode["halo_depth"] == depth
        assert episode["program"] == proto.program_for(depth)
        for pair in episode["train"] + episode["test"]:
            outputs = [proto.apply_python(pair["input"], rival) for rival in proto.HALO_DEPTHS]
            assert len({tuple(map(tuple, output)) for output in outputs}) == 3
            assert pair["output"] == proto.apply_python(pair["input"], depth)


def test_public_challenge_omits_hidden_depth_program_and_query_answers():
    proto = _load_prototype()
    episode = proto.build_episode(7, halo_depth=2, n_train=3, n_test=1)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert "halo_depth" not in public
    assert "program" not in public


def test_invalid_halo_settings_reject_loudly():
    proto = _load_prototype()
    for value in (True, -1, 3, 1.0, "1", None):
        with pytest.raises((TypeError, ValueError), match="halo_depth"):
            proto.program_for(value)
