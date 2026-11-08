from __future__ import annotations

import hashlib
import importlib
import importlib.util
from pathlib import Path
from copy import deepcopy
import random

import pytest


TASK_ID = "8a50bfdecd97"
try:
    gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
except ModuleNotFoundError:
    source = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", source)
    assert spec is not None and spec.loader is not None
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)


def _pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _profile(grid):
    return (len(grid), len(grid[0]), len({cell for row in grid for cell in row}))


def test_generate_rejects_nonliteral_seed_and_invalid_sample_index():
    for bad_seed in (True, False, 1.0, 1.75, "1"):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(bad_seed, 0)
    for bad_index in (True, False, 1.0, 1.75, "1", -1):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(991, bad_index)


def test_default_schedule_meets_strict_canonical_profile_floor():
    canonical_profiles = {_profile(grid) for grid in gen._PUBLIC_INPUTS.values()}
    hs = [value[0] for value in canonical_profiles]
    ws = [value[1] for value in canonical_profiles]
    ps = [value[2] for value in canonical_profiles]
    envelope = ((min(hs), max(hs)), (min(ws), max(ws)), (min(ps), max(ps)))

    exact_by_band = {}
    envelope_hits = 0
    for band in ("easy", "medium", "hard"):
        exact = 0
        for index in range(20):
            seed = _pinned_seed(band, index)
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=band)
            profile = _profile(grid)
            exact += profile in canonical_profiles
            envelope_hits += (
                envelope[0][0] <= profile[0] <= envelope[0][1]
                and envelope[1][0] <= profile[1] <= envelope[1][1]
                and envelope[2][0] <= profile[2] <= envelope[2][1]
            )
        exact_by_band[band] = exact

    assert all(count >= 1 for count in exact_by_band.values()), exact_by_band
    assert envelope_hits >= 15, exact_by_band


def test_semantic_contract_declares_executable_witnesses_and_rivals():
    assert callable(getattr(gen, "strict_canonical_like", None))
    assert callable(getattr(gen, "lesson_identifiable", None))
    assert set(gen.SEMANTIC_RIVALS) == {"copy_instead_of_move", "solid_bbox"}
    assert set(gen.SEMANTIC_WITNESSES) == {"source_erasure", "transparent_bitmap"}
    assert gen.WITNESS_RIVALS == {
        "source_erasure": ["copy_instead_of_move"],
        "transparent_bitmap": ["solid_bbox"],
    }
    assert gen.LESSON_COMPETITORS == gen.SEMANTIC_RIVALS

    hollow = gen.generate(17, 23, scene_profile="pattern_hollow3")
    assert gen.strict_canonical_like(hollow) == []
    expected = gen.rule_mirror(hollow)
    for rival in gen.SEMANTIC_RIVALS.values():
        assert rival(deepcopy(hollow)) != expected
    assert gen.SEMANTIC_WITNESSES["source_erasure"](hollow)
    assert gen.SEMANTIC_WITNESSES["transparent_bitmap"](hollow)


def test_lesson_identifiable_catches_solid_bbox_shortcut():
    demos = []
    for index, profile in enumerate(("pattern_pixel", "pattern_block2", "pattern_hbar3")):
        grid = gen.generate(100 + index, index, scene_profile=profile)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})

    query_input = gen.generate(211, 3, scene_profile="pattern_hollow3")
    reasons = gen.lesson_identifiable(demos, {"input": query_input})
    assert any("solid_bbox" in reason for reason in reasons), reasons


def test_canonical_scale_variants_preserve_scene_profile_provenance():
    for profile, public in gen._PUBLIC_INPUTS.items():
        observed = {
            gen.observe_overrides(gen._public_variant(public, random.Random(seed)))[
                "scene_profile"
            ]
            for seed in range(24)
        }
        assert observed == {profile}


def test_every_four_pair_lesson_has_two_transparent_bitmap_witnesses():
    assert gen.LESSON_SCHEDULE_PERIOD == 2
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for start in range(8):
                witnesses = [
                    gen.SEMANTIC_WITNESSES["transparent_bitmap"](
                        gen.generate(seed, sample_index, difficulty=band)
                    )
                    for sample_index in range(start, start + 4)
                ]
                assert sum(witnesses) >= 2, (band, seed, start, witnesses)
