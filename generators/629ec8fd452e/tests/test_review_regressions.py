"""Regression coverage added by review-6260ee24a1c08425.

These tests are intentionally portable: they bind canonical/runtime data to the
containing source tree instead of importing repository-only scripts.
"""
from __future__ import annotations

import copy

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "629ec8fd452e"
ROOT = find_root(__file__)
gen, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


@pytest.mark.parametrize("seed", [True, 17.0, "17"])
def test_seed_requires_a_literal_integer(seed: object) -> None:
    with pytest.raises((TypeError, ValueError), match="seed"):
        gen.generate(seed, 0, difficulty="medium")


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_sample_index_requires_a_nonnegative_literal_integer(
    sample_index: object,
) -> None:
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.generate(17, sample_index, difficulty="medium")


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("grid_h", True),
        ("grid_h", 9.0),
        ("grid_h", "9"),
        ("grid_w", True),
        ("grid_w", 10.0),
        ("grid_w", "10"),
        ("n_hollow", True),
        ("n_hollow", 1.0),
        ("n_hollow", "1"),
        ("n_solid", True),
        ("n_solid", 1.0),
        ("n_solid", "1"),
    ],
)
def test_integer_overrides_reject_coercible_non_integer_scalars(
    axis: str, value: object
) -> None:
    with pytest.raises((TypeError, ValueError), match=axis):
        gen.generate(17, 3, difficulty="medium", **{axis: value})


@pytest.mark.parametrize("value", [True, 1, "OPEN", "other"])
def test_shared_role_override_requires_a_declared_literal(value: object) -> None:
    with pytest.raises((TypeError, ValueError), match="shared_reject_role"):
        gen.generate(17, 3, difficulty="medium", shared_reject_role=value)


def test_every_generated_leaking_component_matches_a_survivor_cell_count() -> None:
    """Prevent bbox-gap-plus-size shortcuts from fitting the teaching sampler."""
    for band in ("easy", "medium", "hard"):
        for sample_index in range(16):
            grid = gen.generate(20261012, sample_index, difficulty=band)
            analysis = gen._analysis(grid)
            hollow_sizes = {
                len(component["cells"]) for component in analysis["hollow"]
            }
            leaking_sizes = {
                len(component["cells"]) for component in analysis["open_like"]
            }
            assert leaking_sizes & hollow_sizes, (
                band,
                sample_index,
                leaking_sizes,
                hollow_sizes,
            )


def test_combined_bbox_gap_and_minimum_size_rival_is_declared_and_refuted() -> None:
    rival_name = "bbox_missing_interior_at_least_8"
    assert rival_name in gen.SEMANTIC_RIVALS
    rival = gen.SEMANTIC_RIVALS[rival_name]
    for band in ("easy", "medium", "hard"):
        for sample_index in range(8):
            grid = gen.generate(314159, sample_index, difficulty=band)
            assert rival(copy.deepcopy(grid)) != gen.rule_true(grid)


def test_retained_large_open_counterexample_refutes_combined_rival() -> None:
    grid = [
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 0, 0],
        [0, 0, 0, 0, 0, 0, 3, 0, 0, 3, 0, 0],
        [0, 0, 0, 0, 0, 0, 3, 0, 3, 3, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    rival = gen.SEMANTIC_RIVALS["bbox_missing_interior_at_least_8"]
    assert rival(copy.deepcopy(grid)) != gen.rule_true(grid)
