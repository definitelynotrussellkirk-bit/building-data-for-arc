from __future__ import annotations

import hashlib
import importlib
import importlib.util
import os
from pathlib import Path

import pytest

TASK_ID = "196d5de2ea8c"
try:
    GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
except ModuleNotFoundError:
    source = Path(os.environ.get("GENERATOR_UNDER_TEST", Path(__file__).resolve().parents[1] / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"repair_test_{TASK_ID}", source)
    assert spec is not None and spec.loader is not None
    GEN = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(GEN)
BANDS = ("easy", "medium", "hard")


def _profile_floor_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_seed_requires_a_literal_integer(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_sample_index_requires_a_nonnegative_literal_integer(bad_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(991, bad_index)


def test_pinned_profile_floor_has_exact_support_in_every_band_and_25_percent_pooled():
    canonical_profiles = {_profile(grid) for grid in GEN._PUBLIC_INPUTS.values()}
    per_band: dict[str, int] = {}
    exact_total = 0
    for band in BANDS:
        hits = 0
        for index in range(20):
            seed = _profile_floor_seed(band, index)
            sample_index = seed % 7919 + index
            grid = GEN.generate(seed, sample_index, difficulty=band)
            assert GEN.self_check(grid) == []
            hits += _profile(grid) in canonical_profiles
        per_band[band] = hits
        exact_total += hits
    assert all(per_band[band] >= 1 for band in BANDS), per_band
    # This task's canonical envelope is exactly 19x19 with palette size 9..10,
    # so exact and envelope support coincide.
    assert exact_total >= 15, per_band


def test_semantic_contract_declares_real_rivals_and_canonical_shortcut():
    expected = {
        "include_outer_border",
        "sample_region_corners",
        "single_global_mode",
    }
    assert set(GEN.SEMANTIC_RIVALS) == expected
    assert set(GEN.LESSON_COMPETITORS) == expected
    assert set(GEN.CANONICAL_SHORTCUTS) == {"include_outer_border"}
    assert set(GEN.SEMANTIC_WITNESSES) == {
        "ignored_outer_border_changes_answer",
        "regional_modes_not_corner_samples",
        "four_regions_not_one_global_mode",
    }
    assert set(GEN.WITNESS_RIVALS) == set(GEN.SEMANTIC_WITNESSES)

    for profile in GEN.PUBLIC_PROFILES:
        grid = GEN.generate(7, 5, scene_profile=profile)
        assert GEN.CANONICAL_SHORTCUTS["include_outer_border"](grid) == GEN.rule_mirror(grid)

    witness = GEN.generate(7, 6, scene_profile="close_runner_up")
    assert GEN.SEMANTIC_WITNESSES["ignored_outer_border_changes_answer"](witness)
    assert GEN.SEMANTIC_RIVALS["include_outer_border"](witness) != GEN.rule_mirror(witness)


def test_each_semantic_witness_fires_and_refutes_its_claimed_rival_in_every_band():
    for band in BANDS:
        hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        for sample_index in range(40):
            grid = GEN.generate(4200 + sample_index, sample_index, difficulty=band)
            assert GEN.strict_canonical_like(grid) == []
            truth = GEN.rule_mirror(grid)
            for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                if not predicate(grid):
                    continue
                hits[name] += 1
                claimed = GEN.WITNESS_RIVALS[name]
                assert any(GEN.SEMANTIC_RIVALS[rival](grid) != truth for rival in claimed)
        assert all(count > 0 for count in hits.values()), (band, hits)


def test_every_three_demo_rotation_refutes_all_declared_competitors():
    # The production runner consumes four consecutive sample indexes for three
    # demonstrations plus one query. Check every cyclic held-out position over
    # both start residues and each difficulty band.
    for band in BANDS:
        for start in range(4):
            pairs = []
            for offset in range(4):
                grid = GEN.generate(7301 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for query_index in range(4):
                query = pairs[query_index]
                demos = pairs[:query_index] + pairs[query_index + 1 :]
                assert GEN.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    query_index,
                )
                for name, competitor in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        competitor(pair["input"]) != pair["output"] for pair in demos
                    ), (band, start, query_index, name)
