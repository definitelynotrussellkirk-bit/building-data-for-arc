"""Regression tests for the reviewer repair of b7c3b8bc9805."""
from __future__ import annotations

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
gen, _, _ = load_selected_generator("b7c3b8bc9805", root=ROOT)


def test_canonical_shortcuts_are_exactly_the_rules_that_fit_all_canonical_pairs() -> None:
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    assert set(gen.CANONICAL_SHORTCUTS) == {"marker_position_symmetric"}
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("bad_seed", [False, 1.5, "1"])
def test_generate_rejects_non_literal_integer_seed(bad_seed) -> None:
    with pytest.raises((TypeError, ValueError), match="seed"):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [False, 1.5, "1", -1])
def test_generate_rejects_invalid_sample_index(bad_index) -> None:
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.generate(1, bad_index)


@pytest.mark.parametrize("bad_seed", [False, 1.5, "1"])
def test_schedule_profile_rejects_non_literal_integer_seed(bad_seed) -> None:
    with pytest.raises((TypeError, ValueError), match="seed"):
        gen.schedule_profile(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [False, 1.5, "1", -1])
def test_schedule_profile_rejects_invalid_sample_index(bad_index) -> None:
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.schedule_profile(1, bad_index)


@pytest.mark.parametrize("axis", ["grid_h", "grid_w", "frame_h", "frame_w"])
@pytest.mark.parametrize("bad_value", [False, 10.5, "10"])
def test_integer_overrides_reject_coercible_non_integers(axis: str, bad_value) -> None:
    with pytest.raises((TypeError, ValueError), match=axis):
        gen.generate(7, 0, **{axis: bad_value})
