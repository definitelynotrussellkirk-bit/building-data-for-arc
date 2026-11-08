"""Minimal counterexamples for the baseline generator's occupancy repair."""
from reviewer_support import find_root, load_selected_generator
import pytest


def generator():
    return load_selected_generator("af0ae766e671", root=find_root(__file__))[0]


def states(grid):
    half = len(grid) // 2
    return [(int(a != 0), int(b != 0))
            for upper, lower in zip(grid[:half], grid[half:])
            for a, b in zip(upper, lower)]


def test_fully_filled_proposals_become_complete_truth_table():
    module = generator()
    grid = module.generate(0, 0, half_h=3, grid_w=3,
                           panel_pattern="random", top_density=1, bot_density=1)
    assert set(states(grid)) == {(0, 0), (0, 1), (1, 0), (1, 1)}
    assert module.self_check(grid) == []


def test_border_respects_xor_lower_bound():
    grid = generator().generate(0, 0, half_h=3, grid_w=3,
                                panel_pattern="border", xor_target=2)
    assert sum(a != b for a, b in states(grid)) >= 2


def test_complementary_proposals_preserve_requested_panel_colors():
    grid = generator().generate(0, 0, half_h=3, grid_w=3,
                                panel_pattern="random", top_density=0,
                                bot_density=1, top_color=2, bot_color=4)
    assert {v for row in grid[:3] for v in row} == {0, 2}
    assert {v for row in grid[3:] for v in row} == {0, 4}


def test_structured_pattern_teaches_both_directions():
    grid = generator().generate(0, 0, panel_pattern="stripes")
    assert (0, 1) in states(grid)
    assert (1, 0) in states(grid)


@pytest.mark.parametrize("axis", ("top_density", "bot_density"))
def test_huge_invalid_density_raises_contract_error(axis):
    with pytest.raises(ValueError, match=axis):
        generator().generate(0, 0, **{axis: 10**1000})


@pytest.mark.parametrize("seed", (2**32, 172431030768117, 2**256))
def test_native_seed_identity_has_no_uint32_limit(seed):
    # The profile-floor sampler uses 48-bit hash-derived seeds. GenCtx hashes
    # the integer identity without imposing a 32- or 64-bit upper bound.
    module = generator()
    grid = module.generate(seed, 6516, difficulty="easy")
    assert module.self_check(grid) == []
    assert module.generate(seed, 6516, difficulty="easy") == grid
