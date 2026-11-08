"""Regression tests for review findings R4E-1 and R4E-2."""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "4e6862c442fd"
ROOT = find_root(__file__)
G, _, _ = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_seed_scalars(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        G.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_sample_index", [True, False, -1, 1.0, 1.75, "1"])
def test_generate_rejects_non_integer_or_negative_sample_index(bad_sample_index):
    with pytest.raises((TypeError, ValueError)):
        G.generate(0, bad_sample_index)


@pytest.mark.parametrize(
    "axis,bad_value",
    [
        ("grid_h", 12.0),
        ("grid_h", 12.75),
        ("grid_h", "12"),
        ("grid_w", 18.0),
        ("grid_w", 18.75),
        ("grid_w", "18"),
        ("source_basis", True),
        ("source_basis", False),
        ("source_basis", 1.0),
        ("source_basis", 1.75),
        ("source_basis", "1"),
        ("target_basis", True),
        ("target_basis", False),
        ("target_basis", 1.0),
        ("target_basis", 1.75),
        ("target_basis", "1"),
        ("motif_id", True),
        ("motif_id", False),
        ("motif_id", 1.0),
        ("motif_id", 1.75),
        ("motif_id", "1"),
    ],
)
def test_integer_overrides_reject_coercible_non_integer_scalars(axis, bad_value):
    with pytest.raises((TypeError, ValueError)):
        G.generate(0, 0, **{axis: bad_value})


def test_declared_canonical_shortcuts_fit_every_labeled_canonical_pair():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for name, shortcut in G.CANONICAL_SHORTCUTS.items():
        for pair in pairs:
            assert shortcut(pair["input"]) == pair["output"], name


def test_partial_heuristics_remain_declared_as_lesson_competitors():
    assert G.LESSON_COMPETITORS == G.SEMANTIC_RIVALS
    assert set(G.WITNESS_RIVALS)
