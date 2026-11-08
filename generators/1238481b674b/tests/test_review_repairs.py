"""Focused regressions added by review-cf9c41ca8d4a7c2c.

This file intentionally uses only the portable reviewer/public APIs.  The
pre-existing test_generator_1238481b674b.py is an immutable retained fixture;
its legacy imports are documented separately rather than rewritten here.
"""
from __future__ import annotations

from copy import deepcopy

import pytest

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "1238481b674b"
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


@pytest.mark.parametrize("bad_seed", [True, False, 1.25, "17", None])
def test_generate_rejects_non_integer_seed_scalars(bad_seed) -> None:
    with pytest.raises(TypeError, match="seed"):
        GEN.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.25, "17", None])
def test_generate_rejects_non_integer_sample_index_scalars(bad_index) -> None:
    with pytest.raises(TypeError, match="sample_index"):
        GEN.generate(17, bad_index, difficulty="easy")


def test_generate_rejects_negative_sample_index() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        GEN.generate(17, -1, difficulty="easy")


@pytest.mark.parametrize("bad_seed", [True, False, 1.25, "17", None])
def test_schedule_profile_rejects_non_integer_seed_scalars(bad_seed) -> None:
    with pytest.raises(TypeError, match="seed"):
        GEN.schedule_profile(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.25, "17", None])
def test_schedule_profile_rejects_non_integer_sample_index_scalars(bad_index) -> None:
    with pytest.raises(TypeError, match="sample_index"):
        GEN.schedule_profile(17, bad_index, difficulty="easy")


def test_schedule_profile_rejects_negative_sample_index() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        GEN.schedule_profile(17, -1, difficulty="easy")


def test_declared_canonical_shortcut_is_truthful_and_generator_refutes_it() -> None:
    assert set(GEN.CANONICAL_SHORTCUTS) == {"nearest_distractor_corner"}
    shortcut = GEN.CANONICAL_SHORTCUTS["nearest_distractor_corner"]

    # The shortcut must really fit every usable canonical demonstration.
    assert len(PAIRS) == 4
    for pair in PAIRS:
        assert shortcut(pair["input"]) == pair["output"]

    # The production generator must emit a lawful exact disagreement, not merely
    # declare a hypothetical rival.  The clockwise marker is nearer top-right,
    # while the absent bbox corner is top-left.
    witness = GEN.generate(
        991,
        1,
        difficulty="medium",
        grid_h=10,
        grid_w=10,
        side_len=6,
        missing_corner="top_left",
        row_offset=1,
        col_offset=1,
        distractor_variant="clockwise",
    )
    assert GEN.self_check(witness) == []
    assert GEN.observe_overrides(witness)["distractor_variant"] == "clockwise"
    assert shortcut(witness) != GEN.rule_mirror(witness)
    assert GEN.SEMANTIC_WITNESSES["distractor_is_not_orientation_cue"](witness)
    assert "nearest_distractor_corner" in GEN.WITNESS_RIVALS[
        "distractor_is_not_orientation_cue"
    ]


def test_public_authority_still_matches_canonical_and_generated_oracle() -> None:
    generated = [
        GEN.generate(8800 + index, index, difficulty=band)
        for band in ("easy", "medium", "hard")
        for index in range(4)
    ]
    inputs = [pair["input"] for pair in PAIRS] + generated
    frozen = deepcopy(inputs)
    report = Catalog(ROOT).apply(TASK_ID, inputs, reference="canonical", timeout=180)
    assert report["rule_hash_matches_catalog"]
    assert report["executed_rule_hash"] == GEN.RULE_HASH
    assert [row["error"] for row in report["results"]] == [None] * len(inputs)
    outputs = [row["output"] for row in report["results"]]
    assert outputs[: len(PAIRS)] == [pair["output"] for pair in PAIRS]
    assert outputs[len(PAIRS) :] == [GEN.rule_mirror(grid) for grid in generated]
    assert inputs == frozen
