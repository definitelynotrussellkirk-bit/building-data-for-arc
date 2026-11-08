"""Focused regression and semantic-contract tests for 0c4c1974cbf2."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

from puzzle_generators import base
from reviewer_support import canonical_pairs, find_root

TASK_ID = "0c4c1974cbf2"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_pin_and_public_contract_are_bounded_and_honest():
    assert GEN.RULE_HASH == "ceb28731a942"
    assert GEN.EXAMPLES_NEEDED == 3
    assert len(GEN.SCHEDULE_PROFILES) == 5
    assert not hasattr(GEN, "LESSON_SCHEDULE_PERIOD")
    assert set(GEN.AXES) == {
        "grid_h",
        "half_w",
        "left_cells",
        "overlap_count",
        "palette_size",
    }
    assert GEN.HELPFUL_TEXTURES == ()
    assert set(GEN.DEGENERATE_TEXTURES) == {"no_bar", "no_overlap", "all_overlap"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_all_canonical_pairs_are_accepted_strict_and_exact():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_generation_is_deterministic_fresh_and_global_rng_isolated():
    random.seed(20261012)
    state = random.getstate()
    first = GEN.generate(17, 3, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(17, 3, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert GEN.generate(17, 3, difficulty="hard") == second


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", [5, 14])
@pytest.mark.parametrize("half_w", [2, 7])
@pytest.mark.parametrize("left_cells", [5, 8])
@pytest.mark.parametrize("overlap_count", [2, 4])
@pytest.mark.parametrize("palette_size", [2, 4])
def test_every_boundary_override_cross_product_is_constructive_and_observable(
    band, grid_h, half_w, left_cells, overlap_count, palette_size
):
    requested = {
        "grid_h": grid_h,
        "half_w": half_w,
        "left_cells": left_cells,
        "overlap_count": overlap_count,
        "palette_size": palette_size,
    }
    grid = GEN.generate(701, 22, difficulty=band, **requested)
    assert GEN.self_check(grid, meta={"overrides": requested}) == []
    assert GEN.observe_overrides(grid) == requested
    assert GEN.rule_mirror(grid) != [[0] * len(grid[0]) for _ in grid]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_draws_record_exact_observable_axis_provenance(band):
    for index in range(15):
        seen = []
        base.set_ctx_observer(seen.append)
        try:
            grid = GEN.generate(900 + index, index, difficulty=band)
        finally:
            base.set_ctx_observer(None)
        assert GEN.self_check(grid) == []
        assert seen and seen[-1].recorded_draws() == GEN.observe_overrides(grid)


@pytest.mark.parametrize(
    "args,kwargs",
    [
        ((True, 0), {}),
        ((1.5, 0), {}),
        (("1", 0), {}),
        ((1, True), {}),
        ((1, 1.5), {}),
        ((1, "1"), {}),
        ((1, -1), {}),
        ((1, 0), {"difficulty": "impossible"}),
        ((1, 0), {"typo_axis": 3}),
        ((1, 0), {"grid_h": True}),
        ((1, 0), {"grid_h": 4}),
        ((1, 0), {"half_w": 8}),
        ((1, 0), {"left_cells": 4}),
        ((1, 0), {"overlap_count": 1}),
        ((1, 0), {"palette_size": 5}),
        ((1, 0), {"texture": "helpful"}),
        ((1, 0), {"texture": "no_bar", "grid_h": 7}),
    ],
)
def test_invalid_calls_and_retired_controls_fail_loudly(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **kwargs)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_two_schedule_slots_are_canonical_profile_anchors_in_every_band(band):
    first = GEN.generate(41, 0, difficulty=band)
    second = GEN.generate(41, 1, difficulty=band)
    assert GEN.strict_canonical_like(first) == []
    assert GEN.strict_canonical_like(second) == []
    assert (len(first), len(first[0]), len({v for row in first for v in row})) == (7, 11, 4)
    assert (len(second), len(second[0]), len({v for row in second for v in row})) == (7, 13, 4)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_cyclic_start_and_query_rotation_kills_all_declared_rivals(band):
    period = len(GEN.SCHEDULE_PROFILES)
    for start in range(period):
        materialized = [
            _pair(GEN.generate(300 + start, start + offset, difficulty=band))
            for offset in range(GEN.EXAMPLES_NEEDED + 1)
        ]
        for query_index in range(len(materialized)):
            demos = [pair for i, pair in enumerate(materialized) if i != query_index]
            query = materialized[query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), (band, start, query_index, name)


def test_declared_canonical_shortcuts_really_fit_every_canonical_pair():
    pairs = _canonical_pairs()
    assert GEN.CANONICAL_SHORTCUTS
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name


def test_every_witness_fires_and_refutes_each_named_rival():
    grids = [GEN.generate(81, index, difficulty="medium") for index in range(5)]
    for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
        firing = [grid for grid in grids if witness(grid)]
        assert firing, witness_name
        for rival_name in GEN.WITNESS_RIVALS[witness_name]:
            assert all(
                GEN.SEMANTIC_RIVALS[rival_name](grid) != GEN.rule_mirror(grid)
                for grid in firing
            ), (witness_name, rival_name)


def test_generic_profiles_contain_bidirectional_and_color_contrasts():
    for index in (2, 3, 4):
        grid = GEN.generate(123, index, difficulty="medium")
        facts = GEN._analysis(grid)
        assert facts["left_only"]
        assert facts["right_only"]
        assert facts["same_color_overlaps"]
        assert facts["mismatched_overlaps"]
        assert facts["row_decoy"]
        assert 2 not in facts["palette"]


def test_negative_textures_and_mutation_fixtures_are_rejected_without_mutation():
    for texture in GEN.DEGENERATE_TEXTURES:
        grid = GEN.generate(1, 0, texture=texture)
        before = copy.deepcopy(grid)
        assert GEN.self_check(grid), texture
        assert grid == before

    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 7
    for name, grid in fixtures:
        before = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == before


def test_retained_counterexample_refutes_the_canonical_same_color_shortcut():
    path = HOME / "counterexamples" / "same_color_shortcut.json"
    record = json.loads(path.read_text())
    grid = record["input"]
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == record["canonical_output"]
    assert GEN.CANONICAL_SHORTCUTS["same_color_only"](grid) == record["same_color_only_output"]
    assert record["canonical_output"] != record["same_color_only_output"]
    for name in record["additional_refuted_rivals"]:
        assert GEN.LESSON_COMPETITORS[name](grid) != record["canonical_output"]
