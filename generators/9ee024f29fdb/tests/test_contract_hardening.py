"""Regression tests for request validation and degenerate-input rejection."""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import interior_eight_count, load_generator  # noqa: E402


gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed(value) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(value, 0)


@pytest.mark.parametrize("value", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index(value) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, value)


@pytest.mark.parametrize("value", [True, False, 0, 1.0, "__invalid_difficulty__"])
def test_generate_rejects_invalid_difficulty(value) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(991, 0, difficulty=value)


def test_self_check_rejects_singleton_signal_impostor() -> None:
    grid = [[0] * 5 for _ in range(5)]
    grid[1][1] = 8
    errors = gen.self_check(grid)
    assert errors
    assert any("at least two" in error for error in errors)


def test_low_density_override_still_generates_two_signal_cells() -> None:
    grid = gen.generate(
        991,
        0,
        grid_h=5,
        grid_w=5,
        eight_density=0.10,
        eight_layout="random",
        decoy_palette_size=0,
        lattice_noise=False,
    )
    assert interior_eight_count(grid) >= 2
    assert gen.self_check(grid) == []
