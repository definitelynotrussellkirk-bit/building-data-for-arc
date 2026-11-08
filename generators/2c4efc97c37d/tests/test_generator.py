"""Focused regression suite for the 2c4efc97c37d generator repair."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
import onion_probe as probe  # noqa: E402
from onion_probe import (  # noqa: E402
    bbox_shortcut_output,
    canonical_pairs,
    exact_counterexample,
    intended_output,
    load_generator,
    observed,
    profile,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
CANONICAL_PROFILES = {(9, 25, 4), (11, 25, 4), (11, 27, 4)}


def _pair(grid):
    return {"input": deepcopy(grid), "output": intended_output(grid)}


def test_authority_pin_canonical_acceptance_and_shortcut_fit():
    assert gen.RULE_HASH == "dcdf1daba7ab"
    pairs = canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert intended_output(pair["input"]) == pair["output"]
        assert bbox_shortcut_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_in_every_band(band):
    requested = {
        "grid_h": 9,
        "grid_w": 25,
        "object_count": 4,
        "max_depth": 4,
        "irregular_count": 3,
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested
    assert intended_output(grid) != bbox_shortcut_output(grid)


@pytest.mark.parametrize(
    "override",
    [
        {"typo_axis": 1},
        {"grid_h": 8},
        {"grid_h": 19},
        {"grid_w": 24},
        {"grid_w": 31},
        {"object_count": 2},
        {"object_count": 5},
        {"max_depth": 1},
        {"max_depth": 5},
        {"irregular_count": 0},
        {"irregular_count": 4},
        {"grid_h": True},
        {"max_depth": 3.0},
        {"object_count": "3"},
    ],
)
def test_invalid_and_unknown_overrides_fail_loudly(override):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **override)


def test_exact_counterexample_refutes_the_strongest_canonical_shortcut():
    grid = exact_counterexample()
    assert gen.self_check(grid) == []
    assert intended_output(grid) == [[1, 2, 3]]
    assert bbox_shortcut_output(grid) == [[2, 2, 3]]
    assert gen.CANONICAL_SHORTCUTS["bbox_rectangle_depth"](grid) == [[2, 2, 3]]
    assert gen.SEMANTIC_WITNESSES["bbox_depth_disagreement"](grid)


def test_binary_mask_counterexample_refutes_palette_and_nonzero_shortcuts():
    grid = probe.binary_mask_counterexample()
    assert intended_output(grid) == [[1, 2, 3]]
    assert bbox_shortcut_output(grid) == [[2, 2, 3]]
    assert probe.color_partition_output(grid) != intended_output(grid)
    assert probe.nonzero_output(grid) != intended_output(grid)
    assert grid[0][-1] == 9


def test_binary_mask_shortcuts_are_registered_with_executable_witnesses():
    expected = {
        "bbox_rectangle_depth",
        "color_partition_depth",
        "nonzero_foreground_depth",
    }
    assert set(gen.SEMANTIC_RIVALS) == expected
    assert set(gen.CANONICAL_SHORTCUTS) == expected
    assert set(gen.LESSON_COMPETITORS) == expected
    grid = probe.binary_mask_counterexample()
    assert gen.SEMANTIC_RIVALS["color_partition_depth"](grid) == probe.color_partition_output(grid)
    assert gen.SEMANTIC_RIVALS["nonzero_foreground_depth"](grid) == probe.nonzero_output(grid)
    assert all(predicate(grid) for predicate in gen.SEMANTIC_WITNESSES.values())


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_hits_canonical_profiles_and_refutes_bbox_rival(band):
    grids = [gen.generate(9000, index, difficulty=band) for index in range(20)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert any(profile(grid) in CANONICAL_PROFILES for grid in grids)
    assert all(intended_output(grid) != bbox_shortcut_output(grid) for grid in grids)
    seen = {tuple(observed(grid).values()) for grid in grids}
    assert len(seen) >= 5


def _palette_topology(grid):
    color_sets = [
        {grid[row][col] for row, col in cells}
        for cells in probe.components(grid)
    ]
    monochrome = [next(iter(colors)) for colors in color_sets if len(colors) == 1]
    return {
        "mixed": any(len(colors) > 1 for colors in color_sets),
        "reused": len(monochrome) != len(set(monochrome)),
    }


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_draws_teach_binary_mask_palette_semantics(band):
    grids = [gen.generate(27182, index, difficulty=band) for index in range(12)]
    assert gen.self_check(probe.binary_mask_counterexample()) == []
    assert all(any(value == 9 for row in grid for value in row) for grid in grids)
    assert all(probe.color_partition_output(grid) != intended_output(grid) for grid in grids)
    assert all(probe.nonzero_output(grid) != intended_output(grid) for grid in grids)
    modes = {_palette_topology(grid)["mixed"] for grid in grids}
    assert modes == {False, True}
    assert all(
        _palette_topology(grid)["mixed"] or _palette_topology(grid)["reused"]
        for grid in grids
    )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_three_demo_lessons_identify_the_declared_competitor_under_rotations(band):
    for start in range(4):
        pairs = [_pair(gen.generate(12000, start + offset, difficulty=band)) for offset in range(4)]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_self_check_rejects_structural_impostors_without_raising():
    valid = gen.generate(44, 3, grid_h=9, grid_w=25, object_count=3, max_depth=3, irregular_count=2)
    mutations = []

    ragged = deepcopy(valid)
    ragged[-1].pop()
    mutations.append(ragged)

    illegal = deepcopy(valid)
    illegal[0][0] = 10
    mutations.append(illegal)

    blank = [[0] * 25 for _ in range(9)]
    mutations.append(blank)

    boolean_cell = deepcopy(valid)
    boolean_cell[0][0] = True
    mutations.append(boolean_cell)

    for grid in mutations:
        errors = gen.self_check(grid)
        assert isinstance(errors, list) and errors
        assert all(isinstance(error, str) and error for error in errors)


def test_mutation_fixtures_remain_must_reject_inputs():
    for name, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), name


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(20261007)
    state = random.getstate()
    first = gen.generate(2026, 1007, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(2026, 1007, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 8 if first[0][0] != 8 else 7
    assert first != second


def test_racket_authority_matches_independent_oracle_on_witnesses():
    from arcpuzzles import Catalog

    grids = [pair["input"] for pair in canonical_pairs()]
    grids.append(exact_counterexample())
    grids.append(probe.binary_mask_counterexample())
    grids.extend(gen.generate(51000, index, difficulty="hard") for index in range(4))
    grids.extend(
        [
            gen.generate(
                51001,
                10,
                difficulty="easy",
                grid_h=9,
                grid_w=25,
                object_count=4,
                max_depth=4,
                irregular_count=3,
            ),
            gen.generate(
                51002,
                11,
                difficulty="hard",
                grid_h=18,
                grid_w=30,
                object_count=3,
                max_depth=2,
                irregular_count=1,
            ),
        ]
    )
    receipt = Catalog(HOME.parents[1]).apply(gen.TASK_ID, grids, reference="canonical", timeout=180)
    assert receipt["rule_hash_matches_catalog"]
    assert [item["output"] for item in receipt["results"]] == [intended_output(grid) for grid in grids]


def test_output_rows_are_not_locked_to_one_depth_multiset_per_axis_tuple():
    """Mirror the lint diversity cohort and require its warning boundary."""
    rows = []
    for episode in range(24):
        seed = episode * 101
        for sample_index in range(6):
            rows.append(tuple(intended_output(gen.generate(seed, sample_index))[0]))
    assert len(set(rows)) / len(rows) >= 0.35


def test_binary_mask_census_tool_checks_both_topologies():
    source = HOME / "workspace" / "binary_mask_census.py"
    assert source.is_file()
    spec = importlib.util.spec_from_file_location("binary_mask_census", source)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run_census(full=False)
    assert report["failures"] == []
    assert report["topology_counts"] == {"mixed": 1, "reused": 1}
