"""Task-local regressions for ba0c6a5828f9's teaching distribution."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    ROOT,
    TASK_ID,
    canonical_pairs,
    full_orbits_only_rival,
    geometric_center_rival,
    has_clipped_marker,
    intended_output,
    load_generator,
    markers,
    observed_profile,
    pivot,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PROFILES = ("canonical", "off_center", "clipped", "mixed")
BANDS = (None, "easy", "medium", "hard")


def labelled(grid):
    return {"input": deepcopy(grid), "output": intended_output(grid)}


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_canonical_pairs_match_independent_geometry_and_validator(pair):
    assert intended_output(pair["input"]) == pair["output"]
    assert gen.self_check(pair["input"]) == []


def test_rule_hash_and_selected_authority_are_exactly_synchronized():
    assert gen.RULE_HASH == "e28fcc7b8767"
    canonical_path = ROOT / "shared/data/canonical/puzzles.jsonl"
    canonical = next(json.loads(line) for line in canonical_path.read_text().splitlines()
                     if json.loads(line).get("task_id") == TASK_ID)
    selected = json.loads((ROOT / "shared/data/base/solutions/banks/0d92044d8ccc/H20__ba0c6a5828f9.json").read_text())
    assert selected["racket_target"]["target_code"] == canonical["program_solution"]
    assert selected["racket_target"]["raw_code"] == canonical["program_solution"]


def test_metadata_advertises_only_the_exact_profile_control():
    assert tuple(gen.SCHEDULE_PROFILES) == PROFILES
    assert tuple(gen.AXES) == ("profile",)
    assert tuple(gen.AXES["profile"]["valid"]) == PROFILES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("profile", PROFILES)
def test_each_profile_override_is_exact_and_observable_in_every_band(band, profile):
    grid = gen.generate(41, 7, difficulty=band, profile=profile)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"profile": profile}
    assert observed_profile(grid) == profile
    assert grid == gen.generate(41, 7, difficulty=band, profile=profile)


@pytest.mark.parametrize("kwargs", [
    {"typo": "canonical"},
    {"profile": "not-a-profile"},
])
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("band", BANDS)
def test_schedule_is_complete_in_every_consecutive_four_pairs(band):
    for seed in range(8):
        for start in range(12):
            profiles = [gen.schedule_profile(seed, start + offset, band) for offset in range(4)]
            assert set(profiles) == set(PROFILES)
            grids = [gen.generate(seed, start + offset, difficulty=band) for offset in range(4)]
            assert [gen.observe_overrides(grid)["profile"] for grid in grids] == profiles


@pytest.mark.parametrize("profile,off_center,clipped", [
    ("canonical", False, False),
    ("off_center", True, False),
    ("clipped", False, True),
    ("mixed", True, True),
])
def test_profiles_isolate_the_two_hidden_rule_branches(profile, off_center, clipped):
    for seed in range(16):
        grid = gen.generate(seed, 3, profile=profile)
        pr, pc = pivot(grid)
        assert ((pr, pc) != (len(grid) // 2, len(grid[0]) // 2)) is off_center
        assert has_clipped_marker(grid) is clipped
        assert intended_output(grid) != grid


def test_canonical_shortcuts_fit_all_public_pairs_and_generated_witnesses_refute_them():
    for pair in canonical_pairs():
        assert geometric_center_rival(pair["input"]) == pair["output"]
        assert full_orbits_only_rival(pair["input"]) == pair["output"]

    off_center = gen.generate(73, 0, profile="off_center")
    clipped = gen.generate(73, 1, profile="clipped")
    mixed = gen.generate(73, 2, profile="mixed")
    assert geometric_center_rival(off_center) != intended_output(off_center)
    assert full_orbits_only_rival(off_center) == intended_output(off_center)
    assert geometric_center_rival(clipped) == intended_output(clipped)
    assert full_orbits_only_rival(clipped) != intended_output(clipped)
    assert geometric_center_rival(mixed) != intended_output(mixed)
    assert full_orbits_only_rival(mixed) != intended_output(mixed)


def test_declared_semantic_contract_matches_independent_rivals():
    assert set(gen.CANONICAL_SHORTCUTS) == {"geometric_center", "full_orbits_only"}
    assert set(gen.SEMANTIC_RIVALS) == set(gen.CANONICAL_SHORTCUTS)
    assert set(gen.LESSON_COMPETITORS) == set(gen.CANONICAL_SHORTCUTS)
    assert set(gen.SEMANTIC_WITNESSES) == {"off_center_pivot", "edge_clipping"}
    assert gen.WITNESS_RIVALS == {
        "off_center_pivot": ["geometric_center"],
        "edge_clipping": ["full_orbits_only"],
    }
    for profile in PROFILES:
        grid = gen.generate(503, 2, profile=profile)
        assert gen.rule_mirror(grid) == intended_output(grid)
        assert gen.SEMANTIC_RIVALS["geometric_center"](grid) == geometric_center_rival(grid)
        assert gen.SEMANTIC_RIVALS["full_orbits_only"](grid) == full_orbits_only_rival(grid)


@pytest.mark.parametrize("band", BANDS)
def test_every_three_of_four_rotation_is_identifiable_against_named_rivals(band):
    for seed in range(8):
        pairs = [labelled(gen.generate(seed, index, difficulty=band)) for index in range(4)]
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = pairs[query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for rival in gen.LESSON_COMPETITORS.values():
                assert not all(rival(item["input"]) == item["output"] for item in demos)


@pytest.mark.parametrize("band", BANDS)
def test_distribution_is_deterministic_valid_and_diverse(band):
    serialized = set()
    shapes = set()
    counts = set()
    profiles = set()
    for index in range(128):
        grid = gen.generate(1000 + index, index * 11 + 5, difficulty=band)
        assert grid == gen.generate(1000 + index, index * 11 + 5, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == intended_output(grid)
        serialized.add(repr(grid))
        shapes.add((len(grid), len(grid[0])))
        counts.add(len(markers(grid)))
        profiles.add(gen.observe_overrides(grid)["profile"])
    assert len(serialized) >= 120
    assert len(shapes) >= 8
    assert len(counts) >= 2
    assert profiles == set(PROFILES)


def test_rule_mirror_is_pure_and_returns_fresh_rows():
    grid = gen.generate(89, 3, profile="mixed")
    original = deepcopy(grid)
    output = gen.rule_mirror(grid)
    assert grid == original
    assert output == intended_output(grid)
    assert output is not grid
    assert all(a is not b for a, b in zip(output, grid))


@pytest.mark.parametrize("grid", [
    None,
    [],
    [[]],
    [[0], [0, 1]],
    [[True] * 7 for _ in range(7)],
    [[0] * 7 for _ in range(7)],
])
def test_validator_rejects_malformed_inputs_without_throwing(grid):
    assert gen.self_check(grid)


def test_validator_rejects_structure_destroying_mutations():
    base = gen.generate(91, 4, profile="mixed")
    mutations = []

    no_pivot = deepcopy(base)
    pr, pc = pivot(no_pivot)
    no_pivot[pr][pc] = 0
    mutations.append(no_pivot)

    extra_pivot = deepcopy(base)
    extra_pivot[0][0] = 2
    mutations.append(extra_pivot)

    no_markers = [[0 if value == 1 else value for value in row] for row in base]
    mutations.append(no_markers)

    bad_color = deepcopy(base)
    bad_color[0][0] = 9
    mutations.append(bad_color)

    for changed in mutations:
        assert gen.self_check(changed)
