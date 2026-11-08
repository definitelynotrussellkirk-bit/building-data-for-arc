"""Source-bound regression tests for the crossed-strand weave generator."""
from __future__ import annotations

from copy import deepcopy
import itertools
import json
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    RULE_HASH,
    authority_files,
    canonical_pairs,
    canonical_program,
    crossing_to_farthest_output,
    load_generator,
    normalized_rule_hash,
    observed,
    racket_outputs,
    rule_output,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_canonical_pairs_and_selected_authorities_are_exact():
    assert gen.RULE_HASH == RULE_HASH
    assert normalized_rule_hash(canonical_program()) == RULE_HASH
    pairs = canonical_pairs()
    assert len(pairs) == 6
    for pair in pairs:
        assert gen.self_check(deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(deepcopy(pair["input"])) == []
        assert rule_output(pair["input"]) == pair["output"]
        assert gen.rule_mirror(deepcopy(pair["input"])) == pair["output"]

    selected = canonical_program()
    for path in authority_files():
        target = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code"] == selected, path
        assert target["raw_code"] == selected, path


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_exact_override_cartesian_is_observable_and_lawful_in_every_band(difficulty):
    cases = itertools.product(
        (10, 25),
        (10, 15),
        ("horizontal", "vertical"),
        ("outside", "straddle"),
        ("full", "partial"),
    )
    for index, (h, w, primary, relation, extent) in enumerate(cases):
        requested = {
            "grid_h": h,
            "grid_w": w,
            "primary": primary,
            "vertical_relation": relation,
            "strand_extent": extent,
        }
        grid = gen.generate(91000 + index, index, difficulty=difficulty, **requested)
        assert gen.self_check(grid) == [], requested
        assert observed(grid) == requested
        assert gen.observe_overrides(grid) == requested
        assert gen.rule_mirror(grid) == rule_output(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 9},
        {"grid_h": 26},
        {"grid_w": 9},
        {"grid_w": 16},
        {"primary": "diagonal"},
        {"vertical_relation": "touching"},
        {"strand_extent": "mixed"},
        {"grid_h": True},
        {"grid_w": 12.0},
        {"primary": 1},
        {"vertical_relation": False},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_invalid_difficulty_is_rejected_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty="impossible")


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_schedule_covers_profiles_and_refutes_declared_shortcut(difficulty):
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.CANONICAL_SHORTCUTS) == {"crossing_to_farthest"}
    assert set(gen.LESSON_COMPETITORS) == set(gen.CANONICAL_SHORTCUTS)
    assert set(gen.SEMANTIC_RIVALS) == set(gen.CANONICAL_SHORTCUTS)

    canonical_shapes = {(10, 10), (12, 12), (15, 15), (25, 15)}
    for start in range(30):
        grids = [
            gen.generate(7000 + start, start + offset, difficulty=difficulty)
            for offset in range(4)
        ]
        for grid in grids:
            assert gen.self_check(grid) == []
            assert gen.rule_mirror(grid) == rule_output(grid)
        demo_obs = [observed(grid) for grid in grids[:3]]
        assert {row["primary"] for row in demo_obs} == {"horizontal", "vertical"}
        assert {row["vertical_relation"] for row in demo_obs} == {"outside", "straddle"}
        assert {row["strand_extent"] for row in demo_obs} == {"full", "partial"}
        assert any(
            rule_output(grid) != crossing_to_farthest_output(grid)
            for grid in grids[:3]
        )
        demos = [{"input": grid, "output": rule_output(grid)} for grid in grids[:3]]
        query = {"input": grids[3], "output": rule_output(grids[3])}
        assert gen.lesson_identifiable(demos, query) == []

    shapes = {
        (len(gen.generate(9900, index, difficulty=difficulty)),
         len(gen.generate(9900, index, difficulty=difficulty)[0]))
        for index in range(20)
    }
    assert canonical_shapes <= shapes


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_four_pair_windows_refute_declared_shortcut_under_every_query_rotation(difficulty):
    for start in range(6):
        grids = [
            gen.generate(17000 + start, start + offset, difficulty=difficulty)
            for offset in range(4)
        ]
        pairs = [
            {"input": grid, "output": rule_output(grid)}
            for grid in grids
        ]
        for query_index in range(4):
            demos = [
                pair for index, pair in enumerate(pairs) if index != query_index
            ]
            assert gen.lesson_identifiable(demos, pairs[query_index]) == [], (
                difficulty,
                start,
                query_index,
            )


def test_declared_shortcut_fits_every_canonical_pair_but_witnesses_disagree():
    assert all(
        crossing_to_farthest_output(pair["input"]) == pair["output"]
        for pair in canonical_pairs()
    )
    witnesses = [
        gen.generate(12000 + index, index, vertical_relation="straddle")
        for index in range(12)
    ]
    assert all(gen.SEMANTIC_WITNESSES["vertical_straddle"](grid) for grid in witnesses)
    assert all(
        gen.SEMANTIC_RIVALS["crossing_to_farthest"](grid)
        == crossing_to_farthest_output(grid)
        for grid in witnesses
    )
    assert all(
        gen.SEMANTIC_RIVALS["crossing_to_farthest"](grid) != rule_output(grid)
        for grid in witnesses
    )


def test_validator_rejects_structural_corruption_without_mutating_input():
    grid = gen.generate(
        440,
        8,
        grid_h=15,
        grid_w=15,
        primary="vertical",
        vertical_relation="straddle",
        strand_extent="partial",
    )
    original = deepcopy(grid)
    assert gen.self_check(grid) == []
    assert grid == original

    mutations = {}
    mutations["blank"] = [[0 for _ in row] for row in grid]
    mutations["ragged"] = deepcopy(grid)
    mutations["ragged"][-1].pop()
    mutations["bad_color"] = deepcopy(grid)
    mutations["bad_color"][0][0] = 10
    mutations["off_strand"] = deepcopy(grid)
    row_counts = [sum(value > 0 for value in row) for row in grid]
    col_counts = [sum(grid[r][c] > 0 for r in range(len(grid))) for c in range(len(grid[0]))]
    row, col = row_counts.index(max(row_counts)), col_counts.index(max(col_counts))
    rr = next(r for r in range(len(grid)) if r != row)
    cc = next(c for c in range(len(grid[0])) if c != col)
    mutations["off_strand"][rr][cc] = next(value for value in range(1, 10) if value in {v for line in grid for v in line})
    mutations["gap"] = deepcopy(grid)
    occupied = [c for c, value in enumerate(grid[row]) if value > 0 and c != col]
    middle = occupied[len(occupied) // 2]
    mutations["gap"][row][middle] = 0

    for name, changed in mutations.items():
        assert gen.self_check(changed), name


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(10)]],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_replay_is_deterministic_and_global_rng_pure():
    random.seed(20261003)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_real_racket_reference_matches_independent_mirror_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [
        gen.generate(1900 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        for index in range(36)
    ]
    assert racket_outputs(grids) == [rule_output(grid) for grid in grids]


def test_default_path_records_every_exact_axis_through_genctx():
    from puzzle_generators.base import set_ctx_observer

    captured = []
    set_ctx_observer(captured.append)
    try:
        grid = gen.generate(77, 4, difficulty="hard")
    finally:
        set_ctx_observer(None)
    assert captured
    draws = captured[-1].recorded_draws()
    assert set(gen.AXES) <= set(draws)
    assert {name: draws[name] for name in gen.AXES} == gen.observe_overrides(grid)


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
def test_invalid_seed_scalars_are_rejected_at_public_boundary(seed):
    with pytest.raises(TypeError, match="seed"):
        gen.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", -1])
def test_invalid_sample_index_scalars_are_rejected_at_public_boundary(sample_index):
    expected = ValueError if sample_index == -1 and type(sample_index) is int else TypeError
    with pytest.raises(expected, match="sample_index"):
        gen.generate(991, sample_index)
