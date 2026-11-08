"""Prototype-only tests for the proposed scale-factor rule family.

These do not alter or approve the selected canonical rule.  Racket execution is
retained separately under WORK/checks/parametric/.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path


PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)
SPEC = importlib.util.spec_from_file_location("upscale_parametric_prototype", PROTOTYPE_PATH)
assert SPEC and SPEC.loader
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)


def test_parameter_contract_and_default_preserve_canonical_rule():
    assert prototype.ALLOWED_SCALE_FACTORS == (2, 3)
    assert prototype.DEFAULT_SCALE_FACTOR == 2
    assert prototype.choose_scale_factor(0) == 2
    assert prototype.choose_scale_factor(1) == 3
    assert prototype.choose_scale_factor(2) == 2


def test_episode_uses_one_parameter_and_demos_refute_the_alternative():
    for scale in prototype.ALLOWED_SCALE_FACTORS:
        episode = prototype.build_episode(seed=17, scale_factor=scale)
        assert episode["parameter"] == {"scale_factor": scale}
        assert len(episode["train"]) == 2
        assert len(episode["test"]) == 1
        alternative = next(v for v in prototype.ALLOWED_SCALE_FACTORS if v != scale)
        for pair in episode["train"]:
            assert pair["output"] == prototype.python_upscale(pair["input"], scale)
            assert pair["output"] != prototype.python_upscale(pair["input"], alternative)
        query = episode["test"][0]
        assert query["output"] == prototype.python_upscale(query["input"], scale)


def test_public_challenge_hides_parameter_and_query_answer():
    episode = prototype.build_episode(seed=23, scale_factor=3)
    public = prototype.public_challenge(episode)
    assert "parameter" not in public
    assert all("output" in pair for pair in public["train"])
    assert public["test"] and "output" not in public["test"][0]


def test_materialized_racket_programs_are_exact_and_setting_specific():
    p2 = prototype.racket_program(2)
    p3 = prototype.racket_program(3)
    assert "(define SCALE 2)" in p2
    assert "(define SCALE 3)" in p3
    assert p2 != p3
    assert prototype.racket_sha256(2) != prototype.racket_sha256(3)
