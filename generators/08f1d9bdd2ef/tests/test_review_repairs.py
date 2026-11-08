"""Regression tests for the review-bc6873bb6eef14d9 repair."""
from __future__ import annotations

import hashlib
import json

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "08f1d9bdd2ef"
ROOT = find_root(__file__)
TASK_HOME = ROOT / "generators" / TASK_ID
GENERATOR, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
BANDS = ("easy", "medium", "hard")


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_seed_and_sample_index_reject_non_integer_coercions_and_negative_index():
    for bad in (True, False, 1.0, 1.75, "1"):
        with pytest.raises((TypeError, ValueError)):
            GENERATOR.generate(bad, 0, difficulty="easy")
    for bad in (True, False, 1.0, 1.75, "1", -1):
        with pytest.raises((TypeError, ValueError)):
            GENERATOR.generate(0, bad, difficulty="easy")


def test_pinned_profile_floor_has_exact_support_in_every_band_and_pooled_envelope():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    profiles = {_profile(pair["input"]) for pair in pairs}
    heights = [profile[0] for profile in profiles]
    widths = [profile[1] for profile in profiles]
    palettes = [profile[2] for profile in profiles]
    envelope = (
        (min(heights), max(heights)),
        (min(widths), max(widths)),
        (min(palettes), max(palettes)),
    )

    pooled_exact = 0
    pooled_envelope = 0
    for band in BANDS:
        band_exact = 0
        for index in range(20):
            seed = _pinned_seed(band, index)
            sample_index = seed % 7919 + index
            profile = _profile(
                GENERATOR.generate(seed, sample_index, difficulty=band)
            )
            is_exact = profile in profiles
            is_envelope = all(lo <= value <= hi for value, (lo, hi) in zip(profile, envelope))
            band_exact += is_exact
            pooled_exact += is_exact
            pooled_envelope += is_envelope
        assert band_exact >= 1, f"{band} has no exact canonical-profile anchor"

    assert pooled_exact >= 3
    assert pooled_envelope >= 15


def test_semantic_contract_names_and_refutes_public_style_only_shortcut():
    assert GENERATOR.strict_canonical_like(
        GENERATOR.generate(1, 2, difficulty="easy")
    ) == []
    assert set(GENERATOR.SEMANTIC_RIVALS) == {"public_style_only"}
    assert set(GENERATOR.CANONICAL_SHORTCUTS) == {"public_style_only"}
    assert set(GENERATOR.LESSON_COMPETITORS) == {"public_style_only"}
    assert GENERATOR.WITNESS_RIVALS == {
        "generalized_style": ["public_style_only"]
    }

    shortcut = GENERATOR.CANONICAL_SHORTCUTS["public_style_only"]
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert shortcut(pair["input"]) == pair["output"]

    generalized = GENERATOR.generate(
        17, 29, difficulty="hard", scene_family="generalized"
    )
    intended = GENERATOR.rule_mirror(generalized)
    assert GENERATOR.SEMANTIC_WITNESSES["generalized_style"](generalized)
    assert shortcut(generalized) != intended


def test_lesson_identifiability_requires_a_generalized_demonstration():
    public_demos = []
    for index in range(3):
        grid = GENERATOR.generate(
            100 + index,
            200 + index,
            difficulty="medium",
            scene_family="public",
        )
        public_demos.append({"input": grid, "output": GENERATOR.rule_mirror(grid)})
    query_grid = GENERATOR.generate(
        300, 400, difficulty="medium", scene_family="generalized"
    )
    query = {"input": query_grid, "output": GENERATOR.rule_mirror(query_grid)}
    assert any(
        "public_style_only" in reason
        for reason in GENERATOR.lesson_identifiable(public_demos, query)
    )

    generalized_demo_grid = GENERATOR.generate(
        500, 600, difficulty="medium", scene_family="generalized"
    )
    demos = public_demos[:2] + [{
        "input": generalized_demo_grid,
        "output": GENERATOR.rule_mirror(generalized_demo_grid),
    }]
    assert GENERATOR.lesson_identifiable(demos, query) == []


def test_default_family_schedule_refutes_style_shortcut_under_every_query_rotation():
    """Every four-pair lesson must leave a generalized demo after holdout."""
    assert GENERATOR.LESSON_SCHEDULE_PERIOD == 4
    seeds = (0, 1, 17, -3, 2907340390, 3348219404)
    for seed in seeds:
        for start in range(GENERATOR.LESSON_SCHEDULE_PERIOD):
            families = [
                GENERATOR.canonical_profile_signature(
                    GENERATOR.generate(
                        seed,
                        start + offset,
                        difficulty="medium",
                    )
                )
                for offset in range(4)
            ]
            assert families.count("public") == 1, (seed, start, families)
            for query_index in range(4):
                demos = [
                    family
                    for index, family in enumerate(families)
                    if index != query_index
                ]
                assert "generalized" in demos, (seed, start, query_index, families)


def test_retained_public_style_shortcut_counterexample_is_source_bound():
    path = TASK_HOME / "counterexamples" / "public_style_only_generalized.json"
    witness = json.loads(path.read_text())
    assert witness["generator_sha256"] == SOURCE_SHA256
    assert witness["rule_hash"] == GENERATOR.RULE_HASH
    grid = witness["input"]
    assert GENERATOR.self_check(grid) == []
    assert GENERATOR.canonical_profile_signature(grid) == "generalized"
    assert GENERATOR.rule_mirror(grid) == witness["intended_output"]
    rival = GENERATOR.CANONICAL_SHORTCUTS[witness["rival"]]
    assert rival(grid) == witness["rival_output"]
    assert witness["rival_output"] != witness["intended_output"]
