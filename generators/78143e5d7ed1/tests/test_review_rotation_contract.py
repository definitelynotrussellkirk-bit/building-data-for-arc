"""Regression coverage added by review-5d0a82e174676457."""
from __future__ import annotations

import hashlib
import importlib.util
import sys

import pytest

from reviewer_support import find_root

ROOT = find_root(__file__)
GENERATOR_PATH = next(
    path
    for path in (
        ROOT / "generators" / "78143e5d7ed1" / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / "78143e5d7ed1" / "generator.py",
    )
    if path.is_file()
)
_SPEC = importlib.util.spec_from_file_location(
    "generator_78143e5d7ed1_review_test", GENERATOR_PATH
)
assert _SPEC is not None and _SPEC.loader is not None
GEN = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = GEN
_SPEC.loader.exec_module(GEN)


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN._solve_grid(grid)}


def test_each_three_object_profile_carries_paired_sort_evidence() -> None:
    expected = {
        "area": {"area", "height"},
        "height": {"height", "color"},
        "width": {"area", "width"},
        "color": {"width", "color"},
    }
    for band in ("easy", "medium", "hard"):
        observed_profiles = []
        aggregate: set[str] = set()
        for sample_index in range(4):
            grid = GEN.generate(4100, sample_index, difficulty=band, n_objs=3)
            assert GEN.self_check(grid) == []
            profile = GEN.observe_overrides(grid)["tie_profile"]
            evidence = GEN._evidence_keys(GEN._extract_components(grid))
            observed_profiles.append(profile)
            aggregate.update(evidence)
            assert evidence == expected[profile]
        assert observed_profiles == list(GEN.TIE_PROFILES)
        assert aggregate == {"area", "height", "width", "color"}


@pytest.mark.parametrize("sample_index", [True, False, -1])
def test_generate_rejects_noncanonical_sample_indices(sample_index) -> None:
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        GEN.generate(7, sample_index)


def test_generate_rejects_unknown_override_keys() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(7, 0, typo_axis=123)


def test_every_rotated_five_pair_lesson_refutes_declared_rivals() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in (0, 20260725):
            for start in range(4):
                pairs = [_pair(seed, index, band) for index in range(start, start + 5)]
                for query_position in range(5):
                    query = pairs[query_position]
                    demos = [
                        pair
                        for index, pair in enumerate(pairs)
                        if index != query_position
                    ]
                    assert GEN.lesson_identifiable(demos, query) == []
                    for name, rival in GEN.LESSON_COMPETITORS.items():
                        fits = all(
                            rival(pair["input"]) == pair["output"] for pair in demos
                        )
                        if fits:
                            assert rival(query["input"]) == query["output"], (
                                band,
                                seed,
                                start,
                                query_position,
                                name,
                            )


def test_original_omit_height_rotation_is_directly_refuted() -> None:
    pairs = [_pair(0, sample_index, "medium") for sample_index in range(5)]
    query_position = 1
    demos = [pair for index, pair in enumerate(pairs) if index != query_position]
    assert any(
        GEN.SEMANTIC_RIVALS["omit_height_key"](pair["input"])
        != pair["output"]
        for pair in demos
    )
    assert GEN.lesson_identifiable(demos, pairs[query_position]) == []


def test_semantic_witnesses_name_measured_rival_disagreements() -> None:
    grids = [
        GEN.generate(8102, index, difficulty="medium", n_objs=3)
        for index in range(4)
    ]
    assert set(GEN.WITNESS_RIVALS) == set(GEN.SEMANTIC_WITNESSES)
    for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
        witness_grid = next(grid for grid in grids if witness(grid))
        intended = GEN._solve_grid(witness_grid)
        for rival_name in GEN.WITNESS_RIVALS[witness_name]:
            assert GEN.SEMANTIC_RIVALS[rival_name](witness_grid) != intended


def test_pinned_profile_floor_has_exact_canonical_support_in_every_band() -> None:
    canonical_profiles = {
        (9, 12, 4),
        (10, 12, 4),
        (10, 14, 4),
        (11, 13, 4),
    }
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{GEN.TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            grid = GEN.generate(seed, sample_index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            hits += int(profile in canonical_profiles)
        assert hits >= 1, band
