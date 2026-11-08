"""Focused regressions for the reviewed eb60199b6eb8 generator."""
from __future__ import annotations

from copy import deepcopy
from importlib.util import module_from_spec, spec_from_file_location
import os
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "eb60199b6eb8"
REPO_ROOT = find_root(__file__)
HOME = REPO_ROOT / "generators" / TASK_ID
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = spec_from_file_location(f"task_generator_{TASK_ID}", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _intended(grid):
    """Independent Python reading of the unchanged canonical row rule."""
    output = [[0 for _ in row] for row in grid]
    for row_index, row in enumerate(grid):
        positions = [column for column, value in enumerate(row) if value != 0]
        if len(positions) != 2:
            continue
        left, right = positions
        if row[left] != row[right]:
            continue
        for column in range(left, right + 1):
            output[row_index][column] = row[left]
    return output


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_declares_the_source_bound_contract():
    assert GEN.RULE_HASH == "7d5c5a67ac1a"
    assert GEN.EXAMPLES_NEEDED == 2
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_rows", "n_distinct_colors"}
    assert callable(GEN.self_check)
    assert callable(GEN.strict_canonical_like)
    assert callable(GEN.observe_overrides)


@pytest.mark.parametrize("pair", _pairs())
def test_canonical_inputs_remain_lawful_and_match_independent_oracle(pair):
    before = deepcopy(pair["input"])
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert _intended(pair["input"]) == pair["output"]
    assert pair["input"] == before


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 4, "grid_w": 5, "n_rows": 2, "n_distinct_colors": 5},
        {"grid_h": 10, "grid_w": 12, "n_rows": 3, "n_distinct_colors": 3},
    ],
)
def test_exact_overrides_round_trip_in_every_band(band, requested):
    grid = GEN.generate(17, 9, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"palette_kind": "warm"},
        {"texture": "no_pairs"},
        {"grid_h": True},
        {"grid_h": 3},
        {"grid_w": 4},
        {"n_rows": 0},
        {"n_rows": 4},
        {"n_distinct_colors": 2},
        {"n_distinct_colors": 6},
        {"grid_h": 4, "n_rows": 3},
    ],
)
def test_invalid_retired_or_incompatible_overrides_are_rejected(overrides):
    with pytest.raises(ValueError):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_canonical_profile_anchor_is_generated_in_every_band(band):
    grid = GEN.generate(30, 0, difficulty=band)
    assert _profile(grid) in {(4, 5, 4), (4, 6, 4), (4, 7, 4)}
    assert GEN.observe_overrides(grid)["n_rows"] == 2
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_distribution_is_deterministic_lawful_and_teaches_both_decoys(band):
    profiles = set()
    row_counts = set()
    color_counts = set()
    for index in range(36):
        grid = GEN.generate(700 + index, index, difficulty=band)
        assert grid == GEN.generate(700 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.SEMANTIC_WITNESSES["mismatched_pair_row"](grid)
        assert GEN.SEMANTIC_WITNESSES["triple_outer_match_row"](grid)
        observed = GEN.observe_overrides(grid)
        profiles.add(_profile(grid))
        row_counts.add(observed["n_rows"])
        color_counts.add(observed["n_distinct_colors"])
    assert any(profile in {(4, 5, 4), (4, 6, 4), (4, 7, 4)} for profile in profiles)
    assert {1, 2, 3} <= row_counts
    assert {3, 4, 5} <= color_counts


def test_generated_example_refutes_every_declared_rival():
    grid = GEN.generate(901, 1, difficulty="hard")
    truth = _intended(grid)
    for name, rival in GEN.SEMANTIC_RIVALS.items():
        assert rival(grid) != truth, name


def test_canonical_fitting_shortcuts_really_fit_every_canonical_label():
    for name in ("connect_any_two", "connect_outermost_same"):
        rival = GEN.CANONICAL_SHORTCUTS[name]
        assert all(rival(pair["input"]) == pair["output"] for pair in _pairs()), name


def test_lesson_identifiable_reports_no_surviving_declared_rival():
    demos = []
    for index in range(2):
        grid = GEN.generate(1200 + index, index)
        demos.append({"input": grid, "output": _intended(grid)})
    query_grid = GEN.generate(1202, 2)
    query = {"input": query_grid, "output": _intended(query_grid)}
    assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 5 for _ in range(4)],
        [[1, 1, 1, 1, 0] for _ in range(4)],
        [[0, 1, 1, 0, 0] for _ in range(4)],  # adjacent pair is outside the sampler domain
    ],
)
def test_self_check_returns_diagnostics_for_malformed_or_out_of_domain_grids(grid):
    assert GEN.self_check(grid)


def test_retained_counterexample_refutes_every_declared_canonical_shortcut():
    import json

    asset_path = HOME / "counterexamples" / "canonical_shortcut_witness.json"
    asset = json.loads(asset_path.read_text())
    grid = asset["input"]
    assert GEN.self_check(grid) == []
    assert _intended(grid) == asset["expected_output"]
    for name in asset["refutes"]:
        assert GEN.CANONICAL_SHORTCUTS[name](grid) != asset["expected_output"], name
