"""Task-local regression suite for 17ea562973ac.

The oracle and observations live in ``workspace/reference_probe.py`` so these
tests do not merely repeat production helpers.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    at_least_three_output,
    canonical_pairs,
    facts,
    first_two_output,
    load_generator,
    observed,
    reference_output,
    retain_markers_output,
    semantic_profile,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_canonical_inputs_are_owned_and_oracle_matches_labels(pair):
    before = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert reference_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == before


def test_authority_pin_and_public_contract_are_truthful():
    assert gen.RULE_HASH == "22bfb52d3f48"
    assert gen.VERSION != "2.1.1"
    assert set(gen.AXES) == {"grid_h", "grid_w", "color", "num_cells"}
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()
    assert gen.EXAMPLES_NEEDED == 3
    assert tuple(gen.SCHEDULE_PROFILES) == (
        "two_diagonal_tl_br",
        "interior_three",
        "two_diagonal_tr_bl",
        "distributed_interior",
    )


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "axes",
    (
        {"grid_h": 6, "grid_w": 7, "color": 2, "num_cells": 2},
        {"grid_h": 12, "grid_w": 14, "color": 9, "num_cells": 8},
        {"grid_h": 9, "grid_w": 10, "color": 5, "num_cells": 4},
    ),
)
def test_every_public_override_is_exact_in_every_band(band, axes):
    grid = gen.generate(1701, 29, difficulty=band, **axes)
    assert gen.self_check(grid) == []
    assert observed(grid) == axes
    assert gen.observe_overrides(grid) == axes
    assert grid == gen.generate(1701, 29, difficulty=band, **axes)


@pytest.mark.parametrize(
    "overrides",
    (
        {"typo_axis": 1},
        {"grid_h": 5}, {"grid_h": 13},
        {"grid_w": 6}, {"grid_w": 15},
        {"color": 1}, {"color": 10},
        {"num_cells": 1}, {"num_cells": 9},
        {"grid_h": True}, {"grid_w": 8.0},
        {"color": "3"}, {"num_cells": False},
    ),
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("difficulty", ("trivial", 0.5, True))
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", BANDS)
def test_default_schedule_covers_exact_counts_and_semantic_counterexamples(band):
    counts = set()
    for index in range(80):
        grid = gen.generate(712, index, difficulty=band)
        info = facts(grid)
        assert gen.self_check(grid) == []
        assert 2 <= info["num_cells"] <= 8
        assert info["bbox"][2] - info["bbox"][0] >= 3
        assert info["bbox"][3] - info["bbox"][1] >= 3
        counts.add(info["num_cells"])
    assert counts == set(range(2, 9))

    for start in range(20):
        grids = [gen.generate(991, start + offset, difficulty=band) for offset in range(4)]
        profiles = [semantic_profile(grid) for grid in grids]
        assert sum(profile["two_markers"] for profile in profiles) == 2
        assert sum(profile["interior_marker"] for profile in profiles) >= 2
        assert sum(profile["first_two_incomplete"] for profile in profiles) >= 2


@pytest.mark.parametrize("start", range(8))
def test_three_demo_rotations_refute_all_declared_competitors(start):
    grids = [gen.generate(2026, start + offset, difficulty="hard") for offset in range(4)]
    pairs = [{"input": grid, "output": reference_output(grid)} for grid in grids]
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        query = {"input": pairs[query_index]["input"], "output": [[9]]}
        assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    "name,oracle",
    (
        ("requires_three_markers", at_least_three_output),
        ("retain_original_markers", retain_markers_output),
        ("first_two_markers_only", first_two_output),
    ),
)
def test_declared_rivals_match_independent_oracles(name, oracle):
    for index in range(16):
        grid = gen.generate(313, index)
        assert gen.SEMANTIC_RIVALS[name](grid) == oracle(grid)


def test_canonical_count_shortcut_really_fits_all_canonical_labels():
    shortcut = gen.CANONICAL_SHORTCUTS["requires_three_markers"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical_pairs())
    witness = gen.generate(4, 0, num_cells=2)
    assert shortcut(witness) != reference_output(witness)


def test_each_semantic_witness_is_a_real_rival_disagreement():
    hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for index in range(40):
        grid = gen.generate(911, index)
        truth = reference_output(grid)
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            if predicate(grid):
                hits[name] += 1
                assert any(
                    gen.SEMANTIC_RIVALS[rival](grid) != truth
                    for rival in gen.WITNESS_RIVALS[name]
                )
    assert all(hits.values()), hits


def test_self_check_rejects_minimal_impostors():
    valid = gen.generate(7, 1, grid_h=8, grid_w=9, color=5, num_cells=3)
    impostors = []
    impostors.append([[0] * 9 for _ in range(8)])
    one = [[0] * 9 for _ in range(8)]; one[1][1] = 5; impostors.append(one)
    aligned = [[0] * 9 for _ in range(8)]; aligned[2][1] = aligned[2][7] = 5; impostors.append(aligned)
    multi = deepcopy(valid); multi[1][1] = 7; impostors.append(multi)
    full = [[5] * 9 for _ in range(8)]; impostors.append(full)
    too_many = [[0] * 9 for _ in range(8)]
    for r, c in ((1,1),(1,2),(1,3),(2,1),(2,2),(2,3),(5,6),(5,7),(6,7)):
        too_many[r][c] = 5
    impostors.append(too_many)
    bad_color = deepcopy(valid)
    bad_color = [[1 if value else 0 for value in row] for row in bad_color]
    impostors.append(bad_color)
    assert all(gen.self_check(grid) for grid in impostors)


@pytest.mark.parametrize("grid", (None, [], [[]], [[0], [0, 1]], [[True] * 7 for _ in range(6)]))
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_rule_mirror_and_diagnostics_are_input_pure():
    grid = gen.generate(77, 3)
    before = deepcopy(grid)
    assert gen.rule_mirror(grid) == reference_output(grid)
    gen.observe_overrides(grid)
    gen.strict_canonical_like(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == before
