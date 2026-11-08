"""Regressions added by review-f51be7ab3aae2421."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_generator():
    source = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("review_084223_generator", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def test_negative_sample_index_is_rejected_before_any_draw():
    with pytest.raises(ValueError, match="sample_index.*nonnegative"):
        gen.generate(123, -1, difficulty="hard")


def _load_prototype():
    source = Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
    assert source.is_file(), "parametric arm-turn prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("review_084223_parametric", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parametric_arm_turn_is_fixed_per_episode_and_distinguishable():
    prototype = _load_prototype()
    assert prototype.ALLOWED_ARM_TURNS == ("half_turn", "preserve")
    assert prototype.DEFAULT_ARM_TURN == "half_turn"
    for setting in prototype.ALLOWED_ARM_TURNS:
        episode = prototype.build_episode(seed=7319, arm_turn=setting)
        assert episode["meta"]["arm_turn"] == setting
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        rival = next(value for value in prototype.ALLOWED_ARM_TURNS if value != setting)
        assert all(
            prototype.apply_python(pair["input"], rival) != pair["output"]
            for pair in episode["train"]
        )
        public = prototype.public_challenge(episode)
        assert "meta" not in public
        assert all("output" not in pair for pair in public["test"])


def test_parametric_racket_programs_are_distinct_and_default_is_declared_canonical():
    prototype = _load_prototype()
    programs = {setting: prototype.program_for(setting)
                for setting in prototype.ALLOWED_ARM_TURNS}
    assert programs["half_turn"] != programs["preserve"]
    assert all(program.startswith("(rule!") for program in programs.values())
    assert prototype.program_sha256("half_turn") != prototype.program_sha256("preserve")


@pytest.mark.parametrize("seed", [True, 1.0, "1", None])
def test_seed_requires_a_literal_integer(seed):
    with pytest.raises(TypeError, match="seed.*integer"):
        gen.generate(seed, 0, difficulty="hard")
