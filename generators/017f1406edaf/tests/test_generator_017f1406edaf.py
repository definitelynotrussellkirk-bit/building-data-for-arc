"""Focused regressions for the count-to-object generator repair."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "017f1406edaf"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    RIVALS,
    components,
    intended_output,
    load_generator,
    observed,
    rival_count_all_blue,
    rival_include_row0,
    rival_median_candidate,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def _pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def test_rule_authority_is_pinned_and_contract_axes_are_unambiguous():
    assert gen.RULE_HASH == "e05af36c455d"
    assert set(gen.AXES) == {"grid_h", "grid_w", "K", "n_blobs", "decoy"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_honored_in_every_band(band):
    options = {"grid_h": 9, "grid_w": 10, "K": 6, "n_blobs": 4, "decoy": "both"}
    grid = gen.generate(71, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"grid_h": 8},
        {"grid_w": 9},
        {"K": 1},
        {"K": True},
        {"n_blobs": 5},
        {"decoy": "unknown"},
        {"grid_h": 9.5},
    ],
)
def test_invalid_or_unknown_overrides_fail_explicitly(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize(
    "seed,index,decoy",
    [
        (1246, 12, "blue"),
        (1236, 2, "row0"),
        (1236, 2, "both"),
    ],
)
def test_requested_decoys_are_materialized_not_merely_attempted(seed, index, decoy):
    grid = gen.generate(seed, index, decoy=decoy)
    assert observed(grid)["decoy"] == decoy
    assert gen.self_check(grid) == []


@pytest.mark.parametrize("pair", _pairs())
def test_canonical_inputs_are_accepted_and_independent_mirror_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


def test_strong_demo_shortcut_is_real_and_canonical_test_refutes_it():
    pairs = _pairs()
    demonstrations = [pair for pair in pairs if pair["split"] == "train"]
    tests = [pair for pair in pairs if pair["split"] == "test"]
    assert demonstrations and tests
    assert all(rival_median_candidate(pair["input"]) == pair["output"] for pair in demonstrations)
    assert any(rival_median_candidate(pair["input"]) != pair["output"] for pair in tests)


def test_exclusion_shortcuts_fit_every_canonical_pair():
    for pair in _pairs():
        assert rival_count_all_blue(pair["input"]) == pair["output"]
        assert rival_include_row0(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_counterexample_profile_refutes_every_declared_rival(band):
    grid = gen.generate(991, 1, difficulty=band)
    assert gen.schedule_profile(991, 1, band) == "counterexample"
    assert observed(grid)["decoy"] == "both"
    expected = intended_output(grid)
    assert expected != [[0 for _ in row] for row in grid]
    assert set(gen.SEMANTIC_RIVALS) == set(RIVALS)
    for name, independent_rival in RIVALS.items():
        assert independent_rival(grid) != expected, name
        assert gen.SEMANTIC_RIVALS[name](grid) == independent_rival(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("target", range(2, 7))
def test_two_candidate_counterexamples_always_refute_lower_median_shortcut(band, target):
    # Regression for semantic-gate lessons where n_blobs=2 and the target was
    # the smaller object: the rival's lower-median convention then selected it.
    for seed in range(12):
        grid = gen.generate(2000 + seed, 1, difficulty=band, K=target, n_blobs=2)
        assert rival_median_candidate(grid) != intended_output(grid)


def test_four_demo_lessons_remain_identifiable_under_every_query_rotation():
    for start in range(8):
        pairs = []
        for offset in range(5):
            index = start + offset
            grid = gen.generate(7300 + index, index, difficulty="medium")
            pairs.append({"input": grid, "output": intended_output(grid)})
        for query_index in range(5):
            query = pairs[query_index]
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_schedule_is_deterministic_diverse_and_covers_both_profiles(band):
    profiles = set()
    shapes = set()
    targets = set()
    for index in range(64):
        grid = gen.generate(5000 + index, index, difficulty=band)
        assert grid == gen.generate(5000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        profiles.add(gen.schedule_profile(5000 + index, index, band))
        shapes.add((len(grid), len(grid[0])))
        target = next(value for row in intended_output(grid) for value in row if value)
        targets.add(target)
    assert profiles == {"canonical", "counterexample"}
    assert len(shapes) >= 6
    assert targets == {8}


def test_override_provenance_matches_observed_pixels():
    from puzzle_generators.base import set_ctx_observer

    captured = []
    try:
        set_ctx_observer(captured.append)
        grid = gen.generate(81, 7, difficulty="hard", K=5, decoy="row0")
    finally:
        set_ctx_observer(None)
    draws = captured[-1].recorded_draws()
    for name, actual in gen.observe_overrides(grid).items():
        assert draws[name] == actual


@pytest.mark.parametrize("mutation", ["bad_color", "remove_match", "duplicate_match"])
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(87, 1, decoy="none", K=4, n_blobs=3)
    changed = deepcopy(grid)
    if mutation == "bad_color":
        changed[-1][-1] = 10
    else:
        target = next(
            component
            for component in components(changed)
            if component.color != 1 and not component.touches_row0 and component.size == 4
        )
        if mutation == "remove_match":
            row, col = target.cells[-1]
            changed[row][col] = 0
        else:
            # Recolor one nonmatching component to isolate exactly four of its cells
            # is brittle; instead add a lawful-looking four-cell component in the
            # lower-right blank region and let validation catch the second match.
            placed = False
            for row in range(3, len(changed) - 1):
                for col in range(len(changed[0]) - 4):
                    cells = [(row, col + step) for step in range(4)]
                    moat = {
                        (r + dr, c + dc)
                        for r, c in cells
                        for dr, dc in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
                        if 0 <= r + dr < len(changed) and 0 <= c + dc < len(changed[0])
                    }
                    if all(changed[r][c] == 0 for r, c in moat):
                        for r, c in cells:
                            changed[r][c] = 9
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                pytest.skip("sample has no isolated four-cell slot for mutation")
    assert gen.self_check(changed)


def test_real_racket_authority_matches_independent_mirror_on_generated_witnesses():
    from arcpuzzles import Catalog

    grids = [pair["input"] for pair in _pairs()]
    grids += [gen.generate(2600 + index, index, difficulty="medium") for index in range(8)]
    receipt = Catalog(ROOT).apply(TASK_ID, grids, timeout=120)
    assert receipt["rule_hash_matches_catalog"]
    assert [item["output"] for item in receipt["results"]] == [
        intended_output(grid) for grid in grids
    ]
