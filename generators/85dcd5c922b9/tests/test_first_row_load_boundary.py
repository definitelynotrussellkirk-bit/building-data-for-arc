"""The exact public row-load control must not silently coerce requests."""
from itertools import product

import pytest

from reviewer_support import find_root, load_selected_generator


GEN, _, _ = load_selected_generator("85dcd5c922b9", root=find_root(__file__))


@pytest.mark.parametrize("value", [2.75, 3.99, 2.0, "2", "3", True, False])
def test_first_row_load_rejects_noninteger_requests(value):
    with pytest.raises((TypeError, ValueError), match="first_row_load"):
        GEN.generate(27, 0, first_row_load=value, blank_row="last")


@pytest.mark.parametrize("value", [1, 4])
def test_first_row_load_rejects_out_of_range_integers(value):
    with pytest.raises(ValueError, match="first_row_load"):
        GEN.generate(27, 0, first_row_load=value)


def test_integer_boundaries_remain_exact_across_scheduled_profiles():
    for index, load, blank in product(range(3), (2, 3), ("none", "last")):
        grid = GEN.generate(27, index, first_row_load=load, blank_row=blank)
        assert sum(value != 0 for value in grid[0]) == load
        assert bool(any(grid[-1])) == (blank == "none")
        assert GEN.self_check(grid) == []


def test_none_preserves_the_no_override_convention():
    for index in range(3):
        assert GEN.generate(27, index, first_row_load=None) == GEN.generate(27, index)
