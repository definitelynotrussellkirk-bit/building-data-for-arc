"""Task-local regression tests for af373b71d67d.

The geometry oracle lives in workspace/ and does not import production helpers.
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
    canonical_pairs,
    centered_output,
    counterclockwise_output,
    intended_output,
    keep_source_output,
    load_generator,
    preserve_frame_output,
    profile_floor_schedule,
    racket_outputs,
    scene,
    unrotated_output,
    witness_flags,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {
    (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
    for pair in canonical_pairs()
}


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == "7364b3464a5f"


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_canonical_inputs_are_owned_and_python_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


def test_canonical_examples_leave_centering_shortcut_unfalsified():
    assert all(centered_output(pair["input"]) == pair["output"] for pair in canonical_pairs())


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("dims", [(8, 10), (9, 12), (10, 12), (16, 18)])
def test_every_advertised_dimension_pair_is_exact_in_every_band(band, dims):
    grid = gen.generate(17, 9, difficulty=band, grid_h=dims[0], grid_w=dims[1])
    assert (len(grid), len(grid[0])) == dims
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"grid_h": dims[0], "grid_w": dims[1]}


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"grid_h": 7},
        {"grid_h": 17},
        {"grid_w": 9},
        {"grid_w": 19},
        {"grid_h": True},
        {"grid_w": 12.0},
        {"grid_h": "9"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_pinned_profile_floor_has_exact_canonical_support_in_each_band(band):
    exact = 0
    for seed, sample_index, profiles in profile_floor_schedule(band):
        grid = gen.generate(seed, sample_index, difficulty=band)
        profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        exact += profile in profiles
    assert exact >= 1


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_distribution_is_deterministic_lawful_and_teaches_both_schedule_branches(band):
    colors = set()
    shapes = set()
    flags = {name: 0 for name in ("clockwise_direction", "erase_source", "top_left_anchor", "frame_overwrite")}
    distinct = set()
    for index in range(80):
        seed = 4400 + index
        grid = gen.generate(seed, index, difficulty=band)
        assert grid == gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        facts = scene(grid)
        colors.add(facts["frame_color"])
        shapes.add((len(grid), len(grid[0])))
        distinct.add(tuple(tuple(row) for row in grid))
        for name, hit in witness_flags(grid).items():
            flags[name] += int(hit)
    assert len(colors) >= 5
    assert {6, 7, 8} <= colors
    assert len(shapes) >= 12
    assert len(distinct) >= 75
    assert flags["clockwise_direction"] == 80
    assert flags["erase_source"] == 80
    assert flags["top_left_anchor"] >= 40
    assert flags["frame_overwrite"] >= 24


def test_semantic_contract_names_real_counterexamples_and_shortcut():
    expected_rivals = {
        "unrotated",
        "counterclockwise",
        "keep_source",
        "centered_when_fits",
        "preserve_frame",
    }
    assert set(gen.SEMANTIC_RIVALS) == expected_rivals
    assert set(gen.LESSON_COMPETITORS) == expected_rivals
    assert set(gen.CANONICAL_SHORTCUTS) == {"centered_when_fits"}
    expected_witnesses = {
        "clockwise_direction",
        "erase_source",
        "top_left_anchor",
        "frame_overwrite",
    }
    assert set(gen.SEMANTIC_WITNESSES) == expected_witnesses
    for index in range(10):
        grid = gen.generate(712, index, difficulty="hard")
        assert gen.strict_canonical_like(grid) == []
        expected = intended_output(grid)
        assert gen.SEMANTIC_RIVALS["unrotated"](grid) == unrotated_output(grid)
        assert gen.SEMANTIC_RIVALS["counterclockwise"](grid) == counterclockwise_output(grid)
        assert gen.SEMANTIC_RIVALS["keep_source"](grid) == keep_source_output(grid)
        assert gen.SEMANTIC_RIVALS["centered_when_fits"](grid) == centered_output(grid)
        assert gen.SEMANTIC_RIVALS["preserve_frame"](grid) == preserve_frame_output(grid)
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            assert predicate(grid) == witness_flags(grid)[name]
        assert expected != gen.SEMANTIC_RIVALS["unrotated"](grid)
        assert expected != gen.SEMANTIC_RIVALS["counterclockwise"](grid)
        assert expected != gen.SEMANTIC_RIVALS["keep_source"](grid)


@pytest.mark.parametrize("start", range(25))
def test_every_four_pair_lesson_has_redundant_anchor_and_overwrite_evidence(start):
    profiles = [gen.schedule_profile(123, start + offset, difficulty="medium") for offset in range(4)]
    assert profiles.count("frame_overwrite") >= 2
    assert profiles.count("roomy_anchor") >= 2


@pytest.mark.parametrize("start", range(25))
def test_every_five_pair_window_has_redundant_anchor_and_overwrite_evidence(start):
    profiles = [gen.schedule_profile(123, start + offset, difficulty="medium") for offset in range(5)]
    assert profiles.count("frame_overwrite") >= 2
    assert profiles.count("roomy_anchor") >= 2
    assert set(gen.SCHEDULE_PROFILES) == {"frame_overwrite", "roomy_anchor"}


@pytest.mark.parametrize(
    "mutation",
    ["unknown_color", "second_motif", "break_frame", "fill_interior", "erase_motif"],
)
def test_self_check_rejects_destructive_mutations(mutation):
    grid = gen.generate(991, 3, grid_h=12, grid_w=15)
    facts = scene(grid)
    if mutation == "unknown_color":
        grid[0][0] = 9 if facts["frame_color"] != 9 else 8
    elif mutation == "second_motif":
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 0 and all(abs(r - rr) + abs(c - cc) > 1 for rr, cc in facts["motif"]):
                    grid[r][c] = 3
                    break
            else:
                continue
            break
    elif mutation == "break_frame":
        r, c = facts["frame_cells"][0]
        grid[r][c] = 0
    elif mutation == "fill_interior":
        r0, c0, _, _ = facts["frame_bbox"]
        grid[r0 + 1][c0 + 1] = facts["frame_color"]
    elif mutation == "erase_motif":
        for r, c in facts["motif"]:
            grid[r][c] = 0
    assert gen.self_check(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(8)]])
def test_malformed_grid_returns_diagnostics_not_exceptions(bad):
    assert gen.self_check(bad)


def test_real_racket_reference_matches_independent_oracle():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(319, index, difficulty=band) for band in ("easy", "medium", "hard") for index in range(10)]
    original = deepcopy(grids)
    outputs = racket_outputs(grids)
    assert grids == original
    assert outputs == [intended_output(grid) for grid in grids]
