from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "b1e6ee6856bf"
HERE = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HERE / "generator.py"))
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_canonical_pairs_are_accepted_and_match_reference(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.reference_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_honored_in_every_band(band):
    requested = {"grid_h": 14, "grid_w": 14, "n_cols": 5, "stack_depth": 5}
    grid = gen.generate(1729, 23, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 4),
        ("grid_h", 15),
        ("grid_w", 4),
        ("grid_w", 15),
        ("n_cols", 0),
        ("n_cols", 6),
        ("stack_depth", 1),
        ("stack_depth", 6),
        ("grid_h", True),
        ("n_cols", 2.0),
        ("stack_depth", "3"),
    ],
)
def test_invalid_overrides_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_scheduled_canonical_profile_hits_shape_and_full_palette(band):
    grid = gen.generate(91, 0, difficulty=band)
    assert (len(grid), len(grid[0])) == (5, 5)
    assert {value for row in grid for value in row} == set(range(10))
    assert gen.observe_overrides(grid) == {
        "grid_h": 5,
        "grid_w": 5,
        "n_cols": 5,
        "stack_depth": 3,
    }


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_lawful_deterministic_and_teaches_three_cell_case(band):
    shapes = set()
    palettes = set()
    top_rows = set()
    for index in range(96):
        grid = gen.generate(3100 + index, index, difficulty=band)
        assert grid == gen.generate(3100 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        assert 1 <= observed["n_cols"] <= 5
        assert 3 <= observed["stack_depth"] <= 5
        assert gen.SEMANTIC_WITNESSES["three_cell_column"](grid)
        shapes.add((len(grid), len(grid[0])))
        palettes.add(tuple(sorted({value for row in grid for value in row if value})))
        top_rows.update(
            min(r for r, row in enumerate(grid) if row[c] != 0)
            for c in range(len(grid[0]))
            if any(row[c] != 0 for row in grid)
        )
    assert len(shapes) >= 12
    assert len(palettes) >= 8
    assert len(top_rows) >= 4


def test_canonical_fitting_rival_is_refuted_by_generated_three_cell_column():
    rival = gen.SEMANTIC_RIVALS["erase_one_bottom_cell"]
    assert all(rival(pair["input"]) == pair["output"] for pair in _canonical_pairs())
    witness = gen.generate(77, 1, grid_h=7, grid_w=7, n_cols=3, stack_depth=4)
    assert gen.SEMANTIC_WITNESSES["three_cell_column"](witness)
    assert rival(witness) != gen.reference_output(witness)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 5 for _ in range(5)]],
)
def test_malformed_grids_return_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)



def test_dense_named_impostors_are_outside_the_lesson_domain():
    full_one_color = [[1] * 5 for _ in range(5)]
    solid_2x2 = [[0] * 5 for _ in range(5)]
    for row in range(2):
        for column in range(2):
            solid_2x2[row][column] = 1
    assert gen.self_check(full_one_color)
    assert gen.self_check(solid_2x2)


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 5, "grid_w": 5, "n_cols": 5, "stack_depth": 5},
        {"grid_h": 5, "grid_w": 5, "n_cols": 2, "stack_depth": 2},
    ],
)
def test_exact_boundary_overrides_never_emit_named_dense_impostors(overrides):
    for seed in range(128):
        grid = gen.generate(seed, seed, **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides

def test_identity_inputs_are_rejected_but_rule_remains_total():
    identity = [[0] * 5 for _ in range(5)]
    identity[1][0] = 2
    identity[3][2] = 7
    assert gen.self_check(identity)
    assert gen.reference_output(identity) == identity



def test_retained_three_cell_counterexample_refutes_one_erasure_shortcut():
    payload = json.loads((HERE / "counterexamples" / "erase_one_bottom_cell.json").read_text())
    grid = payload["input"]
    expected = payload["intended_output"]
    rival_output = payload["rival_output"]
    assert gen.self_check(grid) == []
    assert gen.reference_output(grid) == expected
    assert gen.SEMANTIC_RIVALS[payload["rival"]](grid) == rival_output
    assert rival_output != expected

def test_metadata_is_pinned_and_contract_is_minimal():
    assert gen.RULE_HASH == "3a3d82df16cd"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_cols", "stack_depth"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert gen.MIN_STRICT_FRAC == 1.0
