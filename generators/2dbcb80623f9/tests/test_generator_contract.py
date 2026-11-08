"""Source-bound regressions for the 2dbcb80623f9 repair."""
from __future__ import annotations

import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    axis_or_diagonal_rival,
    canonical_pairs,
    load_generator,
    observe,
    pairwise_disjoint,
    path_footprints,
    solve_geometry,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs())
def test_canonical_inputs_are_accepted_and_python_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert solve_geometry(pair["input"]) == pair["output"]


def test_contract_is_source_bound_and_axes_are_honest():
    assert gen.RULE_HASH == "1c2557609ca3"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_pairs", "n_distractors"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_extreme_exact_overrides_are_observable_in_every_band(band):
    requested = {"grid_h": 8, "grid_w": 8, "n_pairs": 4, "n_distractors": 2}
    grid = gen.generate(71, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert {key: observe(grid)[key] for key in requested} == requested
    assert pairwise_disjoint(path_footprints(grid))


@pytest.mark.parametrize(
    "args",
    [
        {"seed": True, "sample_index": 0},
        {"seed": 0, "sample_index": True},
        {"seed": 0, "sample_index": -1},
        {"seed": 0, "sample_index": 0, "difficulty": "expert"},
        {"seed": 0, "sample_index": 0, "typo_axis": 1},
        {"seed": 0, "sample_index": 0, "n_pairs": True},
        {"seed": 0, "sample_index": 0, "n_distractors": 1.0},
        {"seed": 0, "sample_index": 0, "grid_h": 7},
        {"seed": 0, "sample_index": 0, "grid_w": 15},
        {"seed": 0, "sample_index": 0, "n_pairs": 0},
        {"seed": 0, "sample_index": 0, "n_distractors": 3},
    ],
)
def test_invalid_calls_are_rejected(args):
    kwargs = dict(args)
    seed = kwargs.pop("seed")
    sample_index = kwargs.pop("sample_index")
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises(ValueError):
        gen.generate(seed, sample_index, difficulty=difficulty, **kwargs)


def test_axis_rival_fits_all_canonical_pairs_but_generated_witness_refutes_it():
    assert all(axis_or_diagonal_rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    grid = gen.generate(31, 1)
    assert gen.SEMANTIC_WITNESSES["axis_distractor"](grid)
    intended = solve_geometry(grid)
    rival = gen.SEMANTIC_RIVALS["axis_or_diagonal"](grid)
    assert rival == axis_or_diagonal_rival(grid)
    assert rival != intended


@pytest.mark.parametrize("start", range(12))
def test_every_default_four_pair_window_remains_rotation_identifiable(start):
    pairs = []
    for index in range(start, start + 4):
        grid = gen.generate(103, index, difficulty="medium")
        assert gen.self_check(grid) == []
        assert len({value for row in grid for value in row if value}) == 3
        pairs.append({"input": grid, "output": solve_geometry(grid)})
    assert sum(gen.SEMANTIC_WITNESSES["axis_distractor"](pair["input"]) for pair in pairs) >= 2
    for query_index in range(4):
        demos = [pair for i, pair in enumerate(pairs) if i != query_index]
        assert gen.lesson_identifiable(demos, pairs[query_index]) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_distribution_is_deterministic_lawful_and_varied(band):
    shapes = set()
    diagonal_slopes = set()
    seen_witness = False
    for index in range(80):
        grid = gen.generate(900 + index, index, difficulty=band)
        assert grid == gen.generate(900 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        stats = observe(grid)
        assert stats["n_pairs"] >= 1
        assert stats["n_pairs"] + stats["n_distractors"] == 3
        assert pairwise_disjoint(path_footprints(grid))
        assert solve_geometry(grid) != grid
        seen_witness |= bool(stats["axis_distractors"])
        shapes.add((len(grid), len(grid[0])))
        for color in {v for row in grid for v in row if v}:
            cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == color]
            dr, dc = cells[1][0] - cells[0][0], cells[1][1] - cells[0][1]
            if dr and abs(dr) == abs(dc):
                diagonal_slopes.add(1 if dr * dc > 0 else -1)
    assert len(shapes) == 4
    # Endpoint order is immaterial; both diagonal slopes must be represented.
    assert diagonal_slopes == {-1, 1}
    assert seen_witness
