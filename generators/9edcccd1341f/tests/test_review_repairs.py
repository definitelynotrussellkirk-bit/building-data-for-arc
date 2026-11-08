"""Focused regressions for the 2026-10-23 review repairs."""
from __future__ import annotations

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "9edcccd1341f"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize("bad_seed", [True, False, 1.5, "7", None])
def test_generate_rejects_noninteger_seed(bad_seed: object) -> None:
    with pytest.raises(TypeError, match="seed"):
        GEN.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.5, "7", None])
def test_generate_rejects_noninteger_sample_index(bad_index: object) -> None:
    with pytest.raises(TypeError, match="sample_index"):
        GEN.generate(0, bad_index)


def test_generate_rejects_negative_sample_index() -> None:
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(0, -1)


def test_noncanonical_rivals_are_not_declared_canonical_shortcuts() -> None:
    assert GEN.CANONICAL_SHORTCUTS == {}
    assert GEN.LESSON_COMPETITORS == GEN.SEMANTIC_RIVALS
    assert set(GEN.LESSON_COMPETITORS) == {
        "draw_only_outer_frame",
        "draw_only_winner_bbox",
        "retain_winner_cells_instead_of_bbox",
        "use_original_border_color",
        "choose_least_frequent_interior_color",
    }
