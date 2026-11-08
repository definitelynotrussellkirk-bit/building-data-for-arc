"""Task-local regression suite for the hole-count recoloring generator."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    canonical_range_only_rival,
    components,
    cross_color_adjacencies,
    enclosed_cell_lookup_rival,
    foreground_area_lookup_rival,
    intended_output,
    load_generator,
    merged_foreground_rival,
    object_stats,
    racket_outputs,
    same_color_global_rival,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PROFILES = ("canonical", "equal_features", "touching", "extended")
BANDS = (None, "easy", "medium", "hard")


def _pair(grid):
    return {"input": grid, "output": intended_output(grid)}


def test_metadata_pins_selected_authority_and_small_honest_surface():
    assert gen.GENERATOR_ID == gen.TASK_ID == "9e80ef661ecc"
    assert gen.RULE_HASH == "609d24e8c088"
    assert gen.VERSION == "3.1.0"
    assert gen.EXAMPLES_NEEDED == 4
    assert gen.MIN_STRICT_FRAC == 1.0
    assert tuple(gen.SCHEDULE_PROFILES) == PROFILES
    assert set(gen.AXES) == {"profile"}
    assert gen.AXES["profile"].get("probe") == "diagnostic"


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_canonical_pairs_are_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", BANDS)
def test_default_schedule_covers_every_profile_in_each_four_example_window(band):
    for start in range(16):
        seen = [gen.observe_overrides(gen.generate(119, start + offset, difficulty=band))["profile"] for offset in range(4)]
        assert set(seen) == set(PROFILES)
        assert seen == [gen.schedule_profile(119, start + offset, band) for offset in range(4)]


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("profile", PROFILES)
def test_explicit_profile_override_is_honored_in_every_band(band, profile):
    grid = gen.generate(23, 7, difficulty=band, profile=profile)
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen.observe_overrides(grid) == {"profile": profile}
    assert gen.rule_mirror(grid) == intended_output(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"profile": "typo"},
        {"unknown_axis": 1},
        {"profile": 3},
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
def test_generated_distribution_is_valid_deterministic_and_oracle_aligned(band):
    unique = set()
    for index in range(64):
        grid = gen.generate(7000 + index, index * 5 + 1, difficulty=band)
        assert grid == gen.generate(7000 + index, index * 5 + 1, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == intended_output(grid)
        unique.add(repr(grid))
    assert len(unique) >= 45


def test_equal_feature_profile_refutes_area_enclosed_cell_and_global_color_shortcuts():
    grid = gen.generate(11, 0, profile="equal_features")
    stats = sorted(object_stats(grid), key=lambda item: item["holes"])
    assert 3 <= len(stats) <= 5
    assert {item["color"] for item in stats} == {stats[0]["color"]}
    assert {item["holes"] for item in stats} == {0, 1, 2}
    assert {item["area"] for item in stats} == {14}
    assert {item["bbox"] for item in stats} == {(4, 4)}
    truth = intended_output(grid)
    assert foreground_area_lookup_rival(grid) != truth
    assert enclosed_cell_lookup_rival(grid) != truth
    assert same_color_global_rival(grid) != truth


def test_touching_profile_refutes_nonzero_connectivity_merger():
    grid = gen.generate(12, 0, profile="touching")
    assert cross_color_adjacencies(grid)
    assert 4 <= len(components(grid)) <= 6
    truth = intended_output(grid)
    assert merged_foreground_rival(grid) != truth


def test_extended_profile_teaches_three_and_four_plus_hole_output_branches():
    grid = gen.generate(13, 0, profile="extended")
    stats = sorted(object_stats(grid), key=lambda item: item["holes"])
    assert {item["holes"] for item in stats} == set(range(7))
    truth = intended_output(grid)
    assert {value for row in truth for value in row if value} == {2, 3, 4, 6, 9}
    assert canonical_range_only_rival(grid) != truth


def test_strongest_canonical_shortcut_fits_every_canonical_but_generated_witness_refutes_it():
    assert all(foreground_area_lookup_rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    witness = gen.generate(29, 1, profile="equal_features")
    assert gen.CANONICAL_SHORTCUTS["foreground_area_lookup"](witness) != gen.rule_mirror(witness)
    witness_name = "diagnostic_profiles_refute_named_shortcuts"
    assert set(gen.SEMANTIC_WITNESSES) == {witness_name}
    assert gen.SEMANTIC_WITNESSES[witness_name](witness)
    assert set(gen.WITNESS_RIVALS[witness_name]) == set(gen.SEMANTIC_RIVALS)


@pytest.mark.parametrize("band", BANDS)
def test_every_consecutive_four_demo_lesson_refutes_all_named_competitors(band):
    for start in range(20):
        demos = [_pair(gen.generate(1000 + start, start + offset, difficulty=band)) for offset in range(4)]
        query = _pair(gen.generate(1000 + start, start + 4, difficulty=band))
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert not all(rival(pair["input"]) == pair["output"] for pair in demos), name


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 0], [0, 0]],
        [[10, 0], [0, 0]],
    ],
)
def test_malformed_grids_return_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)
    assert gen.strict_canonical_like(grid)


@pytest.mark.parametrize("profile", PROFILES)
def test_validator_rejects_structurally_invalid_mutations(profile):
    base = gen.generate(91, 2, profile=profile)
    mutations = []

    unknown_color = deepcopy(base)
    unknown_color[0][0] = 10
    mutations.append(unknown_color)

    boolean_cell = deepcopy(base)
    boolean_cell[0][0] = True
    mutations.append(boolean_cell)

    ragged = deepcopy(base)
    ragged[0].pop()
    mutations.append(ragged)

    # Border contact and a removed exterior pixel are now lawful. Test missing
    # teaching classes and oversized canvases instead of fixed-shape equality.
    mutations.append([[0] * len(base[0]) for _ in base])
    mutations.append([[0] * 31 for _ in range(31)])

    for changed in mutations:
        assert gen.self_check(changed), (profile, changed)


def test_generation_does_not_touch_process_global_rng():
    random.seed(991827)
    before = random.getstate()
    gen.generate(5, 8, profile="canonical")
    assert random.getstate() == before


def test_real_racket_authority_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(401 + i, i, profile=profile) for i, profile in enumerate(PROFILES)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]
