"""Source-bound regression tests for bbbec840ce41."""
from __future__ import annotations

from collections import Counter
import importlib.util
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root

SPEC = importlib.util.spec_from_file_location(
    "review_bbbec840ce41", HERE.parents[1] / "generator.py"
)
gen = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gen)

TASK_ID = "bbbec840ce41"
CANONICAL_PROFILES = {(8, 8, 5), (8, 8, 6), (9, 9, 7), (9, 9, 8), (10, 10, 7)}


def anti_diagonal_output(grid: list[list[int]]) -> list[list[int]]:
    n = len(grid)
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                out[n - 1 - c][n - 1 - r] = value
    return out


def profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def off_axis_unique_anchors(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    n = len(grid)
    counts = Counter(value for row in grid for value in row if value)
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value and counts[value] == 1 and r + c < n - 1 and r != c
    ]


def test_rule_hash_is_pinned_to_reviewed_authority():
    assert gen.RULE_HASH == "655e255b5949"


def test_canonical_inputs_are_accepted_and_match_independent_oracle():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert anti_diagonal_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_generation_is_deterministic_lawful_and_nonidentity(difficulty):
    seen = set()
    for index in range(24):
        grid = gen.generate(4100 + index, index, difficulty=difficulty)
        assert grid == gen.generate(4100 + index, index, difficulty=difficulty)
        assert gen.self_check(grid) == []
        assert anti_diagonal_output(grid) != grid
        assert off_axis_unique_anchors(grid)
        seen.add(tuple(tuple(row) for row in grid))
    assert len(seen) == 24


@pytest.mark.parametrize(
    "options",
    [
        {"grid_n": 6, "n_cells": 4, "n_colors": 2, "n_axis": 0},
        {"grid_n": 8, "n_cells": 6, "n_colors": 5, "n_axis": 1},
        {"grid_n": 9, "n_cells": 8, "n_colors": 7, "n_axis": 2},
        {"grid_n": 16, "n_cells": 12, "n_colors": 7, "n_axis": 3},
    ],
)
def test_every_advertised_override_is_exact_and_observable(options):
    for difficulty in (None, "easy", "medium", "hard"):
        grid = gen.generate(17, 29, difficulty=difficulty, **options)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_n": 5},
        {"grid_n": 17},
        {"n_cells": 3},
        {"n_cells": 13},
        {"n_colors": 1},
        {"n_colors": 8},
        {"n_axis": -1},
        {"n_axis": 4},
        {"grid_n": True},
        {"n_cells": 6.0},
        {"n_colors": "4"},
    ],
)
def test_invalid_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, **kwargs)


def test_incompatible_exact_counts_have_structured_rejection():
    with pytest.raises(ValueError) as caught:
        gen.generate(1, 2, n_cells=4, n_colors=7)
    assert set(caught.value.incompatible_axes) == {"n_cells", "n_colors"}

    with pytest.raises(ValueError) as caught:
        gen.generate(1, 2, n_cells=4, n_axis=4)
    assert set(caught.value.incompatible_axes) == {"n_cells", "n_axis"}


def test_constructive_palette_keeps_a_unique_non8_coordinate_anchor():
    for seed in range(40):
        grid = gen.generate(seed, seed + 3, n_cells=12, n_colors=2, n_axis=3)
        observed = gen.observe_overrides(grid)
        assert observed == {"grid_n": observed["grid_n"], "n_cells": 12, "n_colors": 2, "n_axis": 3}
        anchors = off_axis_unique_anchors(grid)
        assert any(value != 8 for _, _, value in anchors)


def test_default_schedule_guarantees_canonical_profile_support_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        grids = [gen.generate(700 + i, i, difficulty=difficulty) for i in range(20)]
        exact = [grid for grid in grids if profile(grid) in CANONICAL_PROFILES]
        assert len(exact) >= 5
        assert all(profile(grids[i]) in CANONICAL_PROFILES for i in range(0, 20, 4))


def test_semantic_witnesses_are_real_counterexamples_to_named_rivals():
    for index in range(32):
        grid = gen.generate(900 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        truth = anti_diagonal_output(grid)
        for witness_name, predicate in gen.SEMANTIC_WITNESSES.items():
            assert predicate(grid), witness_name
            for rival_name in gen.WITNESS_RIVALS[witness_name]:
                assert gen.SEMANTIC_RIVALS[rival_name](grid) != truth


def test_every_four_demo_window_refutes_all_declared_lesson_competitors():
    for difficulty in ("easy", "medium", "hard"):
        pairs = []
        for index in range(12):
            grid = gen.generate(1200, index, difficulty=difficulty)
            pairs.append({"input": grid, "output": anti_diagonal_output(grid)})
        for start in range(0, 9):
            demos = pairs[start : start + 4]
            query = pairs[(start + 4) % len(pairs)]
            assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 0], [0, 0]],
        [[10, 0], [0, 0]],
        [[0] * 8 for _ in range(8)],
        [[1, 0], [0, 0]],
    ],
)
def test_self_check_rejects_malformed_or_non_teaching_inputs(bad):
    assert gen.self_check(bad)


def test_self_check_rejects_lower_triangle_and_missing_coordinate_anchor():
    lower = [[0] * 8 for _ in range(8)]
    for r, c, value in [(0, 0, 1), (0, 1, 2), (1, 0, 3), (7, 7, 4)]:
        lower[r][c] = value
    assert gen.self_check(lower)

    no_anchor = [[0] * 8 for _ in range(8)]
    for r, c, value in [(0, 0, 1), (1, 1, 2), (2, 2, 3), (3, 3, 4)]:
        no_anchor[r][c] = value
    assert gen.self_check(no_anchor)


def test_declared_mutation_fixtures_are_rejected():
    for name, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), name


def test_retained_counterexamples_cover_old_identity_and_semantic_shortcuts():
    import json

    counterexamples = HERE.parents[1] / "counterexamples"
    identity = json.loads((counterexamples / "identity_all_axis.json").read_text())
    assert gen.self_check(identity["input"])
    assert anti_diagonal_output(identity["input"]) == identity["input"]

    semantic = json.loads((counterexamples / "semantic_witness.json").read_text())
    grid = semantic["input"]
    expected = semantic["output"]
    assert gen.self_check(grid) == []
    assert anti_diagonal_output(grid) == expected
    for rival in semantic["refuted_rivals"]:
        assert gen.SEMANTIC_RIVALS[rival](grid) != expected
