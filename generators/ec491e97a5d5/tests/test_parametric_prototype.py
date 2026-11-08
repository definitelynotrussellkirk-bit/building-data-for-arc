"""Focused checks for the optional border-thickness prototype."""
from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest


PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)
SPEC = importlib.util.spec_from_file_location("ec491e97a5d5_parametric", PROTOTYPE_PATH)
assert SPEC is not None and SPEC.loader is not None
PROTO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTO)


def all_pairs(episode):
    return episode["train"] + episode["test"]


def test_parameter_is_bounded_and_selected_once_per_episode():
    assert PROTO.ALLOWED_BORDER_THICKNESSES == (1, 2)
    assert PROTO.DEFAULT_BORDER_THICKNESS == 1
    assert PROTO.choose_border_thickness(0) == 1
    assert PROTO.choose_border_thickness(1) == 2
    for seed in range(4):
        episode = PROTO.build_episode(seed)
        chosen = episode["parameter"]["border_thickness"]
        assert chosen == PROTO.choose_border_thickness(seed)
        assert all(pair["border_thickness"] == chosen for pair in all_pairs(episode))


@pytest.mark.parametrize("thickness", [1, 2])
def test_every_demo_distinguishes_the_other_thickness(thickness):
    alternative = 3 - thickness
    episode = PROTO.build_episode(seed=17, border_thickness=thickness)
    for pair in episode["train"]:
        assert pair["output"] == PROTO.python_hollow(pair["input"], thickness)
        assert pair["output"] != PROTO.python_hollow(pair["input"], alternative)


def test_public_challenge_hides_parameter_and_query_answer():
    public = PROTO.public_challenge(PROTO.build_episode(17, border_thickness=2))
    assert "parameter" not in public
    assert all("output" in pair for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])


@pytest.mark.skipif(shutil.which("racket") is None, reason="run through bundled Racket wrapper")
@pytest.mark.parametrize("thickness", [1, 2])
def test_materialized_racket_matches_python_on_complete_episode(thickness):
    PROTO.materialize_rules()
    episode = PROTO.build_episode(seed=17, border_thickness=thickness)
    for pair in all_pairs(episode):
        assert PROTO.run_racket(thickness, pair["input"]) == pair["output"]
