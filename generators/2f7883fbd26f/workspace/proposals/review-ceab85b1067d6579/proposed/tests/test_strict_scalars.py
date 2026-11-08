from __future__ import annotations

import importlib

import pytest


TASK_ID = "2f7883fbd26f"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def test_replay_keys_reject_coercible_scalars() -> None:
    invalid_scalars = (True, False, 1.0, 1.75, "1")

    for value in invalid_scalars:
        with pytest.raises(TypeError, match="seed"):
            GEN.generate(value, 0, difficulty="easy")
        with pytest.raises(TypeError, match="seed"):
            GEN.schedule_profile(value, 0, "easy")

    for value in invalid_scalars:
        with pytest.raises(TypeError, match="sample_index"):
            GEN.generate(991, value, difficulty="easy")
        with pytest.raises(TypeError, match="sample_index"):
            GEN.schedule_profile(991, value, "easy")

    with pytest.raises(ValueError, match="sample_index.*nonnegative"):
        GEN.generate(991, -1, difficulty="easy")
    with pytest.raises(ValueError, match="sample_index.*nonnegative"):
        GEN.schedule_profile(991, -1, "easy")


def test_declared_integer_axes_reject_coercible_scalars() -> None:
    controls = {
        "grid_h": 9,
        "grid_w": 9,
        "n_target_blocks": 2,
        "n_decoy_blocks": 2,
        "n_singleton_ones": 2,
        "n_singleton_twos": 1,
    }
    for axis, control in controls.items():
        for value in (True, False, str(control), float(control), control + 0.75):
            with pytest.raises(TypeError, match=axis):
                GEN.generate(991, 0, difficulty="easy", **{axis: value})
