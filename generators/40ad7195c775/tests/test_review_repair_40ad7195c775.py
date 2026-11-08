"""Regression tests for the 2026-10 review repair of 40ad7195c775."""
from __future__ import annotations

from copy import deepcopy
import json

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "40ad7195c775"
ROOT = find_root(__file__)
gen, _GENERATOR_PATH, _GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _labeled(grid):
    return {"input": deepcopy(grid), "output": gen.rule_mirror(grid)}


@pytest.mark.parametrize(
    "seed,sample_index",
    [
        (True, 0),
        (False, 0),
        (1.5, 0),
        ("1", 0),
        (0, True),
        (0, False),
        (0, 1.5),
        (0, "1"),
        (0, -1),
    ],
)
def test_seed_and_sample_index_reject_invalid_scalars(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index)


def test_negative_literal_seed_remains_supported_but_sample_index_is_nonnegative():
    grid = gen.generate(-17, 0, difficulty="hard")
    assert gen.self_check(grid) == []


def test_semantic_contract_accepts_canonical_pairs_and_declares_bound_rival():
    assert PAIRS
    for pair in PAIRS:
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.CANONICAL_SHORTCUTS["canonical_profile_lookup"](pair["input"]) == pair["output"]

    assert gen.SEMANTIC_RIVALS["canonical_profile_lookup"] is gen.CANONICAL_SHORTCUTS["canonical_profile_lookup"]
    assert gen.LESSON_COMPETITORS["canonical_profile_lookup"] is gen.CANONICAL_SHORTCUTS["canonical_profile_lookup"]
    assert gen.WITNESS_RIVALS == {
        "generalized_geometry": ["canonical_profile_lookup"]
    }


def test_generalized_geometry_witness_refutes_canonical_profile_lookup_shortcut():
    generalized_code = len(gen.PUBLIC_GEOMETRIES) * gen.PALETTE_COUNT
    grid = gen.generate(123, 9, scene_code=generalized_code)
    original = deepcopy(grid)
    expected = gen.rule_mirror(grid)
    rival = gen.CANONICAL_SHORTCUTS["canonical_profile_lookup"]

    assert gen.SEMANTIC_WITNESSES["generalized_geometry"](grid) is True
    assert rival(grid) == grid
    assert rival(grid) != expected
    assert grid == original


def test_lesson_contract_requires_a_demonstration_that_refutes_lookup_shortcut():
    # Default sample indexes 0..3 contain one public scene and three generalized
    # scenes, so the first three labeled pairs refute the lookup shortcut.
    pairs = [_labeled(gen.generate(7, index)) for index in range(4)]
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []

    public_demos = [
        _labeled(gen.generate(0, 0, scene_code=index * gen.PALETTE_COUNT))
        for index in range(3)
    ]
    generalized = _labeled(
        gen.generate(0, 0, scene_code=len(gen.PUBLIC_GEOMETRIES) * gen.PALETTE_COUNT)
    )
    reasons = gen.lesson_identifiable(public_demos, generalized)
    assert any("canonical_profile_lookup" in reason for reason in reasons)


def test_retained_shortcut_counterexample_is_source_bound_and_reproducible():
    path = ROOT / (
        "generators/40ad7195c775/counterexamples/"
        "canonical-profile-lookup-generalized.json"
    )
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["generator_sha256"] == _GENERATOR_SHA256
    grid = gen.generate(
        record["seed"],
        record["sample_index"],
        scene_code=record["scene_code"],
    )
    assert grid == record["input"]
    assert gen.rule_mirror(grid) == record["intended_output"]
    assert (
        gen.CANONICAL_SHORTCUTS["canonical_profile_lookup"](grid)
        == record["rival_output"]
    )
    assert record["intended_output"] != record["rival_output"]
