"""Regression contract for the a5e17b975ae0 chamber sampler repair."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    frames,
    load_generator,
    open_regions,
    profile,
    python_output,
    region_seed_counts,
    seed_positions,
)

from reviewer_support import canonical_pairs, find_root  # noqa: E402

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL = canonical_pairs("a5e17b975ae0", root=find_root(__file__))
CANONICAL_PROFILES = {
    (12, 17, 5),
    (12, 18, 5),
    (13, 19, 5),
    (13, 20, 5),
    (14, 19, 4),
}


def test_contract_is_source_bound_and_probeable():
    assert gen.RULE_HASH == "ced8e283e2c4"
    assert gen.VERSION != "2.0.1"
    assert set(gen.AXES) == {"grid_h", "grid_w", "seed_profile", "wall_profile"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert callable(gen.observe_overrides)
    assert callable(gen.strict_canonical_like)


@pytest.mark.parametrize("pair", CANONICAL, ids=lambda pair: str(profile(pair["input"])))
def test_canonical_examples_remain_lawful_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert python_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_hits_real_profiles_and_real_chambers(band):
    seen_profiles = set()
    seen_wall_profiles = set()
    seen_seed_profiles = set()
    for index in range(20):
        grid = gen.generate(7000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(7000 + index, index, difficulty=band)
        assert len(frames(grid)) == 2
        assert any(value == 5 for row in grid for value in row)
        counts = region_seed_counts(grid)
        assert counts and max(counts) == 1
        assert 0 in counts and 1 in counts
        assert python_output(grid) != grid
        observed = gen.observe_overrides(grid)
        seen_profiles.add(profile(grid))
        seen_wall_profiles.add(observed["wall_profile"])
        seen_seed_profiles.add(observed["seed_profile"])
    assert seen_profiles <= CANONICAL_PROFILES
    assert seen_profiles == CANONICAL_PROFILES
    assert seen_wall_profiles == {"cross_gap", "dual_cross", "cross_tee"}
    assert seen_seed_profiles == {"single", "separate", "partitioned"}


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h,grid_w", [(12, 17), (14, 20)])
@pytest.mark.parametrize("seed_profile", ["single", "separate", "partitioned"])
@pytest.mark.parametrize("wall_profile", ["cross_gap", "dual_cross", "cross_tee"])
def test_every_advertised_override_combination_is_exact(
    band, grid_h, grid_w, seed_profile, wall_profile
):
    options = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "seed_profile": seed_profile,
        "wall_profile": wall_profile,
    }
    grid = gen.generate(19, 7, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 11),
        ("grid_h", 15),
        ("grid_w", 16),
        ("grid_w", 21),
        ("grid_h", True),
        ("grid_w", "19"),
        ("seed_profile", "other"),
        ("wall_profile", "none"),
    ],
)
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_semantic_contract_names_real_wrong_rules():
    assert set(gen.SEMANTIC_RIVALS) == {"identity", "ignore_color5"}
    assert set(gen.LESSON_COMPETITORS) == {"identity", "ignore_color5"}
    for index in range(15):
        grid = gen.generate(901, index)
        intended = python_output(grid)
        assert gen.strict_canonical_like(grid) == []
        assert gen.SEMANTIC_WITNESSES["fillable_region"](grid)
        assert gen.SEMANTIC_WITNESSES["five_wall_partition"](grid)
        assert gen.SEMANTIC_RIVALS["identity"](grid) != intended
        assert gen.SEMANTIC_RIVALS["ignore_color5"](grid) != intended


@pytest.mark.parametrize(
    "mutation",
    ["stray_nine", "stray_five", "second_seed_same_region", "erase_all_seeds", "bad_color"],
)
def test_self_check_rejects_semantic_mutations(mutation):
    grid = gen.generate(44, 1, seed_profile="single", wall_profile="dual_cross")
    changed = deepcopy(grid)
    if mutation == "stray_nine":
        changed[0][0] = 9
    elif mutation == "stray_five":
        changed[0][0] = 5
    elif mutation == "erase_all_seeds":
        for r, c, _ in seed_positions(changed):
            changed[r][c] = 0
    elif mutation == "bad_color":
        r, c, _ = seed_positions(changed)[0]
        changed[r][c] = 10
    elif mutation == "second_seed_same_region":
        box = frames(changed)[0]
        region = next(
            region
            for region in open_regions(changed, box)
            if any(changed[r][c] not in (0, 5, 9) for r, c in region)
        )
        target = next((r, c) for r, c in sorted(region) if changed[r][c] == 0)
        changed[target[0]][target[1]] = 8
    assert gen.self_check(changed)


@pytest.mark.parametrize("index", range(5))
def test_difficulty_bands_rotate_the_schedule_without_leaving_the_manifold(index):
    bands = ("easy", "medium", "hard")
    names = [gen.schedule_profile(314, index, band) for band in bands]
    grids = [gen.generate(314, index, difficulty=band) for band in bands]
    assert len(set(names)) == len(bands)
    assert len({tuple(tuple(row) for row in grid) for grid in grids}) == len(bands)
    assert all(gen.strict_canonical_like(grid) == [] for grid in grids)
