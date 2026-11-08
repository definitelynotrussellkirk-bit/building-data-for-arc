"""Prototype-only tests for the proposed row-wave orientation family.

The prototype is deliberately separate from the selected canonical generator and
Racket authority. Racket execution evidence is retained under WORK/checks/parametric/.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "8a3fe170ed27"
PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)
assert PROTOTYPE_PATH.is_file(), "parametric wave-orientation prototype is missing"
SPEC = importlib.util.spec_from_file_location("row_wave_parametric_prototype", PROTOTYPE_PATH)
assert SPEC and SPEC.loader
prototype = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prototype)


def test_parameter_contract_and_default_preserve_canonical_orientation():
    assert prototype.ALLOWED_ORIENTATIONS == ("left_first", "right_first")
    assert prototype.DEFAULT_ORIENTATION == "left_first"
    assert prototype.choose_orientation(0) == "left_first"
    assert prototype.choose_orientation(1) == "right_first"
    assert prototype.choose_orientation(2) == "left_first"


@pytest.mark.parametrize("bad", [True, 0, "mirror", None])
def test_invalid_orientation_is_rejected(bad):
    with pytest.raises(ValueError, match="wave_orientation"):
        prototype.python_row_wave([[0, 1, 0], [0, 1, 0]], bad)


def test_default_python_rule_matches_every_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert prototype.python_row_wave(
            pair["input"], prototype.DEFAULT_ORIENTATION
        ) == pair["output"]


def test_episode_uses_one_orientation_and_every_demo_refutes_the_alternative():
    for orientation in prototype.ALLOWED_ORIENTATIONS:
        episode = prototype.build_episode(seed=17, wave_orientation=orientation)
        assert episode["parameter"] == {"wave_orientation": orientation}
        assert len(episode["train"]) == 4
        assert len(episode["test"]) == 1
        alternative = next(
            value for value in prototype.ALLOWED_ORIENTATIONS if value != orientation
        )
        for pair in episode["train"]:
            expected = prototype.python_row_wave(pair["input"], orientation)
            assert pair["output"] == expected
            assert expected != prototype.python_row_wave(pair["input"], alternative)
        query = episode["test"][0]
        assert query["output"] == prototype.python_row_wave(
            query["input"], orientation
        )


def test_public_challenge_hides_parameter_and_query_answer():
    episode = prototype.build_episode(seed=23, wave_orientation="right_first")
    public = prototype.public_challenge(episode)
    assert "parameter" not in public
    assert all("output" in pair for pair in public["train"])
    assert public["test"] and "output" not in public["test"][0]


def test_materialized_racket_programs_are_exact_and_setting_specific():
    left = prototype.racket_program("left_first")
    right = prototype.racket_program("right_first")
    assert "(define FIRST-SHIFT -1)" in left
    assert "(define FIRST-SHIFT 1)" in right
    assert left != right
    assert prototype.racket_sha256("left_first") != prototype.racket_sha256(
        "right_first"
    )
    for orientation in prototype.ALLOWED_ORIENTATIONS:
        path = prototype.rule_path(orientation)
        assert path.read_text(encoding="utf-8") == prototype.racket_program(orientation)
