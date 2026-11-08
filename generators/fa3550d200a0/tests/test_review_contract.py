"""Focused regression coverage for the source-bound 2026-10-23 review."""
from itertools import product

import pytest
from reviewer_support import canonical_pairs, find_root, load_selected_generator


gen, SOURCE, SOURCE_SHA256 = load_selected_generator("fa3550d200a0", root=find_root(__file__))


@pytest.mark.parametrize("name,value", [
    ("seed", True), ("seed", False), ("seed", 1.0), ("seed", 1.75), ("seed", "1"),
    ("sample_index", True), ("sample_index", False), ("sample_index", -1),
    ("sample_index", 1.0), ("sample_index", "1"),
])
def test_call_scalars_reject_coercion(name, value):
    args = {"seed": 17, "sample_index": 0, name: value}
    with pytest.raises((TypeError, ValueError)):
        gen.generate(**args)


def test_small_canonical_sizes_and_large_grid_exact_controls():
    for h, w in [(16, 18), (16, 20), (18, 22), (26, 24), (30, 30)]:
        for side in ("left", "right"):
            grid = gen.generate(17, 2, grid_h=h, grid_w=w, rect_h=6, rect_w=6,
                                piece_count=5, decoy_count=1, canvas_side=side)
            assert gen.self_check(grid) == []
            assert (len(grid), len(grid[0])) == (h, w)
            assert gen.observe_overrides(grid)["piece_count"] == 5


def test_impossible_joint_width_is_rejected_explicitly():
    with pytest.raises(ValueError, match="rect_w.*grid_w"):
        gen.generate(17, 0, grid_w=18, rect_w=12)


def test_shortcut_declaration_really_fits_all_canonical_pairs():
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__), labeled_only=True)
    assert pairs
    assert gen.CANONICAL_SHORTCUTS
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs)


def test_each_cycle_rotation_has_two_teaching_inputs():
    # Two explicit witnesses per four-pair window survive any one held-out pair.
    for band, seed, start in product(("easy", "medium", "hard"), (0, 17), range(4)):
        grids = [gen.generate(seed, start + i, difficulty=band) for i in range(4)]
        for rival_name in ("local_window_3x3", "four_connected"):
            rival = gen.LESSON_COMPETITORS[rival_name]
            distinguished = [gen.diagnostic_stamp(g) != rival(g) for g in grids]
            assert sum(distinguished) >= 2, (band, seed, start, rival_name)
            for held_out in range(4):
                assert any(distinguished[i] for i in range(4) if i != held_out)


def test_scheduled_shape_stamps_keep_boundary_overrides_observable():
    for seed, side, palette in product((0, 17), ("left", "right"), gen.PALETTE_KINDS):
        args = dict(grid_h=16, grid_w=18, rect_h=6, rect_w=6, piece_count=5,
                    decoy_count=1, canvas_side=side, palette_kind=palette)
        grid = gen.generate(seed, 0, difficulty="hard", **args)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == args
