"""Task-local regression suite for total plus-growth size as a bar."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    PROFILE_NAMES,
    canonical_pairs,
    canonical_shortcuts_fit,
    clipped_sum_without_union_rival,
    edge_seed_count,
    five_per_seed_rival,
    intended_output,
    load_generator,
    overlap_pairs,
    pair,
    profile_signature,
    seeds,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")


def test_metadata_pins_authority_and_has_one_honest_public_axis():
    assert gen.GENERATOR_ID == gen.TASK_ID == "cf787ae40567"
    assert gen.RULE_HASH == "5d3366b26415"
    assert gen.VERSION == "2.0.0"
    assert gen.EXAMPLES_NEEDED == 4
    assert gen.MIN_STRICT_FRAC == 1.0
    assert tuple(gen.SCHEDULE_PROFILES) == PROFILE_NAMES
    assert set(gen.AXES) == {"profile"}
    assert gen.AXES["profile"].get("probe") == "diagnostic"


@pytest.mark.parametrize("item", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_pairs_are_accepted_and_match_independent_oracle(item):
    assert gen.self_check(item["input"]) == []
    assert gen.strict_canonical_like(item["input"]) == []
    assert intended_output(item["input"]) == item["output"]
    assert gen.rule_mirror(item["input"]) == item["output"]


@pytest.mark.parametrize("band", BANDS)
def test_every_four_consecutive_default_examples_cover_all_profiles(band):
    for start in range(12):
        observed = [
            gen.observe_overrides(gen.generate(109, start + offset, difficulty=band))["profile"]
            for offset in range(4)
        ]
        assert set(observed) == set(PROFILE_NAMES)
        assert observed == [
            gen.schedule_profile(109, start + offset, band) for offset in range(4)
        ]


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("profile", PROFILE_NAMES)
def test_explicit_profile_override_is_observable_and_rule_correct(band, profile):
    grid = gen.generate(37, 11, difficulty=band, profile=profile)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid) == {"profile": profile}
    assert gen.rule_mirror(grid) == intended_output(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"profile": "typo"},
        {"profile": 3},
        {"unknown_axis": 1},
    ],
)
def test_invalid_overrides_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("difficulty", ["trivial", 0.5, True])
def test_invalid_difficulty_fails_closed(difficulty):
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", BANDS)
def test_profile_topologies_are_distinct_and_intentional(band):
    grids = {
        profile: gen.generate(71, 5, difficulty=band, profile=profile)
        for profile in PROFILE_NAMES
    }
    sig = {name: profile_signature(grid) for name, grid in grids.items()}

    canonical = sig["canonical"]
    assert canonical["shape"] in {(7, 7), (8, 8), (9, 9)}
    assert canonical["edge_seed_count"] == 0
    assert canonical["overlap_pair_count"] == 0
    assert set(canonical["seed_colors"]) == {2}

    overlap = sig["overlap"]
    assert overlap["edge_seed_count"] == 0
    assert overlap["overlap_pair_count"] == 1
    assert overlap["distinct_seed_colors"] == overlap["seed_count"]

    edge = sig["edge"]
    assert edge["edge_seed_count"] >= 1
    assert edge["overlap_pair_count"] == 0
    assert edge["distinct_seed_colors"] == 1

    mixed = sig["mixed"]
    assert mixed["edge_seed_count"] >= 1
    assert mixed["overlap_pair_count"] == 1
    assert mixed["distinct_seed_colors"] == mixed["seed_count"]


@pytest.mark.parametrize("band", BANDS)
def test_generated_distribution_is_deterministic_diverse_and_arc_sized(band):
    serialized = set()
    shapes = set()
    profiles = set()
    for index in range(80):
        grid = gen.generate(500 + index, index * 7 + 3, difficulty=band)
        assert grid == gen.generate(500 + index, index * 7 + 3, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == intended_output(grid)
        assert 1 <= len(intended_output(grid)[0]) <= 30
        serialized.add(repr(grid))
        shapes.add((len(grid), len(grid[0])))
        profiles.add(gen.observe_overrides(grid)["profile"])
    assert len(serialized) >= 50
    assert len(shapes) >= 3
    assert profiles == set(PROFILE_NAMES)


def test_canonical_fitting_shortcuts_are_real_and_generated_counterexamples_exist():
    assert canonical_shortcuts_fit() == {
        "five_per_seed": True,
        "clipped_sum_without_union": True,
    }
    witnesses = {
        profile: gen.generate(13, 2, profile=profile)
        for profile in ("overlap", "edge", "mixed")
    }
    assert five_per_seed_rival(witnesses["edge"]) != intended_output(witnesses["edge"])
    assert five_per_seed_rival(witnesses["overlap"]) != intended_output(witnesses["overlap"])
    assert clipped_sum_without_union_rival(witnesses["overlap"]) != intended_output(witnesses["overlap"])
    assert clipped_sum_without_union_rival(witnesses["mixed"]) != intended_output(witnesses["mixed"])


def test_declared_semantic_contract_names_real_rivals_and_witnesses():
    assert set(gen.CANONICAL_SHORTCUTS) == {
        "five_per_seed",
        "clipped_sum_without_union",
    }
    assert set(gen.CANONICAL_SHORTCUTS) <= set(gen.SEMANTIC_RIVALS)
    assert set(gen.LESSON_COMPETITORS) == set(gen.SEMANTIC_RIVALS)
    assert set(gen.SEMANTIC_WITNESSES) == {"edge_clipping", "overlap_deduplication"}
    assert gen.WITNESS_RIVALS["edge_clipping"] == ["five_per_seed"]
    assert set(gen.WITNESS_RIVALS["overlap_deduplication"]) == {
        "five_per_seed",
        "clipped_sum_without_union",
    }


@pytest.mark.parametrize("band", BANDS)
def test_every_consecutive_four_demo_lesson_eliminates_named_rivals(band):
    for start in range(12):
        demos = [pair(gen.generate(991, start + offset, difficulty=band)) for offset in range(4)]
        query = pair(gen.generate(991, start + 4, difficulty=band))
        assert gen.lesson_identifiable(demos, query) == []
        for rival in gen.LESSON_COMPETITORS.values():
            assert not all(rival(item["input"]) == item["output"] for item in demos)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 7 for _ in range(7)],
        [[0] * 7 for _ in range(7)],
        [[8 if (r, c) == (3, 3) else 0 for c in range(7)] for r in range(7)],
        [[2] * 7 for _ in range(7)],
    ],
)
def test_self_check_rejects_malformed_or_out_of_grammar_inputs(grid):
    assert gen.self_check(grid)


def test_self_check_rejects_structure_destroying_mutations():
    base = gen.generate(17, 3, profile="mixed")
    mutations = []

    all_background = [[0 for _ in row] for row in base]
    mutations.append(all_background)

    reserved_color = deepcopy(base)
    r, c, _ = seeds(reserved_color)[0]
    reserved_color[r][c] = 8
    mutations.append(reserved_color)

    too_many = deepcopy(base)
    for r in range(len(too_many)):
        for c in range(len(too_many[0])):
            if too_many[r][c] == 0:
                too_many[r][c] = 2
                if len(seeds(too_many)) > 6:
                    break
        if len(seeds(too_many)) > 6:
            break
    mutations.append(too_many)

    for changed in mutations:
        assert gen.self_check(changed)


def test_rule_mirror_is_pure():
    grid = gen.generate(31, 3, profile="mixed")
    original = deepcopy(grid)
    output = gen.rule_mirror(grid)
    assert grid == original
    assert output == intended_output(grid)
    assert output is not grid


def test_profile_schedule_rotates_across_seed_roots_as_well_as_sample_indices():
    observed = [gen.schedule_profile(seed, 1, "hard") for seed in range(4)]
    assert set(observed) == set(PROFILE_NAMES)


def test_declared_count_bar_codomain_is_exact_and_exhausted_by_probe_schedule():
    assert gen.EXPECTED_OUTPUT_CODOMAIN == 24
    widths = {
        len(gen.rule_mirror(gen.generate(episode * 101, sample_index))[0])
        for episode in range(24)
        for sample_index in range(6)
    }
    assert widths == set(range(5, 29))


def test_pinned_profile_floor_clears_cross_band_and_rate_thresholds():
    per_band = {}
    for band in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:cf787ae40567:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            sample_index = seed % 7919 + index
            hits += gen.schedule_profile(seed, sample_index, band) == "canonical"
        per_band[band] = hits
    assert min(per_band.values()) >= 1
    assert sum(per_band.values()) >= 15


def test_lesson_probe_tool_reports_a_clean_compact_census():
    from lesson_probe import run_probe

    report = run_probe(seed_roots=range(2), starts=range(2))
    assert report["status"] == "pass"
    assert report["failures"] == []
    assert report["lessons"] == 12
    assert set(report["output_widths_observed"]) <= set(gen.EXPECTED_OUTPUT_WIDTHS)
    assert report["canonical_shortcuts_fit"] == {
        "five_per_seed": True,
        "clipped_sum_without_union": True,
    }
    assert report["rival_refutations"] == {
        "five_per_seed": 12,
        "clipped_sum_without_union": 12,
    }
