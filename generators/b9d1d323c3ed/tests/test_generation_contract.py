"""Regressions for invalid calls and the forced-corner sampling defect."""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "b9d1d323c3ed"
ROOT = find_root(__file__)
gen, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def occupancy(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return tuple(tuple(bool(value) for value in row[c0:c1 + 1]) for row in grid[r0:r1 + 1])


@pytest.mark.parametrize("argument,value", [
    ("seed", True), ("seed", False), ("seed", 1.0), ("seed", 1.75),
    ("seed", "1"), ("seed", None),
    ("sample_index", True), ("sample_index", False), ("sample_index", -1),
    ("sample_index", 1.0), ("sample_index", "1"), ("sample_index", None),
    ("difficulty", True), ("difficulty", False), ("difficulty", 0),
    ("difficulty", 1.0), ("difficulty", "__invalid_difficulty__"),
    ("difficulty", []), ("difficulty", {}),
])
def test_invalid_call_arguments_are_rejected_before_sampling(argument, value):
    arguments = {"seed": 991, "sample_index": 0, "difficulty": "easy"}
    arguments[argument] = value
    with pytest.raises(ValueError):
        gen.generate(**arguments)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_signed_integer_seeds_and_valid_bands_remain_supported(band):
    grid = gen.generate(-17, 0, difficulty=band)
    assert gen.self_check(grid) == []
    assert grid == gen.generate(-17, 0, difficulty=band)


def test_scattered_sampling_covers_all_canonical_occupancy_masks():
    """Forcing occupied opposite corners excludes three supplied shapes."""
    missing = {occupancy(pair["input"]) for pair in canonical_pairs(TASK_ID, root=ROOT)}
    for seed in range(4096):
        grid = gen.generate(seed, 0, fg_layout="scattered")
        missing.discard(occupancy(grid))
        if not missing:
            break
    assert not missing, f"canonical occupied-box masks absent from the scatter support: {missing}"


@pytest.mark.parametrize("layout", gen.FG_LAYOUTS)
def test_all_layouts_preserve_requested_extent_and_visible_repetition(layout):
    """Removing hardcoded anchors must not shrink requested boxes or fill them."""
    for kind, want in [("small", (2, 2)), ("medium", (3, 3)), ("large", (17, 8))]:
        for seed in range(24):
            grid = gen.generate(seed, 1, grid_h=18, grid_w=18,
                                bbox_size_kind=kind, fg_layout=layout)
            shape = occupancy(grid)
            assert (len(shape), len(shape[0])) == want
            assert any(not cell for row in shape for cell in row)
            assert gen.self_check(grid) == []
