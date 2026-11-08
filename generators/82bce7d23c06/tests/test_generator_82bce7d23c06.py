from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "82bce7d23c06"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK, root=ROOT)


def _nz(grid):
    return sum(value != 0 for value in grid[0])


def test_all_canonical_pairs_are_accepted_and_match_rule_mirror():
    pairs = canonical_pairs(TASK, root=ROOT, labeled_only=True)
    assert len(pairs) == 6
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("layout", GEN.NZ_LAYOUTS)
@pytest.mark.parametrize("bias", GEN.NZ_BIASES)
def test_every_layout_bias_pair_returns_exact_requested_nonzero_count(layout, bias):
    grid = GEN.generate(
        71,
        3,
        grid_w=6,
        nz_count=5,
        nz_layout=layout,
        nz_position_bias=bias,
        nz_color_dist="all_distinct",
    )
    assert GEN.self_check(grid) == []
    assert len(grid[0]) == 6
    assert _nz(grid) == 5


def test_all_zero_and_non_row_inputs_fail_closed():
    assert GEN.self_check([[0, 0, 0, 0, 0]])
    assert GEN.self_check([[1, 0], [0, 1]])
    assert GEN.self_check([])


def test_nz_override_uses_typed_validity_gate_instead_of_clamping():
    with pytest.raises(ValueError):
        GEN.generate(1, 0, grid_w=6, nz_count=0)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, grid_w=6, nz_count=6)
    with pytest.raises(TypeError):
        GEN.generate(1, 0, grid_w=6, nz_count=True)


def test_declared_width_boundaries_and_determinism():
    for width in (2, 10):
        max_nz = min(width, 7, 30 // width)
        grid = GEN.generate(80 + width, 1, grid_w=width, nz_count=max_nz)
        assert len(grid[0]) == width
        assert _nz(grid) == max_nz
        assert GEN.self_check(grid) == []
    kwargs = dict(grid_w=6, nz_count=5, nz_layout="regular_spaced", nz_position_bias="left")
    first = GEN.generate(91, 2, **kwargs)
    second = GEN.generate(91, 2, **kwargs)
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9
    assert GEN.generate(91, 2, **kwargs) == second
