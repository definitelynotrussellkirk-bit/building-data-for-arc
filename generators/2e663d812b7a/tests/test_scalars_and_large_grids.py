"""API validation and meaningful larger canonical-rule examples."""
from __future__ import annotations

import pytest
from reviewer_support import find_root, load_selected_generator

ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator("2e663d812b7a", root=ROOT)


@pytest.mark.parametrize("band", ["easy", None, "hard"])
@pytest.mark.parametrize("axis,value", [
    ("seed", True), ("seed", False), ("seed", 1.0), ("seed", 1.75), ("seed", "1"),
    ("sample_index", True), ("sample_index", False), ("sample_index", 1.0),
    ("sample_index", 1.75), ("sample_index", "1"), ("sample_index", -1),
    ("difficulty", True), ("difficulty", False), ("difficulty", 0),
    ("difficulty", 1.0), ("difficulty", "__invalid_difficulty__"),
])
def test_public_call_scalars_are_not_silently_coerced(axis, value, band):
    arguments = dict(seed=991, sample_index=0, difficulty=band)
    arguments[axis] = value
    with pytest.raises(ValueError):
        GEN.generate(**arguments)


def test_negative_integer_seed_is_supported_and_deterministic():
    assert GEN.generate(-7, 0) == GEN.generate(-7, 0)


@pytest.mark.parametrize("height,width,row,col", [
    (30, 30, 2, 0), (30, 30, 29, 29), (30, 30, 16, 16),
    (30, 9, 29, 8), (9, 30, 8, 29), (21, 29, 11, 19),
])
def test_large_exact_controls_are_observable(height, width, row, col):
    controls = dict(grid_h=height, grid_w=width, seed_r=row, seed_c=col,
                    key_len=min(10, width), palette_size=4, zero_rings=1)
    grid = GEN.generate(2461, 0, **controls)
    assert GEN.observe_overrides(grid) == controls
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("axis,value", [("seed_r", 29), ("seed_c", 29)])
def test_largest_seed_coordinate_adapts_unpinned_dimensions(axis, value):
    for i in range(10):
        grid = GEN.generate(210, i, **{axis: value})
        assert GEN.observe_overrides(grid)[axis] == value
        assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_mix_keeps_anchors_and_reaches_large_nonempty_rings(band):
    samples = [GEN.generate(735, i, difficulty=band) for i in range(100)]
    shapes = [(len(g), len(g[0])) for g in samples]
    assert sum(shape == (30, 30) for shape in shapes) >= 20
    assert sum(max(shape) > 20 for shape in shapes) >= 60
    assert sum(shape == (16, 16) for shape in shapes) >= 30
    assert any(h != w and max(h, w) > 20 for h, w in shapes)
    # Meaningful large scenes include a long positional key and a seed near
    # the far boundary; this is not just extending an old input with blank rows.
    assert any(max(shape) > 20 and len(GEN._parts(g)[0]) >= 9
               for g, shape in zip(samples, shapes))
    assert any(max(GEN._parts(g)[1]) > 18 for g in samples)


def test_sizes_beyond_arc_limit_and_infeasible_positions_are_rejected():
    for controls in ({"grid_h": 31}, {"grid_w": 31}, {"seed_r": 30},
                     {"seed_c": 30}, {"grid_h": 20, "seed_r": 29},
                     {"grid_w": 20, "seed_c": 29}):
        with pytest.raises(ValueError):
            GEN.generate(19, 0, **controls)
