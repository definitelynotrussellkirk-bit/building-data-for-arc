"""Focused regression tests added by review-a1e69e9fdec20d2f."""
from __future__ import annotations

import pytest
from reviewer_support import find_root, load_selected_generator


ROOT = find_root(__file__)
GEN, GENERATOR_SOURCE, GENERATOR_SHA256 = load_selected_generator(
    "19158f03ecb2", root=ROOT
)


def _mirror(grid):
    return [row + list(reversed(row)) for row in grid]


def _duplicate(grid):
    return [row + row for row in grid]


def _pair(grid, solve=_mirror):
    return {"input": grid, "output": solve(grid)}


def test_call_arguments_reject_scalar_coercion():
    for bad_seed in (True, False, 1.0, 1.75, "1"):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(bad_seed, 0, difficulty="easy")
    for bad_index in (True, False, 1.0, 1.75, "1", -1):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, bad_index, difficulty="easy")
    for bad_difficulty in (True, False, 0, 1.0, "__invalid_difficulty__"):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 0, difficulty=bad_difficulty)


def test_declared_axes_reject_wrong_scalar_types():
    bad_cases = (
        {"grid_h": 3.0},
        {"grid_w": True},
        {"palette_size": "3"},
        {"texture": 1},
        {"bg_density": True},
        {"noise_overlay": "0.1"},
        {"lr_asymmetric": 1},
    )
    for overrides in bad_cases:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(7, 0, difficulty="medium", **overrides)


def test_unknown_override_axis_is_rejected():
    with pytest.raises((TypeError, ValueError, KeyError), match="unknown override"):
        GEN.generate(7, 0, __override_contract_unknown_axis__=123)


def test_partial_high_palette_override_widens_only_unpinned_dimension():
    # Index 3 is the scheduled symmetric branch. A 3-row symmetric grid needs
    # width >= 7 to expose ten independent palette cells. The caller pinned
    # height and palette, not width, so generation should widen width rather
    # than reject a feasible request merely because the easy default stops at 6.
    grid = GEN.generate(17, 3, difficulty="easy", grid_h=3, palette_size=10)
    observed = GEN.observe_overrides(grid)
    assert observed["grid_h"] == 3
    assert observed["palette_size"] == 10
    assert observed["lr_asymmetric"] is False
    assert 7 <= observed["grid_w"] <= 15

    grid = GEN.generate(18, 3, difficulty="easy", grid_w=3, palette_size=10)
    observed = GEN.observe_overrides(grid)
    assert observed["grid_w"] == 3
    assert observed["palette_size"] == 10
    assert observed["lr_asymmetric"] is False
    assert 5 <= observed["grid_h"] <= 15


def test_impossible_exact_overrides_raise_structured_incompatibility():
    with pytest.raises(ValueError) as captured:
        GEN.generate(
            19,
            0,
            grid_h=3,
            grid_w=4,
            palette_size=10,
            lr_asymmetric=False,
        )
    assert {
        "grid_h",
        "grid_w",
        "palette_size",
        "lr_asymmetric",
    } <= set(captured.value.incompatible_axes)


def test_semantic_contract_accepts_domain_and_refutes_duplication():
    asymmetric = [[1, 2, 3], [3, 1, 2], [2, 3, 1]]
    symmetric = [[1, 2, 1], [2, 3, 2], [3, 1, 3]]

    assert GEN.strict_canonical_like(asymmetric) == []
    assert GEN.SEMANTIC_WITNESSES["asymmetric_refutes_duplication"](asymmetric)
    assert not GEN.SEMANTIC_WITNESSES["asymmetric_refutes_duplication"](symmetric)
    assert GEN.SEMANTIC_RIVALS["duplicate_input"](asymmetric) == _duplicate(asymmetric)
    assert _mirror(asymmetric) != _duplicate(asymmetric)


def test_lesson_identifiability_reports_only_query_relevant_ambiguity():
    asymmetric = [[1, 2, 3], [3, 1, 2], [2, 3, 1]]
    symmetric = [[1, 2, 1], [2, 3, 2], [3, 1, 3]]

    assert GEN.lesson_identifiable([_pair(asymmetric)], _pair(symmetric)) == []

    reasons = GEN.lesson_identifiable([_pair(symmetric)], _pair(asymmetric))
    assert reasons
    assert any("duplicate" in reason.lower() for reason in reasons)

    # When the surviving rival predicts the same query output, it is not a
    # query-answer ambiguity even though the general rule remains under-taught.
    assert GEN.lesson_identifiable([_pair(symmetric)], _pair(symmetric)) == []
