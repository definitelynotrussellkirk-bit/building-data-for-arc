"""Focused regression, override, and semantic-contract tests for 6ecd6f93877b."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import random
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "6ecd6f93877b"
HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    clip_counts_at_three,
    load_generator,
    observed_axes,
    rule_output,
    truncate_to_six,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _pair(grid):
    return {"input": grid, "output": rule_output(grid)}


def test_authority_pin_and_honest_exact_axis_contract():
    assert gen.RULE_HASH == "66d1273fdbac"
    assert gen.VERSION == "3.0.0"
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_colors", "max_count"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_all_canonical_pairs_are_owned_and_rule_mirror_is_exact():
    assert len(PAIRS) == 5
    for pair in PAIRS:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert rule_output(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 5, "grid_w": 5, "n_colors": 2, "max_count": 1},
        {"grid_h": 7, "grid_w": 9, "n_colors": 3, "max_count": 3},
        {"grid_h": 10, "grid_w": 10, "n_colors": 5, "max_count": 4},
    ],
)
def test_every_declared_override_is_exact_observable_and_constructive(band, options):
    grid = gen.generate(917, 13, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed_axes(grid) == options
    assert gen.observe_overrides(grid) == options
    assert grid == gen.generate(917, 13, difficulty=band, **options)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"grid_h": 4},
        {"grid_h": 11},
        {"grid_w": 4},
        {"grid_w": 11},
        {"n_colors": 1},
        {"n_colors": 6},
        {"max_count": 0},
        {"max_count": 5},
        {"grid_h": True},
        {"grid_w": 7.0},
        {"n_colors": "3"},
        {"max_count": None},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_balances_canonical_anchors_and_shortcut_witnesses(band):
    for start in range(12):
        grids = [gen.generate(4000 + start, index, difficulty=band) for index in range(start, start + 4)]
        assert all(gen.self_check(grid) == [] for grid in grids)
        assert sum(gen.strict_canonical_like(grid) == [] for grid in grids) >= 2
        assert sum(observed_axes(grid)["max_count"] == 4 for grid in grids) >= 2
        assert sum(len(rule_output(grid)[0]) > 6 for grid in grids) >= 2


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_query_rotation_keeps_a_shortcut_counterexample_in_the_demos(band):
    for start in range(8):
        pairs = [_pair(gen.generate(8000 + start, index, difficulty=band)) for index in range(start, start + 4)]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []


def test_canonical_shortcuts_fit_authority_but_generated_broad_cases_refute_them():
    assert all(clip_counts_at_three(pair["input"]) == pair["output"] for pair in PAIRS)
    assert all(truncate_to_six(pair["input"]) == pair["output"] for pair in PAIRS)
    for index in range(1, 32, 2):
        grid = gen.generate(12000 + index, index)
        official = rule_output(grid)
        assert clip_counts_at_three(grid) != official
        assert truncate_to_six(grid) != official


def test_declared_semantic_contract_is_live_and_matches_independent_rivals():
    assert set(gen.SEMANTIC_WITNESSES) == {"count_above_three", "output_longer_than_six"}
    assert set(gen.SEMANTIC_RIVALS) == {"clip_counts_at_three", "truncate_to_six"}
    assert gen.CANONICAL_SHORTCUTS == gen.SEMANTIC_RIVALS
    assert gen.LESSON_COMPETITORS == gen.SEMANTIC_RIVALS
    assert gen.WITNESS_RIVALS == {
        "count_above_three": ["clip_counts_at_three"],
        "output_longer_than_six": ["truncate_to_six"],
    }
    for index in range(1, 16, 2):
        grid = gen.generate(16000 + index, index)
        assert gen.SEMANTIC_WITNESSES["count_above_three"](grid)
        assert gen.SEMANTIC_WITNESSES["output_longer_than_six"](grid)
        assert gen.SEMANTIC_RIVALS["clip_counts_at_three"](grid) == clip_counts_at_three(grid)
        assert gen.SEMANTIC_RIVALS["truncate_to_six"](grid) == truncate_to_six(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], "bad", [[True]], {}])
def test_malformed_inputs_are_diagnostic_not_exceptions(bad):
    assert gen.self_check(bad)
    for predicate in gen.SEMANTIC_WITNESSES.values():
        assert predicate(bad) is False


def test_self_check_rejects_out_of_manifold_counts_and_colors():
    too_many = [[0] * 5 for _ in range(5)]
    for r, c in ((0, 0), (0, 1), (0, 2), (0, 3), (0, 4)):
        too_many[r][c] = 2
    too_many[1][0] = 5
    assert any("1..4" in message for message in gen.self_check(too_many))

    one_color = [[0] * 5 for _ in range(5)]
    one_color[0][0] = 3
    one_color[1][1] = 3
    assert any("2..5" in message for message in gen.self_check(one_color))

    invalid_color = gen.generate(3, 1)
    invalid_color[0][0] = 10
    assert gen.self_check(invalid_color)


def test_replay_is_deterministic_and_does_not_touch_global_random_state():
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(314159, 27, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(314159, 27, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_curriculum_preserves_canonical_shrink_relation(band):
    for sample_index in range(40):
        grid = gen.generate(23000, sample_index, difficulty=band)
        output = rule_output(grid)
        assert len(output) == 1
        assert len(output[0]) <= len(grid[0])


def test_workspace_qualification_probe_catches_no_final_contract_failures():
    from qualify import qualify_generator

    report = qualify_generator(gen, starts_per_band=6)
    assert report["failures"] == []
    assert report["draws"] == 4 * 6 * 4
    assert report["canonical_anchors"] == 4 * 6 * 2
    assert report["shortcut_witnesses"] == 4 * 6 * 2
    assert report["rotation_checks"] == 4 * 6 * 4
    assert report["start_indices"] == list(range(6))
