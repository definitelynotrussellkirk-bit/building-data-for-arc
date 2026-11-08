"""Focused regressions for the 2026-10-23 review repair."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator
from review_diagnostics import structural_signature

TASK_ID = "4d5bb3c0250b"
ROOT = find_root(__file__)


def _generator():
    module, _source, _digest = load_selected_generator(TASK_ID, root=ROOT)
    return module


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_generate_rejects_noninteger_seed(bad_seed: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _generator().generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_generate_rejects_invalid_sample_index(bad_index: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _generator().generate(991, bad_index, difficulty="easy")


@pytest.mark.parametrize("bad_difficulty", [True, False, 0, 1.0, "impossible"])
def test_generate_rejects_invalid_difficulty(bad_difficulty: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _generator().generate(991, 0, difficulty=bad_difficulty)


@pytest.mark.parametrize(
    ("axis", "control"),
    [
        ("separator_color", 1),
        ("target_color", 2),
        ("target_cells", 4),
        ("distractor_colors", 2),
    ],
)
def test_integer_axes_reject_scalar_coercions(axis: str, control: int) -> None:
    for value in (True, False, float(control), control + 0.75, str(control)):
        with pytest.raises((TypeError, ValueError)):
            _generator().generate(991, 0, difficulty="easy", **{axis: value})


@pytest.mark.parametrize("value", [1, 0, "true", None])
def test_target_at_border_requires_literal_bool_when_overridden(value: object) -> None:
    if value is None:
        pytest.skip("None intentionally means no override")
    with pytest.raises((TypeError, ValueError)):
        _generator().generate(991, 0, difficulty="easy", target_at_border=value)


def test_unknown_override_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        _generator().generate(991, 0, difficulty="easy", distractor_colour=4)


def test_equal_separator_and_target_colors_are_structured_incompatibility() -> None:
    with pytest.raises(ValueError) as caught:
        _generator().generate(
            991,
            0,
            difficulty="easy",
            separator_color=4,
            target_color=4,
        )
    assert set(getattr(caught.value, "incompatible_axes", ())) == {
        "separator_color",
        "target_color",
    }


def test_full_canonical_distractor_color_support_is_observable() -> None:
    gen = _generator()
    grid = gen.generate(
        991,
        0,
        difficulty="hard",
        profile="canonical_23_3x6",
        distractor_colors=7,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid)["distractor_colors"] == 7


def test_default_census_overlaps_canonical_singleton_marker_support() -> None:
    """The canonical palette density should appear naturally in the pinned 60 draws."""
    gen = _generator()
    canonical_support = {
        structural_signature(pair)["marker_count"]
        for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    }
    generated_support = set()
    for band in ("easy", "medium", "hard"):
        for seed in range(1, 21):
            grid = gen.generate(seed, seed, difficulty=band)
            generated_support.add(
                structural_signature({"input": grid, "output": gen.rule_mirror(grid)})[
                    "marker_count"
                ]
            )
    assert generated_support & canonical_support, (
        canonical_support,
        sorted(generated_support),
    )


def test_rule_mirror_matches_all_labeled_canonical_pairs() -> None:
    gen = _generator()
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert gen.rule_mirror(deepcopy(pair["input"])) == pair["output"]


def test_semantic_witness_refutes_top_left_shortcut() -> None:
    gen = _generator()
    assert callable(gen.strict_canonical_like)
    assert "target_not_top_left" in gen.SEMANTIC_WITNESSES
    rival_name = "crop_top_left_block"
    assert rival_name in gen.SEMANTIC_RIVALS
    assert rival_name in gen.LESSON_COMPETITORS
    assert rival_name in gen.WITNESS_RIVALS["target_not_top_left"]

    witnesses = []
    for seed in range(64):
        grid = gen.generate(12000 + seed, seed, difficulty="medium")
        if gen.SEMANTIC_WITNESSES["target_not_top_left"](grid):
            witnesses.append(grid)
    assert witnesses
    for grid in witnesses[:8]:
        assert gen.strict_canonical_like(grid) == []
        assert gen.SEMANTIC_RIVALS[rival_name](grid) != gen.rule_mirror(grid)
