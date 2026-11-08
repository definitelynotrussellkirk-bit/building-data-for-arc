"""Task-local regressions for the reviewed aa378df15340 generator."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pytest
from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    TASK_ID,
    load_generator,
    malformed_grids,
    observed,
    teaching_errors,
    transpose_add_output,
    upper_triangle_only,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def test_rule_hash_is_pinned_to_selected_authority():
    assert getattr(gen, "RULE_HASH", None) == "ba8b31fe9030"


@pytest.mark.parametrize("pair", PAIRS)
def test_canonical_inputs_are_owned_and_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert transpose_add_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_n": 5, "n_seeds": 3, "n_colors": 1},
        {"grid_n": 8, "n_seeds": 4, "n_colors": 2},
        {"grid_n": 12, "n_seeds": 9, "n_colors": 3},
        {"grid_n": 6, "n_seeds": 4, "n_colors": 4},
    ],
)
def test_exact_overrides_are_constructive_in_every_band(band, overrides):
    grid = gen.generate(1701, 29, difficulty=band, **overrides)
    assert gen.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
    assert observed(grid) == overrides
    assert gen.observe_overrides(grid) == overrides
    assert teaching_errors(grid) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_n": 4},
        {"grid_n": 13},
        {"n_seeds": 2},
        {"n_seeds": 10},
        {"n_colors": 0},
        {"n_colors": 5},
        {"grid_n": True},
        {"n_seeds": 3.0},
        {"n_colors": "2"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)



def test_rejects_more_colors_than_seeds_as_an_incompatible_pair():
    with pytest.raises(ValueError) as excinfo:
        gen.generate(0, 0, n_seeds=3, n_colors=4)
    assert set(getattr(excinfo.value, "incompatible_axes", ())) == {"n_seeds", "n_colors"}

def test_audited_seed_never_uses_an_occupied_transpose_target():
    grid = gen.generate(0, 2, difficulty=None)
    assert not [error for error in teaching_errors(grid) if "occupied" in error]


def test_retained_collision_counterexample_records_the_semantic_disagreement():
    record_path = HOME / "counterexamples" / "occupied_transpose_pair.json"
    record = json.loads(record_path.read_text())
    assert record["baseline_replay"] == {
        "seed": 0,
        "sample_index": 2,
        "difficulty": None,
    }
    assert transpose_add_output(record["input"]) == record["authority_output"]
    assert record["preserve_occupied_rival_output"] != record["authority_output"]
    repaired = gen.generate(0, 2, difficulty=None)
    assert repaired != record["input"]
    assert teaching_errors(repaired) == []


def test_canonical_shortcut_fits_canonical_pairs_but_not_generated_inputs():
    assert all(upper_triangle_only(pair["input"]) == pair["output"] for pair in PAIRS)
    for index in range(64):
        grid = gen.generate(8100 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        assert teaching_errors(grid) == []
        assert gen.CANONICAL_SHORTCUTS["upper_triangle_only"](grid) == upper_triangle_only(grid)
        assert upper_triangle_only(grid) != transpose_add_output(grid)


def test_default_distribution_is_deterministic_and_covers_declared_ranges():
    sizes: set[int] = set()
    counts: set[int] = set()
    colors: set[int] = set()
    inputs: set[tuple[tuple[int, ...], ...]] = set()
    for index in range(256):
        band = ("easy", "medium", "hard")[index % 3]
        grid = gen.generate(9100 + index, index * 7 + 3, difficulty=band)
        assert grid == gen.generate(9100 + index, index * 7 + 3, difficulty=band)
        assert gen.self_check(grid, difficulty=band) == []
        assert teaching_errors(grid) == []
        stats = observed(grid)
        sizes.add(stats["grid_n"])
        counts.add(stats["n_seeds"])
        colors.add(stats["n_colors"])
        inputs.add(tuple(tuple(row) for row in grid))
    assert {5, 6, 7, 8} <= sizes
    assert {3, 9} <= counts
    assert colors == {1, 2, 3, 4}
    assert len(inputs) >= 250


@pytest.mark.parametrize("grid", malformed_grids())
def test_malformed_inputs_return_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)


@pytest.mark.parametrize(
    "grid",
    [
        [[0] * 5 for _ in range(5)],
        [
            [3, 0, 0, 0, 0],
            [0, 4, 0, 0, 0],
            [0, 0, 5, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        [
            [0, 7, 0, 0, 0],
            [6, 0, 0, 0, 0],
            [0, 0, 0, 8, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
        [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [7, 7, 0, 7, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
    ],
    ids=["blank", "diagonal_only", "occupied_pair", "horizontal_short_line"],
)
def test_self_check_rejects_non_teaching_impostors(grid):
    assert gen.self_check(grid)


def test_semantic_contract_names_a_real_witness_and_rival():
    for index in range(16):
        grid = gen.generate(111 + index, index)
        assert gen.strict_canonical_like(grid) == []
        assert gen.SEMANTIC_WITNESSES["lower_triangle_source"](grid)
        assert gen.SEMANTIC_RIVALS["upper_triangle_only"](grid) != transpose_add_output(grid)
        assert gen.WITNESS_RIVALS["lower_triangle_source"] == ["upper_triangle_only"]


def test_lesson_identifiability_hook_accepts_generated_lessons():
    demos = []
    for index in range(3):
        grid = gen.generate(500, index)
        demos.append({"input": grid, "output": transpose_add_output(grid)})
    query_grid = gen.generate(500, 3)
    query = {"input": query_grid, "output": transpose_add_output(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
