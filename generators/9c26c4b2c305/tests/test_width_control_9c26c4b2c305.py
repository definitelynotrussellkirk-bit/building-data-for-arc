"""Reject silent coercion of the exact width control at the public generator API."""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator


GEN, _, _ = load_selected_generator("9c26c4b2c305", root=find_root(__file__))


@pytest.mark.parametrize("value", [4.0, 4.75, 14.0, 14.75, "4", "14", True, False])
def test_width_rejects_noninteger_requests(value):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(17, 1, difficulty="medium", grid_w=value)


@pytest.mark.parametrize("value", [3, 15])
def test_width_rejects_integer_requests_outside_domain(value):
    with pytest.raises(ValueError):
        GEN.generate(17, 1, difficulty="medium", grid_w=value)


@pytest.mark.parametrize("width", [4, 14])
def test_width_accepts_exact_integer_endpoints(width):
    grid = GEN.generate(17, 1, difficulty="medium", grid_w=width)
    assert len(grid) == 9
    assert all(len(row) == width for row in grid)
    assert GEN.observe_overrides(grid)["grid_w"] == width
    assert GEN.strict_canonical_like(grid) == []


def test_none_width_retains_the_scheduled_default():
    assert GEN.generate(17, 1, difficulty="medium", grid_w=None) == GEN.generate(
        17, 1, difficulty="medium"
    )
