"""Source-bound regressions for the onion-depth crop generator."""
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
    RULE_HASH,
    canonical_pairs,
    color_separate_output,
    has_multicolor_component,
    load_generator,
    max_component_size,
    observed,
    onion_output,
    profile,
    racket_outputs,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL = canonical_pairs()


def test_rule_pin_and_all_canonical_pairs_are_exact():
    assert gen.RULE_HASH == RULE_HASH
    assert len(CANONICAL) == 3
    for pair in CANONICAL:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert onion_output(pair["input"]) == pair["output"]
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("dims", [(9, 9), (11, 11), (18, 20)])
def test_exact_size_overrides_are_lawful_and_observable_in_every_band(difficulty, dims):
    requested = {"grid_h": dims[0], "grid_w": dims[1]}
    grid = gen.generate(1901, 7, difficulty=difficulty, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested
    assert gen.rule_mirror(grid) == onion_output(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 8},
        {"grid_h": 19},
        {"grid_w": 8},
        {"grid_w": 21},
        {"grid_h": True},
        {"grid_w": 11.0},
    ],
)
def test_invalid_and_unknown_overrides_are_rejected_loudly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **overrides)


def test_invalid_difficulty_is_rejected_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 2, difficulty="impossible")


def test_self_check_rejects_blank_full_and_malformed_impostors():
    bad = [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[0] * 9 for _ in range(9)],
        [[3] * 9 for _ in range(9)],
        [[True] * 9 for _ in range(9)],
        [[10] * 9 for _ in range(9)],
    ]
    for grid in bad:
        errors = gen.self_check(grid)
        assert isinstance(errors, list) and errors, grid


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_schedule_covers_canonical_profiles_depth_and_teaching_witnesses(difficulty):
    grids = [gen.generate(8100, index, difficulty=difficulty) for index in range(30)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert {(9, 9, 2), (11, 11, 2)} <= {profile(grid) for grid in grids}
    assert max(max_component_size(grid) for grid in grids) >= 33
    witnesses = [grid for grid in grids if has_multicolor_component(grid)]
    assert len(witnesses) >= 20
    assert all(color_separate_output(grid) != onion_output(grid) for grid in witnesses)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(6))
def test_every_query_rotation_refutes_each_declared_competitor(difficulty, start):
    grids = [gen.generate(9200, start + offset, difficulty=difficulty) for offset in range(4)]
    pairs = [{"input": grid, "output": onion_output(grid)} for grid in grids]
    for query_index in range(len(pairs)):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        query = pairs[query_index]
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), (
                name,
                difficulty,
                start,
                query_index,
            )
        assert gen.lesson_identifiable(demos, query) == []


def test_declared_color_separation_shortcut_fits_canonical_and_witnesses_disagree():
    assert set(gen.CANONICAL_SHORTCUTS) == {"peel_each_color_separately"}
    assert set(gen.LESSON_COMPETITORS) == set(gen.CANONICAL_SHORTCUTS)
    assert set(gen.SEMANTIC_RIVALS) == set(gen.CANONICAL_SHORTCUTS)
    assert all(color_separate_output(pair["input"]) == pair["output"] for pair in CANONICAL)
    witnesses = [gen.generate(12000, index) for index in range(12) if index % 3 != 1]
    assert witnesses
    for grid in witnesses:
        assert gen.SEMANTIC_WITNESSES["multicolor_connected_shape"](grid)
        assert gen.SEMANTIC_RIVALS["peel_each_color_separately"](grid) == color_separate_output(grid)
        assert color_separate_output(grid) != onion_output(grid)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261004)
    state = random.getstate()
    first = gen.generate(123, 17, difficulty="hard")
    second = gen.generate(123, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second and first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 8
    assert first != second


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


def test_real_racket_authority_matches_independent_mirror_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in CANONICAL]
    grids += [gen.generate(3100 + index, index) for index in range(24)]
    assert racket_outputs(grids) == [onion_output(grid) for grid in grids]
