"""Task-local regression tests for the diagonal-block mini-grid generator.

Expected outputs come from the independent pixel oracle in
``workspace/reference_probe.py`` rather than production helper functions.
"""
from __future__ import annotations

from copy import deepcopy
import itertools
import json
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    always_anti_output,
    always_main_output,
    canonical_pairs,
    counterexample_input,
    gap_parity_output,
    inverse_gap_parity_output,
    load_generator,
    observed,
    racket_outputs,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

EXPECTED_AXES = {"gap_row", "gap_col", "marker_corner", "block_color"}
COLORS = (1, 3, 4, 5, 6, 7, 8, 9)


def test_rule_pin_and_honest_axis_surface():
    assert getattr(gen, "RULE_HASH", None) == "39724c7d06e2"
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.EXAMPLES_NEEDED == 3


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_accepts_all_canonical_pairs_and_independent_oracle_matches(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert pair["input"] == original
    assert rule_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_exact_override_cartesian_is_constructive_and_observable(difficulty):
    for index, (gap_row, gap_col, marker_corner, block_color) in enumerate(
        itertools.product(range(3), range(3), range(4), COLORS)
    ):
        requested = {
            "gap_row": gap_row,
            "gap_col": gap_col,
            "marker_corner": marker_corner,
            "block_color": block_color,
        }
        grid = gen.generate(91_000 + index, index, difficulty=difficulty, **requested)
        assert gen.self_check(grid) == [], requested
        assert observed(grid) == requested
        assert gen.observe_overrides(grid) == requested
        assert gen.rule_mirror(grid) == rule_output(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"gap_row": -1},
        {"gap_row": 3},
        {"gap_col": -1},
        {"gap_col": 3},
        {"marker_corner": -1},
        {"marker_corner": 4},
        {"block_color": 0},
        {"block_color": 2},
        {"block_color": 10},
        {"gap_row": True},
        {"gap_col": 1.0},
        {"marker_corner": "1"},
        {"block_color": False},
    ],
)
def test_invalid_or_unknown_overrides_fail_closed(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_invalid_difficulty_fails_closed():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty="impossible")


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", None])
def test_seed_requires_a_plain_integer(seed):
    with pytest.raises((TypeError, ValueError), match="seed"):
        gen.generate(seed, 0)
    with pytest.raises((TypeError, ValueError), match="seed"):
        gen.schedule_profile(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, 1.75, "1", None])
def test_sample_index_requires_a_nonnegative_plain_integer(sample_index):
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.generate(991, sample_index)
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.schedule_profile(991, sample_index)


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 3 for _ in range(3)],
        [[0, 0, 0], [0, 2, 3], [0, 3]],
        [[0, 0, 0], [0, 2, 3], [0, 3, 10]],
        [[0, 0, 0], [0, 2, 3], [0, 4, 3]],
        [[0, 0, 0], [0, 2, 2], [0, 3, 3]],
        [[0, 0, 0], [0, 3, 3], [0, 3, 3]],
        [[0, 0, 0], [0, 2, 3], [0, 0, 3]],
        [[2, 3, 3], [3, 3, 3], [3, 3, 3]],
    ],
)
def test_validator_rejects_malformed_or_semantically_invalid_grids(grid):
    assert gen.self_check(grid)


def test_validator_and_mirror_do_not_mutate_input():
    grid = gen.generate(44, 7, gap_row=1, gap_col=2, marker_corner=3, block_color=8)
    original = deepcopy(grid)
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == rule_output(grid)
    assert grid == original


def test_declared_canonical_shortcut_fits_all_canonical_pairs_but_generated_witness_refutes_it():
    assert set(gen.CANONICAL_SHORTCUTS) == {"gap_parity"}
    expected_rivals = {
        "gap_parity",
        "inverse_gap_parity",
        "always_main",
        "always_anti",
    }
    assert set(gen.SEMANTIC_RIVALS) == expected_rivals
    assert set(gen.LESSON_COMPETITORS) == expected_rivals
    assert all(
        gap_parity_output(pair["input"]) == pair["output"]
        for pair in canonical_pairs()
    )

    witness = counterexample_input()
    assert observed(witness) == {
        "gap_row": 0,
        "gap_col": 0,
        "marker_corner": 1,
        "block_color": 3,
    }
    assert gen.self_check(witness) == []
    assert rule_output(witness) != gap_parity_output(witness)
    assert rule_output(witness) != always_main_output(witness)
    assert gen.SEMANTIC_WITNESSES["anti_marker_same_gaps"](witness)
    assert gen.SEMANTIC_RIVALS["gap_parity"](witness) == gap_parity_output(witness)

    reverse_witness = [[0, 0, 0], [0, 2, 3], [0, 3, 3]]
    assert rule_output(reverse_witness) != inverse_gap_parity_output(reverse_witness)
    assert rule_output(reverse_witness) != always_anti_output(reverse_witness)


def test_default_schedule_makes_every_rotated_four_pair_lesson_identifiable():
    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(24):
            grids = [
                gen.generate(800_000 + start, start + offset, difficulty=difficulty)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            assert {gen.schedule_profile(0, start + offset, difficulty) for offset in range(4)} == set(gen.SCHEDULE_PROFILES)
            for query_index in range(len(grids)):
                demos = [
                    {"input": deepcopy(grid), "output": rule_output(grid)}
                    for index, grid in enumerate(grids)
                    if index != query_index
                ]
                query = {"input": deepcopy(grids[query_index])}
                assert gen.lesson_identifiable(demos, query) == []
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_each_band_is_lawful_broad_and_behaviorally_live():
    signatures = {}
    for difficulty in (None, "easy", "medium", "hard"):
        values = {key: set() for key in EXPECTED_AXES}
        grids = []
        for index in range(320):
            grid = gen.generate(920_000 + index, index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.rule_mirror(grid) == rule_output(grid)
            grids.append(grid)
            for key, value in observed(grid).items():
                values[key].add(value)
        assert values["gap_row"] == {0, 1, 2}
        assert values["gap_col"] == {0, 1, 2}
        assert values["marker_corner"] == {0, 1, 2, 3}
        assert values["block_color"] == set(COLORS)
        signatures[difficulty] = json.dumps(grids, separators=(",", ":"))
    assert len(set(signatures.values())) == len(signatures)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261004)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_keyed_generation_is_python_hashseed_independent():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]


def test_real_racket_reference_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids.extend(gen.generate(5100 + index, index) for index in range(24))
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]


def test_production_duplicate_filter_cannot_remove_the_only_anti_diagonal_witness():
    """Regression for failed census lesson medium/index 41.

    The production sampler rejects duplicate inputs before assembling a lesson.
    Four scheduled draws therefore must be pairwise distinct and contain two
    main- and two anti-diagonal marker codes, so any one query rotation leaves
    both orientations in the three demonstrations.
    """
    seed = 3163466928
    start = 41
    grids = [gen.generate(seed, start + offset, difficulty="medium") for offset in range(4)]
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in grids]
    assert len(set(serialized)) == 4

    orientations = [observed(grid)["marker_corner"] in (0, 3) for grid in grids]
    assert orientations.count(True) == orientations.count(False) == 2
    for query_index in range(4):
        demos = [
            {"input": deepcopy(grid), "output": rule_output(grid)}
            for index, grid in enumerate(grids)
            if index != query_index
        ]
        query = {"input": deepcopy(grids[query_index])}
        assert gen.lesson_identifiable(demos, query) == []
        assert all(
            any(rival(demo["input"]) != demo["output"] for demo in demos)
            for rival in gen.LESSON_COMPETITORS.values()
        )


def test_default_sampler_covers_both_gap_relations_for_every_marker_corner():
    """Do not replace one gap shortcut with a corner-to-gap correlation."""
    expected = {(corner, same) for corner in range(4) for same in (False, True)}
    for difficulty in (None, "easy", "medium", "hard"):
        observed_pairs = set()
        for seed in range(24):
            for sample_index in range(4):
                info = observed(gen.generate(seed, sample_index, difficulty=difficulty))
                observed_pairs.add(
                    (info["marker_corner"], info["gap_row"] == info["gap_col"])
                )
        assert observed_pairs == expected
