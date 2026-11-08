"""Task-local regression tests written before the d57b7deebba2 repair."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    distinct_color_pairs_only,
    has_reused_color,
    intended_output,
    load_generator,
    observed,
    witness_input,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_authority_pin_and_honest_axis_surface():
    assert gen.RULE_HASH == "ed1603229043"
    assert gen.AXES == {
        "grid_h": {"type": "int", "default": "canonical-weighted 7..10", "valid": "7..10"},
        "grid_w": {"type": "int", "default": "canonical-weighted 10..12", "valid": "10..12"},
        "n_pairs": {"type": "int", "default": "canonical-weighted 2..3", "valid": "2..3"},
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "train3", "test0"])
def test_accepts_canonical_inputs_and_independent_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("options", [
    {"grid_h": 7, "grid_w": 10, "n_pairs": 2},
    {"grid_h": 10, "grid_w": 12, "n_pairs": 3},
])
def test_exact_boundary_overrides_work_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize("key,value", [
    ("typo", 1),
    ("grid_h", 6), ("grid_h", 11),
    ("grid_w", 9), ("grid_w", 13),
    ("n_pairs", 1), ("n_pairs", 4),
    ("grid_h", True), ("grid_w", "10"), ("n_pairs", 2.5),
])
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_inputs_are_valid_deterministic_and_oracle_fires(band):
    shapes = set()
    pair_counts = set()
    changed = 0
    for index in range(96):
        grid = gen.generate(600 + index, index, difficulty=band)
        assert grid == gen.generate(600 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        shapes.add((len(grid), len(grid[0])))
        pair_counts.add(observed(grid)["n_pairs"])
        changed += intended_output(grid) != grid
    assert changed == 96
    assert {2, 3} <= pair_counts
    assert {(7, 12), (8, 10), (9, 11), (10, 10)} <= shapes


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_consecutive_three_demo_window_refutes_canonical_shortcut(band):
    for start in range(30):
        demos = [gen.generate(991, start + offset, difficulty=band) for offset in range(3)]
        assert any(has_reused_color(grid) for grid in demos)
        assert any(distinct_color_pairs_only(grid) != intended_output(grid) for grid in demos)
        query = gen.generate(991, start + 3, difficulty=band)
        pairs = [{"input": grid, "output": intended_output(grid)} for grid in demos]
        assert gen.lesson_identifiable(pairs, {"input": query, "output": intended_output(query)}) == []


def test_shortcut_fits_all_canonical_pairs_but_fixed_witness_refutes_it():
    assert all(distinct_color_pairs_only(pair["input"]) == pair["output"] for pair in canonical_pairs())
    grid = witness_input()
    assert gen.self_check(grid) == []
    intended = intended_output(grid)
    rival = distinct_color_pairs_only(grid)
    assert intended != rival
    assert [(r, c) for r in range(7) for c in range(10) if intended[r][c] != rival[r][c]] == [
        (1, 3), (4, 7), (5, 6)
    ]


def test_declared_semantic_contract_executes_on_generated_witness():
    grid = gen.generate(712, 0, grid_h=7, grid_w=10, n_pairs=3)
    assert gen.strict_canonical_like(grid) == []
    assert gen.SEMANTIC_WITNESSES["reused_color"](grid)
    assert gen.SEMANTIC_RIVALS["distinct_color_pairs_only"](grid) == distinct_color_pairs_only(grid)
    assert gen.SEMANTIC_RIVALS["distinct_color_pairs_only"](grid) != intended_output(grid)
    assert gen.WITNESS_RIVALS == {"reused_color": ["distinct_color_pairs_only"]}
    assert gen.CANONICAL_SHORTCUTS["distinct_color_pairs_only"](grid) != intended_output(grid)
    assert gen.LESSON_COMPETITORS["distinct_color_pairs_only"](grid) != intended_output(grid)
    assert gen.EXAMPLES_NEEDED == 3


@pytest.mark.parametrize("start", range(18))
def test_schedule_profile_matches_pixels(start):
    grid = gen.generate(8, start)
    profile = gen.schedule_profile(8, start)
    assert profile in gen.SCHEDULE_PROFILES
    assert (profile == "reused_color") == has_reused_color(grid)


@pytest.mark.parametrize("mutation", [
    "singleton", "same_diag_four_endpoints", "short_span", "long_span",
    "filled_interior", "extra_span", "bad_color", "ragged",
])
def test_validator_rejects_structural_mutations(mutation):
    grid = gen.generate(19, 2, grid_h=8, grid_w=10, n_pairs=2)
    if mutation == "ragged":
        grid[0].pop()
    elif mutation == "bad_color":
        grid[0][0] = 10
    elif mutation == "singleton":
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value:
                    grid[r][c] = 0
                    break
            else:
                continue
            break
    elif mutation == "same_diag_four_endpoints":
        grid = [[0] * 10 for _ in range(7)]
        for r, c in ((0, 6), (1, 5), (3, 3), (5, 1)):
            grid[r][c] = 4
        grid[0][9] = grid[2][7] = 7
    elif mutation == "short_span":
        grid = [[0] * 10 for _ in range(7)]
        grid[1][5] = grid[2][4] = 4
        grid[3][8] = grid[5][6] = 7
    elif mutation == "long_span":
        grid = [[0] * 10 for _ in range(7)]
        grid[0][6] = grid[6][0] = 4
        grid[3][8] = grid[5][6] = 7
    elif mutation == "filled_interior":
        groups = []
        for color in range(1, 10):
            cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
            by_diag = {}
            for cell in cells:
                by_diag.setdefault(sum(cell), []).append(cell)
            groups.extend((color, points) for points in by_diag.values() if len(points) == 2)
        color, points = groups[0]
        (r0, c0), (r1, _c1) = sorted(points)
        grid[r0 + 1][c0 - 1] = color
    elif mutation == "extra_span":
        grid = [[0] * 10 for _ in range(7)]
        for color, cells in ((2, ((0, 4), (2, 2))), (3, ((1, 8), (3, 6))),
                             (4, ((3, 5), (5, 3))), (5, ((4, 9), (6, 7)))):
            for r, c in cells:
                grid[r][c] = color
    assert gen.self_check(grid)


@pytest.mark.parametrize("bad", [None, [], [[]], [[0], [0, 1]], [[True] * 10 for _ in range(7)]])
def test_malformed_grid_returns_diagnostics_not_exceptions(bad):
    assert gen.self_check(bad)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(subprocess.check_output(
            [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
            env=env, text=True,
        ))
    assert results[0] == results[1]


def test_transform_helpers_do_not_mutate_input():
    grid = gen.generate(22, 0)
    original = deepcopy(grid)
    intended_output(grid)
    distinct_color_pairs_only(grid)
    assert grid == original
