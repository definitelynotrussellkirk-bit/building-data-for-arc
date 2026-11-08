"""Task-local behavioral regressions for the repaired trio-rotation sampler."""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (canonical_pairs, intended_output, load_generator,
                             observed, racket_outputs, vertical_runs)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def assert_default_teaching_witnesses(grid):
    stats = observed(grid)
    assert stats["short_count"] == 1
    assert stats["long_count"] == 1
    assert stats["edge_count"] == 1
    assert stats["edge_side"] in {"left", "right"}
    assert stats["target_count"] >= 1
    return stats


def test_authority_pin_and_public_contract_are_current():
    assert gen.VERSION == "2.0.0"
    assert gen.RULE_HASH == "fc2cfb863af5"
    assert set(gen.AXES) == {"grid_h", "grid_w", "target_count",
                             "n_distinct_colors", "edge_side"}


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_canonical_examples_remain_accepted_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("options", [
    dict(grid_h=6, grid_w=8, target_count=1, n_distinct_colors=4, edge_side="left"),
    dict(grid_h=6, grid_w=8, target_count=5, n_distinct_colors=2, edge_side="right"),
    dict(grid_h=15, grid_w=17, target_count=1, n_distinct_colors=2, edge_side="right"),
    dict(grid_h=15, grid_w=17, target_count=5, n_distinct_colors=4, edge_side="left"),
])
def test_exact_joint_controls_are_observable_in_pixels(band, options):
    grid = gen.generate(701, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    stats = assert_default_teaching_witnesses(grid)
    assert {name: stats[name] for name in options} == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize("bad", [
    {"grid_h": 5}, {"grid_h": 16}, {"grid_w": 7}, {"grid_w": 18},
    {"target_count": 0}, {"target_count": 6},
    {"n_distinct_colors": 1}, {"n_distinct_colors": 5},
    {"edge_side": "both"}, {"grid_h": True}, {"grid_w": 8.5},
    {"target_count": "3"}, {"palette_kind": "warm"}, {"texture": "default"},
    {"density": "sparse"}, {"position_bias": "vertical_3_runs"},
])
def test_invalid_and_retired_controls_fail_loudly(bad):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **bad)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_deterministic_and_teaches_exact_filtering(band):
    shapes = set()
    sides = set()
    targets = set()
    palettes = set()
    for index in range(60):
        grid = gen.generate(9000 + index, index, difficulty=band)
        assert grid == gen.generate(9000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        stats = assert_default_teaching_witnesses(grid)
        assert intended_output(grid) != grid
        assert gen.lesson_identifiable([{"input": grid, "output": intended_output(grid)}], None) == []
        shapes.add((stats["grid_h"], stats["grid_w"]))
        sides.add(stats["edge_side"])
        targets.add(stats["target_count"])
        palettes.add(stats["n_distinct_colors"])
    assert {(7, 9), (6, 10), (8, 8)} & shapes
    assert sides == {"left", "right"}
    assert len(targets) >= 3
    assert palettes == {2, 3, 4}


def test_declared_shortcuts_fit_all_canonical_pairs_but_not_generated_witnesses():
    pairs = canonical_pairs()
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name
    for index in range(24):
        grid = gen.generate(313, index)
        expected = intended_output(grid)
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert rival(grid) != expected, (index, name)


def test_every_query_rotation_of_a_four_pair_window_remains_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            for offset in range(4):
                grid = gen.generate(1221 + start, start * 7 + offset, difficulty=band)
                pairs.append({"input": grid, "output": intended_output(grid)})
            for query_index in range(4):
                demos = [pair for i, pair in enumerate(pairs) if i != query_index]
                assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_generated_runs_are_clean_and_outputs_do_not_collide():
    for index in range(120):
        grid = gen.generate(77, index, difficulty="hard")
        runs = vertical_runs(grid)
        stats = observed(grid)
        assert len(runs) == stats["target_count"] + 3
        output = intended_output(grid)
        target_cells = []
        for run in runs:
            if run["length"] == 3 and 0 < run["c"] < len(grid[0]) - 1:
                row = run["r0"] + 1
                target_cells.extend((row, c) for c in range(run["c"] - 1, run["c"] + 2))
        assert len(target_cells) == len(set(target_cells))
        assert sum(v != 0 for row in output for v in row) == 3 * stats["target_count"]


def test_fresh_returns_and_self_check_mutation_sensitivity():
    grid = gen.generate(44, 5, target_count=3, edge_side="left")
    expected = [row[:] for row in grid]
    grid[0][0] = 99
    assert gen.generate(44, 5, target_count=3, edge_side="left") == expected

    malformed = [row[:] for row in expected]
    # Add a horizontal neighbor to create a non-vertical connected object.
    hit = next((r, c) for r, row in enumerate(malformed) for c, v in enumerate(row)
               if v and c + 1 < len(row) and row[c + 1] == 0)
    malformed[hit[0]][hit[1] + 1] = malformed[hit[0]][hit[1]]
    assert gen.self_check(malformed)


def test_real_racket_authority_matches_oracle_on_canonical_and_generated_grids():
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(555, index, difficulty=("easy", "medium", "hard")[index % 3])
              for index in range(36)]
    assert racket_outputs(grids) == [intended_output(grid) for grid in grids]
