"""Focused regression and semantic-contract tests for a8a8969ab4f1."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_HOME / "workspace"))
from reference_probe import analyze_pixels, canonical_pairs, intended_output, load_generator

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == "1130750019d1"


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_canonical_inputs_are_owned_and_match_the_rule(pair):
    assert gen.self_check(deepcopy(pair["input"])) == []
    assert intended_output(pair["input"]) == pair["output"]


def test_public_axes_are_small_literal_and_pixel_observable():
    assert set(gen.AXES) == {"shape", "row_pattern", "key_color_pattern", "marker_profile"}
    for axis in gen.AXES.values():
        assert axis.get("probe") != "diagnostic"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_honored_in_every_band(band):
    options = {
        "shape": "8x10",
        "row_pattern": "clustered",
        "key_color_pattern": "mixed",
        "marker_profile": "mixed",
    }
    grid = gen.generate(17, 5, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": "8x10"},
        {"shape": "5x7"},
        {"shape": 8},
        {"row_pattern": "diagonal"},
        {"key_color_pattern": "all_unique-ish"},
        {"marker_profile": "four_each"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


def test_default_schedule_is_rotation_robust_for_unkeyed_marker_witness():
    grids = [gen.generate(73, index, difficulty="medium") for index in range(12)]
    witness = gen.SEMANTIC_WITNESSES["unkeyed_marker_preservation"]
    observed = [witness(grid) for grid in grids]
    assert observed == [index % 3 != 0 for index in range(12)]
    # Any 4-pair production window retains a witness after any one query is held out.
    for start in range(9):
        window = grids[start : start + 4]
        for held_out in range(4):
            demos = [grid for index, grid in enumerate(window) if index != held_out]
            assert any(witness(grid) for grid in demos)


def test_canonical_shortcut_fits_public_pairs_but_generated_witness_refutes_it():
    rival = gen.CANONICAL_SHORTCUTS["erase_unkeyed_markers"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    witness_grid = gen.generate(91, 1, shape="7x9", key_color_pattern="distinct")
    assert gen.SEMANTIC_WITNESSES["unkeyed_marker_preservation"](witness_grid)
    assert rival(witness_grid) != intended_output(witness_grid)


def test_lesson_identifiability_survives_all_query_rotations():
    pairs = []
    for index in range(4):
        grid = gen.generate(211, index, difficulty="hard")
        pairs.append({"input": grid, "output": intended_output(grid)})
    for held_out in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != held_out]
        assert gen.lesson_identifiable(demos, pairs[held_out]) == []


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(6)]])
def test_malformed_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_generated_distribution_is_deterministic_and_covers_declared_profiles():
    seen = {name: set() for name in gen.AXES}
    for index in range(180):
        grid = gen.generate(1200 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        assert grid == gen.generate(1200 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        assert gen.self_check(grid) == []
        facts = gen.observe_overrides(grid)
        for name, value in facts.items():
            seen[name].add(value)
    assert seen["shape"] == {"6x8", "7x9", "8x10"}
    assert seen["row_pattern"] == {"alternating", "clustered", "scattered"}
    assert seen["key_color_pattern"] == {"distinct", "mixed", "repeated"}
    assert seen["marker_profile"] == {"one_each", "two_each", "three_each", "mixed"}


def test_validator_rejects_destructive_mutations():
    base = gen.generate(31, 0, shape="6x8", key_color_pattern="distinct")
    mutations = []

    extra_key = deepcopy(base)
    blank = next(r for r, row in enumerate(extra_key) if row[0] == 0)
    extra_key[blank][0] = 4
    mutations.append(extra_key)

    remove_markers = deepcopy(base)
    active = next(r for r, row in enumerate(remove_markers) if row[0] != 0)
    remove_markers[active] = [remove_markers[active][0]] + [0] * (len(remove_markers[active]) - 1)
    mutations.append(remove_markers)

    illegal_color = deepcopy(base)
    illegal_color[0][1] = 5
    mutations.append(illegal_color)

    for mutated in mutations:
        assert gen.self_check(mutated)


def test_probe_and_observer_agree_on_generated_structure():
    grid = gen.generate(
        19,
        2,
        shape="8x10",
        row_pattern="scattered",
        key_color_pattern="repeated",
        marker_profile="three_each",
    )
    facts = analyze_pixels(grid)
    observed = gen.observe_overrides(grid)
    assert observed["shape"] == facts["shape"]
    assert len(facts["active_rows"]) == 3
    assert len(set(facts["key_colors"])) == 1
    assert facts["marker_counts"] == [3, 3, 3]


def test_qualification_harness_checks_all_schedule_phases_and_declared_shortcuts():
    from qualify import run_qualification

    report = run_qualification(gen, starts_per_band=6, seed=404)
    assert report["status"] == "passed"
    assert report["summary"]["windows"] == 18
    assert report["summary"]["rotations"] == 72
    assert report["summary"]["ambiguous_rotations"] == 0
    assert report["summary"]["invalid_inputs"] == 0
    assert report["schedule_profiles"] == {
        "canonical_anchor": 24,
        "unkeyed_marker_witness": 48,
    }
    assert report["canonical_shortcuts"] == {"erase_unkeyed_markers": "fits_all_canonical_pairs"}
