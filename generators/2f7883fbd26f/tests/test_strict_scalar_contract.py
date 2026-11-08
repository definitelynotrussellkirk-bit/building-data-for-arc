"""Regression tests for literal-integer validation at the generator boundary."""
from __future__ import annotations

import importlib

import pytest


TASK_ID = "2f7883fbd26f"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        (axis, value)
        for axis in (
            "grid_h",
            "grid_w",
            "n_target_blocks",
            "n_decoy_blocks",
            "n_singleton_ones",
            "n_singleton_twos",
        )
        for value in (True, False, "1", 1.0, 1.75)
    ],
)
def test_declared_integer_overrides_reject_non_literal_integers(axis, value) -> None:
    with pytest.raises((TypeError, ValueError), match=axis):
        GEN.generate(901, 1, difficulty="hard", **{axis: value})


@pytest.mark.parametrize(
    ("argument", "value"),
    [
        *[("seed", value) for value in (True, False, "1", 1.0, 1.75, -1)],
        *[("sample_index", value) for value in (True, False, "1", 1.0, 1.75, -1)],
    ],
)
def test_public_call_indices_reject_non_literal_or_negative_integers(argument, value) -> None:
    kwargs = {"seed": 991, "sample_index": 0}
    kwargs[argument] = value
    with pytest.raises((TypeError, ValueError), match=argument):
        GEN.generate(**kwargs, difficulty="hard")
