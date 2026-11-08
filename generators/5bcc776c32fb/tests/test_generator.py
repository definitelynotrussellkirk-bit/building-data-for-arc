"""Regression and semantic-contract tests for generator 5bcc776c32fb."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))

from reference_probe import (
    canonical_pairs,
    features,
    intended_output,
    load_generator,
    observed,
    rival_color_blind,
    rival_lengths_357,
    rival_no_minimum,
    shortcut_witness,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {(8, 10, 3), (8, 11, 3), (9, 12, 3), (10, 13, 3)}


@pytest.mark.parametrize("pair", canonical_pairs())
def test_canonical_pairs_match_oracle_and_are_accepted(pair):
    assert intended_output(pair["input"]) == pair["output"]
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []


def test_rule_pin_and_unknown_override_rejection():
    assert gen.RULE_HASH == "51414a828017"
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, __override_contract_unknown_axis__=123)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(8, 10), (8, 13), (10, 10), (10, 13)])
@pytest.mark.parametrize("n_targets", [1, 2])
@pytest.mark.parametrize("distractor_color", [4, 9])
def test_exact_overrides_are_observable_in_every_band(
    band, height, width, n_targets, distractor_color
):
    options = {
        "grid_h": height,
        "grid_w": width,
        "n_targets": n_targets,
        "distractor_color": distractor_color,
    }
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 7),
        ("grid_h", 11),
        ("grid_w", 9),
        ("grid_w", 14),
        ("n_targets", 0),
        ("n_targets", 3),
        ("distractor_color", 0),
        ("distractor_color", 1),
        ("distractor_color", 2),
        ("distractor_color", 8),
        ("grid_h", True),
        ("n_targets", 1.0),
        ("distractor_color", "7"),
    ],
)
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError, KeyError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_has_canonical_profiles_and_teaching_witnesses(band):
    profile_hits = 0
    feature_counts = {name: 0 for name in features(shortcut_witness())}
    distinct = set()
    for index in range(96):
        grid = gen.generate(1200 + index, index * 11 + 3, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(1200 + index, index * 11 + 3, difficulty=band)
        assert len({value for row in grid for value in row}) == 3
        profile_hits += (len(grid), len(grid[0]), 3) in CANONICAL_PROFILES
        for name, present in features(grid).items():
            feature_counts[name] += bool(present)
        distinct.add(tuple(tuple(row) for row in grid))
    assert profile_hits >= 48
    assert len(distinct) >= 90
    assert feature_counts["positive_target"] == 96
    assert feature_counts["length9_target"] == 96
    for scheduled in (
        "even_horizontal_negative",
        "vertical_negative",
        "junction_negative",
        "singleton_negative",
        "color_specific_distractor",
    ):
        assert feature_counts[scheduled] == 64


def test_declared_canonical_shortcuts_fit_all_canonical_pairs():
    shortcuts = {
        "color_blind": rival_color_blind,
        "no_minimum": rival_no_minimum,
        "lengths_357": rival_lengths_357,
    }
    for name, rival in shortcuts.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs()), name
        assert gen.CANONICAL_SHORTCUTS[name] is not None


def test_generated_curriculum_refutes_every_declared_rival_and_fires_witnesses():
    for band in (None, "easy", "medium", "hard"):
        grids = [gen.generate(712, sample_index, difficulty=band) for sample_index in range(3)]
        witness_rows = [
            {name: predicate(grid) for name, predicate in gen.SEMANTIC_WITNESSES.items()}
            for grid in grids
        ]
        assert all(any(row[name] for row in witness_rows) for name in gen.BRANCH_WITNESSES)

        rival_refuted = {name: False for name in gen.SEMANTIC_RIVALS}
        for grid, witness_results in zip(grids, witness_rows):
            expected = intended_output(grid)
            for witness, rivals in gen.WITNESS_RIVALS.items():
                if witness_results[witness]:
                    for rival_name in rivals:
                        assert gen.SEMANTIC_RIVALS[rival_name](grid) != expected
                        rival_refuted[rival_name] = True
        assert all(rival_refuted.values())


def test_color_blind_shortcut_has_exact_reproducible_counterexample():
    grid = shortcut_witness()
    intended = intended_output(grid)
    shortcut = rival_color_blind(grid)
    assert [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if intended[row][col] != shortcut[row][col]
    ] == [(5, 6)]
    assert gen.CANONICAL_SHORTCUTS["color_blind"](grid) == shortcut


def test_lesson_contract_passes_ordered_and_rotated_generated_lessons():
    pairs = []
    for index in range(4):
        grid = gen.generate(884, index * 11, difficulty="hard")
        pairs.append({"input": grid, "output": intended_output(grid)})
    assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
    for query_index in range(len(pairs)):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == []


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(8)]])
def test_self_check_reports_malformed_grids_without_raising(bad):
    assert gen.self_check(bad)


def test_generation_does_not_mutate_global_random_or_return_aliases():
    random.seed(9182)
    before = random.getstate()
    first = gen.generate(55, 8, difficulty="hard")
    assert random.getstate() == before
    second = gen.generate(55, 8, difficulty="hard")
    assert first == second
    changed = deepcopy(first)
    changed[0][0] = (changed[0][0] + 1) % 10
    assert changed != gen.generate(55, 8, difficulty="hard")


def test_real_racket_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    from reference_probe import racket_outputs

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()] + [shortcut_witness()]
    grids += [gen.generate(319, index, difficulty=("easy", "medium", "hard")[index % 3]) for index in range(12)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]


def test_reference_probe_audit_runs_requested_count_per_band():
    from reference_probe import audit

    report, grids = audit(gen, 2)
    assert report["passed"] is True
    assert all(section["counts"]["samples"] == 2 for section in report["bands"].values())
    assert report["curriculum"]["ambiguous_rotations"] == 0
    assert report["curriculum"]["checked_rotations"] > 0
    assert len(grids) >= len(canonical_pairs()) + 1


@pytest.mark.parametrize(
    "sample_index,expected_true,expected_false,expected_objects",
    [
        (0, {"even_horizontal_negative", "vertical_negative", "junction_negative"},
         {"singleton_negative", "color_specific_distractor"}, 5),
        (1, {"singleton_negative", "junction_negative", "color_specific_distractor"},
         {"even_horizontal_negative", "vertical_negative"}, 4),
        (2, {"even_horizontal_negative", "vertical_negative", "singleton_negative", "color_specific_distractor"},
         {"junction_negative"}, 5),
    ],
)
def test_three_profile_curriculum_stays_canonical_scale(
    sample_index, expected_true, expected_false, expected_objects
):
    from reference_probe import components

    grid = gen.generate(42, sample_index, difficulty="medium", n_targets=1)
    present = features(grid)
    assert all(present[name] for name in expected_true)
    assert not any(present[name] for name in expected_false)
    assert len(components(grid)) == expected_objects
