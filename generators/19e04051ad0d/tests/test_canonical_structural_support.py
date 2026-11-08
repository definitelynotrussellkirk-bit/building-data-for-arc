"""Canonical structural-support regressions for task 19e04051ad0d."""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator
from review_diagnostics import structural_signature

ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator("19e04051ad0d", root=ROOT)


def _persistent_markers(grid):
    return structural_signature(
        {"input": grid, "output": GEN.rule_mirror(grid)}
    )["persistent_markers"]


CANONICAL_SUPPORT = {
    structural_signature(pair)["persistent_markers"]
    for pair in canonical_pairs(GEN.TASK_ID, root=ROOT)
}
CANONICAL_OBJECT_SUPPORT = {
    structural_signature(pair)["object_count"]
    for pair in canonical_pairs(GEN.TASK_ID, root=ROOT)
}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_linter_sampling_window_overlaps_canonical_persistent_marker_support(band):
    generated_support = {
        _persistent_markers(GEN.generate(seed, seed, difficulty=band))
        for seed in range(1, 9)
    }
    assert CANONICAL_SUPPORT & generated_support, (
        band,
        CANONICAL_SUPPORT,
        generated_support,
    )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_connected_profile_is_present_without_erasing_random_mask_support(band):
    connected_witness = GEN.generate(6, 6, difficulty=band)
    assert _persistent_markers(connected_witness) == 0

    random_profile_counts = [
        _persistent_markers(GEN.generate(index, index, difficulty=band))
        for index in range(1, 6)
    ]
    assert any(count > 0 for count in random_profile_counts)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_linter_sampling_window_overlaps_canonical_object_count_support(band):
    generated_support = {
        structural_signature(
            {"input": grid, "output": GEN.rule_mirror(grid)}
        )["object_count"]
        for seed in range(1, 9)
        for grid in [GEN.generate(seed, seed, difficulty=band)]
    }
    assert CANONICAL_OBJECT_SUPPORT & generated_support, (
        band,
        CANONICAL_OBJECT_SUPPORT,
        generated_support,
    )
