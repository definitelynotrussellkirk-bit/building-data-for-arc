"""Regression tests for the separate midpoint-rule parameter prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = HOME / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), (
        "workspace/parametric/prototype.py is required for the proposed "
        "episode-level midpoint-rule extension"
    )
    spec = importlib.util.spec_from_file_location(
        "parametric_midpoint_92f4d4eb0dbb", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_declares_two_bounded_parameters_and_canonical_default():
    proto = _load_prototype()
    assert proto.ALLOWED_SIDES == ("lower", "upper")
    assert proto.ALLOWED_BOUNDARIES == ("strict", "inclusive")
    assert proto.DEFAULT_SIDE == "lower"
    assert proto.DEFAULT_BOUNDARY == "strict"
    assert set(proto.SETTINGS) == {
        ("lower", "strict"),
        ("lower", "inclusive"),
        ("upper", "strict"),
        ("upper", "inclusive"),
    }


@pytest.mark.parametrize(
    "side,boundary",
    [
        ("lower", "strict"),
        ("lower", "inclusive"),
        ("upper", "strict"),
        ("upper", "inclusive"),
    ],
)
def test_program_and_python_mirror_agree_on_declared_setting(side, boundary):
    proto = _load_prototype()
    grid = proto.prototype_input(101, 0)
    outputs = {
        setting: proto.solve(grid, side=setting[0], boundary=setting[1])
        for setting in proto.SETTINGS
    }
    assert len({proto.grid_hash(value) for value in outputs.values()}) == 4
    assert proto.program_for(side, boundary).startswith("(rule!")
    assert proto.solve(grid, side=side, boundary=boundary) == outputs[(side, boundary)]
    if (side, boundary) == (proto.DEFAULT_SIDE, proto.DEFAULT_BOUNDARY):
        assert outputs[(side, boundary)] == proto.canonical_output(grid)


def test_episode_selects_once_and_demonstrations_refute_every_other_setting():
    proto = _load_prototype()
    seen = set()
    for seed in range(4):
        episode = proto.generate_episode(seed)
        setting = (
            episode["meta"]["parameters"]["side"],
            episode["meta"]["parameters"]["boundary"],
        )
        seen.add(setting)
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["meta"]["selection_scope"] == "once_per_episode"
        for pair in [*episode["train"], *episode["test"]]:
            assert pair["output"] == proto.solve(
                deepcopy(pair["input"]), side=setting[0], boundary=setting[1]
            )
        for rival in proto.SETTINGS:
            if rival == setting:
                continue
            assert any(
                proto.solve(
                    deepcopy(pair["input"]), side=rival[0], boundary=rival[1]
                )
                != pair["output"]
                for pair in episode["train"]
            )
    assert seen == set(proto.SETTINGS)


def test_public_challenge_masks_hidden_rule_and_query_answer():
    proto = _load_prototype()
    episode = proto.generate_episode(3)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert public["train"] == episode["train"]
    assert public["test"] == [{"input": episode["test"][0]["input"]}]
    assert "meta" not in public
    assert "program" not in public


@pytest.mark.parametrize(
    "side,boundary",
    [("left", "strict"), ("lower", "closed"), (1, "strict")],
)
def test_rejects_unknown_or_wrong_type_settings(side, boundary):
    proto = _load_prototype()
    with pytest.raises(ValueError):
        proto.program_for(side, boundary)
