"""Contract for the task-local rank-order parametric prototype."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fe947_parametric", HERE / "prototype.py")
assert SPEC and SPEC.loader
PROTO = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTO)


def test_parameter_contract_and_canonical_default():
    assert PROTO.PARAMETER_NAME == "rank_order"
    assert PROTO.SETTINGS == ("largest_first", "smallest_first")
    assert PROTO.DEFAULT_SETTING == "largest_first"
    assert PROTO.instantiate_rule("largest_first") == PROTO.canonical_rule_source()
    assert PROTO.instantiate_rule("smallest_first") != PROTO.instantiate_rule("largest_first")


def test_each_episode_pins_one_setting_and_demos_distinguish_settings():
    for setting in PROTO.SETTINGS:
        episode = PROTO.make_episode(seed=700, rank_order=setting)
        assert episode["parameter"] == {"rank_order": setting}
        assert len(episode["train"]) == 3 and len(episode["test"]) == 1
        expected = [PROTO.solve_python(pair["input"], rank_order=setting)
                    for pair in episode["train"] + episode["test"]]
        actual = [pair["output"] for pair in episode["train"] + episode["test"]]
        assert actual == expected
        other = next(value for value in PROTO.SETTINGS if value != setting)
        assert any(PROTO.solve_python(pair["input"], rank_order=other) != pair["output"]
                   for pair in episode["train"])


def test_invalid_setting_is_rejected():
    with pytest.raises(ValueError):
        PROTO.instantiate_rule("middle_first")
    with pytest.raises(ValueError):
        PROTO.make_episode(seed=1, rank_order="middle_first")


def test_racket_matches_python_when_runtime_is_available():
    status = PROTO.racket_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    for setting in PROTO.SETTINGS:
        episode = PROTO.make_episode(seed=808, rank_order=setting)
        grids = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert PROTO.racket_outputs(grids, rank_order=setting) == [
            PROTO.solve_python(grid, rank_order=setting) for grid in grids
        ]
