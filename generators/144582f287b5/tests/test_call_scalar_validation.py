"""Regression tests for strict public call-scalar validation.

Kept separate from the packet's frozen baseline fixture.
"""
from __future__ import annotations

import importlib

import pytest


MODULE = importlib.import_module("puzzle_generators.per_puzzle.144582f287b5.generator")


def test_seed_must_be_an_exact_integer():
    for bad in (True, False, 1.0, 1.75, "1"):
        with pytest.raises((TypeError, ValueError)):
            MODULE.generate(bad, 0)
        with pytest.raises((TypeError, ValueError)):
            MODULE.schedule_profile(bad, 0)


def test_sample_index_must_be_a_nonnegative_exact_integer():
    for bad in (True, False, 1.0, 1.75, "1", -1):
        with pytest.raises((TypeError, ValueError)):
            MODULE.generate(0, bad)
        with pytest.raises((TypeError, ValueError)):
            MODULE.schedule_profile(0, bad)
