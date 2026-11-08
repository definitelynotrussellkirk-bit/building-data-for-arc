"""Task-local regression suite for 5bb29951ab1a."""
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
    corner_or_dense_output,
    intended_output,
    load_generator,
    observed,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs())
def test_canonical_pairs_are_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


def test_generated_lessons_cover_both_rule_branches_and_shortcut_witness():
    for band in (None, "easy", "medium", "hard"):
        for index in range(24):
            grid = gen.generate(1901, index, difficulty=band)
            stats = observed(grid)
            assert gen.self_check(grid) == []
            assert stats["n_absorb"] >= 2
            assert stats["one_neighbor_rejects"] >= 1
            assert stats["isolated_rejects"] >= 1
            assert stats["opposite_two_witnesses"] >= 1
            assert intended_output(grid) != grid
            assert corner_or_dense_output(grid) != intended_output(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_visible_in_returned_pixels(band):
    requested = {
        "grid_h": 12,
        "grid_w": 14,
        "n_absorb": 8,
        "n_reject": 8,
        "palette_id": 7,
    }
    grid = gen.generate(77, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    stats = observed(grid)
    assert {key: stats[key] for key in ("grid_h", "grid_w", "n_absorb", "n_reject")} == {
        key: requested[key] for key in ("grid_h", "grid_w", "n_absorb", "n_reject")
    }


@pytest.mark.parametrize(
    "key,value",
    [
        ("unknown_axis", 1),
        ("grid_h", 11),
        ("grid_h", 18),
        ("grid_w", 13),
        ("grid_w", 20),
        ("n_absorb", 1),
        ("n_absorb", 9),
        ("n_reject", 1),
        ("n_reject", 9),
        ("palette_id", -1),
        ("palette_id", 8),
        ("n_absorb", True),
        ("n_reject", 2.5),
        ("palette_id", "2"),
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_canonical_fitting_rival_is_refuted_by_generated_bridge_witness():
    pairs = canonical_pairs()
    assert all(corner_or_dense_output(pair["input"]) == pair["output"] for pair in pairs)
    grid = gen.generate(811, 4, n_absorb=2, n_reject=2)
    assert gen.SEMANTIC_WITNESSES["opposite_two_neighbors"](grid)
    assert gen.SEMANTIC_RIVALS["corner_or_dense_only"](grid) == corner_or_dense_output(grid)
    assert gen.SEMANTIC_RIVALS["corner_or_dense_only"](grid) != intended_output(grid)


def test_generator_is_deterministic_and_does_not_touch_global_random_state():
    random.seed(314159)
    before = random.getstate()
    first = gen.generate(42, 17, difficulty="hard")
    after = random.getstate()
    second = gen.generate(42, 17, difficulty="hard")
    assert first == second
    assert before == after
    assert first == deepcopy(first)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 14 for _ in range(12)]],
)
def test_malformed_inputs_return_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)


def test_real_racket_authority_matches_independent_oracle_on_shortcut_witnesses():
    from arc_repl.racket_bridge import racket_runtime_status
    from reference_probe import racket_outputs, shortcut_witness

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()] + [shortcut_witness()]
    grids += [gen.generate(319, index, difficulty=band) for band in ("easy", "medium", "hard") for index in range(8)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]


def test_invalid_difficulty_is_rejected_before_generation():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="__invalid_difficulty__")


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_non_integer_seed_is_rejected_before_generation(bad_seed):
    with pytest.raises(ValueError, match="seed"):
        gen.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", -1])
def test_invalid_sample_index_is_rejected_before_generation(bad_index):
    with pytest.raises(ValueError, match="sample_index"):
        gen.generate(991, bad_index)
