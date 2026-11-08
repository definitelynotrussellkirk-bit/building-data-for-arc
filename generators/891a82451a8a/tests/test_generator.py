"""Task-local regression tests for the repaired 891a82451a8a generator."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import random
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    CYCLE,
    canonical_pairs,
    competitor_is_ambiguous,
    expected_output,
    load_generator,
    observed,
)

gen = load_generator()


def _pinned_profile_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(
        f"profile-floor:v1:{gen.TASK_ID}:{band}:{index}".encode()
    ).hexdigest()
    return int(digest[:12], 16)


def _labeled_pair(seed: int, sample_index: int, band: str | None):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": expected_output(grid)}


def test_rule_hash_and_every_canonical_pair_are_owned():
    assert gen.RULE_HASH == "635140e0e1b3"
    for pair in canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert expected_output(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("region", ["corner", "edge", "center", "interior"])
def test_every_exact_axis_is_observable_and_honored(band, region):
    requested = {
        "grid_h": 18,
        "grid_w": 5,
        "bg_color": 7,
        "seed_color": 3,
        "seed_region": region,
    }
    grid = gen.generate(71, 13, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"grid_h": True},
        {"grid_w": 8.0},
        {"bg_color": "7"},
        {"seed_color": 7},
        {"seed_region": "spread"},
        {"grid_h": 4},
        {"grid_w": 19},
    ],
)
def test_invalid_or_stale_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_same_background_and_seed_are_structured_incompatible_overrides():
    with pytest.raises(ValueError) as caught:
        gen.generate(0, 0, bg_color=5, seed_color=5)
    assert set(caught.value.incompatible_axes) == {"bg_color", "seed_color"}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_defaults_are_deterministic_fresh_and_global_rng_pure(band):
    random.seed(891)
    state = random.getstate()
    first = gen.generate(103, 29, difficulty=band)
    second = gen.generate(103, 29, difficulty=band)
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = (first[0][0] + 1) % 10
    assert gen.generate(103, 29, difficulty=band) == second
    assert random.getstate() == state


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 5 for _ in range(5)]])
def test_malformed_inputs_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_self_check_rejects_destructive_seed_mutations():
    grid = gen.generate(14, 9, grid_h=8, grid_w=8, bg_color=7, seed_color=3)
    info = observed(grid)
    assert gen.self_check(grid) == []

    blank = [[info["bg_color"] for _ in row] for row in grid]
    assert gen.self_check(blank)

    doubled = deepcopy(grid)
    seed = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v != info["bg_color"])
    target = (0, 0) if seed != (0, 0) else (0, 1)
    doubled[target[0]][target[1]] = info["seed_color"]
    assert gen.self_check(doubled)

    bad_seed = deepcopy(grid)
    bad_seed[seed[0]][seed[1]] = 7 if info["bg_color"] != 7 else info["bg_color"]
    assert gen.self_check(bad_seed)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_covers_scale_palette_regions_and_canonical_profile(band):
    shapes, backgrounds, seed_colors, regions = set(), set(), set(), set()
    canonical_profile_hits = 0
    for index in range(144):
        grid = gen.generate(1300 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        stats = observed(grid)
        shapes.add((stats["grid_h"], stats["grid_w"]))
        backgrounds.add(stats["bg_color"])
        seed_colors.add(stats["seed_color"])
        regions.add(stats["seed_region"])
        canonical_profile_hits += (stats["grid_h"], stats["grid_w"], len({v for row in grid for v in row})) == (8, 8, 2)
        assert expected_output(grid) == gen.rule_mirror(grid)
    assert canonical_profile_hits > 0
    assert len(shapes) >= 20
    assert backgrounds == set(range(1, 10))
    assert seed_colors == set(CYCLE)
    assert regions == {"corner", "edge", "center", "interior"}



def test_zero_background_is_rejected_because_racket_mode_ignores_zero():
    with pytest.raises(ValueError):
        gen.generate(0, 0, bg_color=0, seed_color=5)
    invalid = [[0] * 5 for _ in range(5)]
    invalid[2][2] = 5
    assert gen.self_check(invalid)


def test_fixed_sample_index_still_varies_across_seed_families():
    grids = {
        repr(gen.generate(seed, 0, difficulty="medium"))
        for seed in range(40)
    }
    assert len(grids) >= 20

def test_pinned_profile_floor_meets_twenty_five_percent_in_every_band():
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            seed = _pinned_profile_seed(band, index)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            palette = {value for row in grid for value in row}
            hits += (len(grid), len(grid[0]), len(palette)) == (8, 8, 2)
        assert hits >= 5, (band, hits)


def test_declared_rivals_are_real_and_canonical_shortcut_really_fits_canonical():
    shortcut = gen.CANONICAL_SHORTCUTS["canonical_profile_only"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs())

    witness_counts = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for index in range(72):
        grid = gen.generate(900 + index, index)
        intended = expected_output(grid)
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                witness_counts[name] += 1
                for rival_name in gen.WITNESS_RIVALS[name]:
                    assert gen.SEMANTIC_RIVALS[rival_name](grid) != intended
    assert all(count > 0 for count in witness_counts.values())


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_cyclic_start_and_query_rotation_kills_declared_competitors(band):
    total = gen.EXAMPLES_NEEDED + 1
    for start in range(36):
        pairs = [_labeled_pair(5000 + start, start + offset, band) for offset in range(total)]
        for query_index in range(total):
            query = pairs[query_index]
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            assert not any(
                competitor_is_ambiguous(competitor, demos, query)
                for competitor in gen.LESSON_COMPETITORS.values()
            )


def test_rule_and_rivals_do_not_mutate_inputs():
    grid = gen.generate(42, 17)
    original = deepcopy(grid)
    assert gen.rule_mirror(grid) == expected_output(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
        assert grid == original
