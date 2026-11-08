"""Review-owned regressions for b6ba2d176fe8.

The inherited ``test_generator_b6ba2d176fe8.py`` is a frozen fixture.  New
repair coverage belongs here so the before/after contract remains auditable.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("review_b6ba2d176fe8_generator", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("canonical_prior", 1),
        ("canonical_prior", "true"),
        ("n_objects", True),
        ("n_objects", 3.0),
        ("n_objects", "3"),
        ("n_objects", 1),
        ("n_objects", 7),
        ("row_layout", 1),
        ("row_layout", "diagonal"),
        ("column_layout", False),
        ("column_layout", "random"),
    ],
)
def test_invalid_exact_override_values_fail_at_api_boundary(axis, value):
    with pytest.raises(ValueError, match=axis):
        generator.generate(17, 23, difficulty="hard", **{axis: value})


def test_valid_canonical_joint_overrides_are_honored_exactly():
    for n_objects in (3, 4):
        grid = generator.generate(
            31,
            47 + n_objects,
            canonical_prior=True,
            n_objects=n_objects,
            row_layout="bottom",
            column_layout="compact",
        )
        assert generator.observe_overrides(grid) == {
            "canonical_prior": True,
            "n_objects": n_objects,
            "row_layout": "bottom",
            "column_layout": "compact",
        }


def test_canonical_prior_incompatibilities_are_value_specific_and_declared():
    declared = generator.INCOMPATIBLE_OVERRIDE_COMBINATIONS
    assert {"canonical_prior": True, "n_objects": (2, 5, 6)} in declared
    assert {
        "canonical_prior": True,
        "row_layout": ("mixed", "scattered"),
    } in declared
    assert {
        "canonical_prior": True,
        "column_layout": ("irregular", "spread"),
    } in declared

    for kwargs in (
        {"canonical_prior": True, "n_objects": 2},
        {"canonical_prior": True, "n_objects": 5},
        {"canonical_prior": True, "n_objects": 6},
        {"canonical_prior": True, "row_layout": "mixed"},
        {"canonical_prior": True, "row_layout": "scattered"},
        {"canonical_prior": True, "column_layout": "irregular"},
        {"canonical_prior": True, "column_layout": "spread"},
    ):
        with pytest.raises(ValueError):
            generator.generate(3, 5, **kwargs)


def _canonical_staircase(grid):
    rectangles = generator._ordered_rectangles(grid)
    assert rectangles is not None
    output = [[0 for _ in row] for row in grid]
    row = column = 0
    for rectangle in rectangles:
        top, left, bottom, right = rectangle["bbox"]
        height = bottom - top + 1
        width = right - left + 1
        for rr in range(row, row + height):
            for cc in range(column, column + width):
                output[rr][cc] = rectangle["color"]
        row += height - 1
        column += width - 1
    return output


def test_semantic_contract_accepts_lawful_inputs_and_refutes_corner_owner_rival():
    grid = generator.generate(
        101,
        303,
        difficulty="hard",
        canonical_prior=False,
        n_objects=6,
        row_layout="scattered",
        column_layout="spread",
    )
    assert generator.strict_canonical_like(grid) == []
    witness = generator.SEMANTIC_WITNESSES["shared_corner_ownership"]
    rival = generator.SEMANTIC_RIVALS["earlier_corner_owner"]
    assert witness(grid) is True

    canonical = _canonical_staircase(grid)
    rival_output = rival(grid)
    assert rival_output is not None
    assert len(rival_output) == len(canonical)
    assert all(len(a) == len(b) for a, b in zip(rival_output, canonical, strict=True))
    assert rival_output != canonical


def test_semantic_declarations_bind_witness_to_lesson_competitor():
    assert generator.WITNESS_RIVALS == {
        "shared_corner_ownership": ["earlier_corner_owner"]
    }
    assert generator.LESSON_COMPETITORS == generator.SEMANTIC_RIVALS


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_seed_requires_a_literal_integer(bad_seed):
    with pytest.raises(ValueError, match="seed"):
        generator.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_sample_index_requires_a_nonnegative_literal_integer(bad_sample_index):
    with pytest.raises(ValueError, match="sample_index"):
        generator.generate(991, bad_sample_index, difficulty="hard")
