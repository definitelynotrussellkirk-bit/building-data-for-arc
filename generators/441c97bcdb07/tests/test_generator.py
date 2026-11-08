from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import random
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs as load_canonical_pairs, canonical_path, find_root

TASK_ID = "441c97bcdb07"
ROOT = find_root(__file__)
DEFAULT_GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_GENERATOR.is_file():
    DEFAULT_GENERATOR = (
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    )
MODULE_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)
PAIRS = load_canonical_pairs(TASK_ID, root=ROOT, variant=0)


def _canonical_rule_hash() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                source = str(row["program_solution"])
                return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    raise AssertionError("canonical rule source is missing")


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def _signature(grid):
    return tuple(tuple(row) for row in grid)


def test_authority_is_pinned_and_python_mirror_matches_all_canonical_pairs():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == _canonical_rule_hash() == "a51bdd8a29a6"
    assert len(PAIRS) == 3
    for item in PAIRS:
        before = copy.deepcopy(item["input"])
        assert GEN.self_check(item["input"]) == []
        assert GEN.strict_canonical_like(item["input"]) == []
        assert GEN.rule_mirror(item["input"]) == item["output"]
        assert item["input"] == before


def test_exact_override_boundaries_are_total_and_observable_in_every_band():
    assert set(GEN.AXES) == {"grid_h", "grid_w", "shape_id"}
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()
    cases = (
        {"grid_h": 9, "grid_w": 9, "shape_id": 7},
        {"grid_h": 22, "grid_w": 22, "shape_id": 4},
        {"grid_h": 9, "grid_w": 22, "shape_id": 9},
        {"grid_h": 22, "grid_w": 9, "shape_id": 0},
    )
    for band in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = GEN.generate(1000 + index, index, difficulty=band, **requested)
            assert GEN.self_check(grid, difficulty=band) == []
            assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_axis": 1},
        {"grid_h": 8},
        {"grid_h": 23},
        {"grid_w": 8},
        {"grid_w": 23},
        {"shape_id": -1},
        {"shape_id": 10},
        {"grid_h": True},
        {"grid_w": 10.0},
        {"shape_id": "4"},
    ],
)
def test_unknown_and_invalid_overrides_reject_loudly(overrides):
    with pytest.raises((TypeError, ValueError), match="override|grid|shape|integer|axis"):
        GEN.generate(1, 0, **overrides)


def test_default_schedule_has_a_non_four_cell_counterexample_in_every_three_demos():
    assert GEN.EXAMPLES_NEEDED == 3
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "non_four_cell_counterexample",
        "four_cell_anchor",
    )
    for band in ("easy", "medium", "hard"):
        for seed in (0, 17, 998877):
            for start in range(32):
                grids = [
                    GEN.generate(seed, start + offset, difficulty=band)
                    for offset in range(GEN.EXAMPLES_NEEDED)
                ]
                assert any(
                    GEN.SEMANTIC_WITNESSES["non_four_cell_shape"](grid)
                    for grid in grids
                ), (band, seed, start)
                demos = [_pair(grid) for grid in grids]
                query_grid = GEN.generate(
                    seed, start + GEN.EXAMPLES_NEEDED, difficulty=band
                )
                assert GEN.lesson_identifiable(demos, _pair(query_grid)) == []


def test_four_cell_only_shortcut_fits_canonical_but_generated_witnesses_refute_it():
    name = "four_cell_only"
    assert name in GEN.CANONICAL_SHORTCUTS
    assert name in GEN.SEMANTIC_RIVALS
    assert name in GEN.LESSON_COMPETITORS
    assert GEN.WITNESS_RIVALS["non_four_cell_shape"] == [name]

    shortcut = GEN.CANONICAL_SHORTCUTS[name]
    for item in PAIRS:
        assert shortcut(item["input"]) == item["output"]

    for band in ("easy", "medium", "hard"):
        for sample_index in range(0, 32, 2):
            grid = GEN.generate(424242, sample_index, difficulty=band)
            assert GEN.schedule_profile(424242, sample_index, band) == (
                "non_four_cell_counterexample"
            )
            assert GEN.SEMANTIC_WITNESSES["non_four_cell_shape"](grid)
            assert shortcut(grid) != GEN.rule_mirror(grid)


def test_every_rotation_of_each_four_pair_window_remains_identifiable():
    for band in ("easy", "medium", "hard"):
        for seed in (31, 91):
            for start in range(20):
                labelled = [
                    _pair(GEN.generate(seed, start + offset, difficulty=band))
                    for offset in range(GEN.EXAMPLES_NEEDED + 1)
                ]
                for query_index in range(len(labelled)):
                    demos = [
                        item for index, item in enumerate(labelled)
                        if index != query_index
                    ]
                    assert GEN.lesson_identifiable(
                        demos, labelled[query_index]
                    ) == [], (band, seed, start, query_index)


def test_self_check_rejects_minimal_and_task_specific_impostors():
    blank = [[0] * 10 for _ in range(10)]
    full = [[2] * 10 for _ in range(10)]
    singleton_corners = copy.deepcopy(blank)
    for r, c in ((1, 1), (1, 7), (7, 1)):
        singleton_corners[r][c] = 2
    short_line_corners = copy.deepcopy(blank)
    for top, left in ((1, 1), (1, 7), (7, 1)):
        short_line_corners[top][left] = 2
        short_line_corners[top][left + 1] = 2
    solid_2x2_corners = copy.deepcopy(blank)
    for top, left in ((1, 1), (1, 7), (7, 1)):
        for dr in range(2):
            for dc in range(2):
                solid_2x2_corners[top + dr][left + dc] = 2

    for name, grid in (
        ("blank", blank),
        ("full", full),
        ("singleton corners", singleton_corners),
        ("short-line corners", short_line_corners),
        ("solid-2x2 corners", solid_2x2_corners),
        ("ragged", [[0, 2, 0], [0, 0]]),
        ("bad color", [[0, 11], [0, 0]]),
        ("bool cell", [[0, False], [0, 0]]),
    ):
        before = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == before

    fixtures = dict(GEN.mutation_fixtures())
    assert {
        "blank",
        "singletons",
        "short_lines",
        "solid_2x2",
        "missing_copy",
        "mismatched_copy",
        "filled_bottom_right",
        "ragged",
    } <= set(fixtures)
    assert all(GEN.self_check(grid) for grid in fixtures.values())


def test_generated_distribution_is_lawful_diverse_and_spans_every_shape_id():
    inputs = set()
    observed_shapes = set()
    observed_sizes = set()
    for band in ("easy", "medium", "hard"):
        for sample_index in range(80):
            grid = GEN.generate(20261006, sample_index, difficulty=band)
            assert GEN.self_check(grid, difficulty=band) == []
            assert GEN.strict_canonical_like(grid) == []
            observed = GEN.observe_overrides(grid)
            observed_shapes.add(observed["shape_id"])
            observed_sizes.add((observed["grid_h"], observed["grid_w"]))
            output = GEN.rule_mirror(grid)
            assert output != grid
            assert sum(value != 0 for row in output for value in row) == (
                4 * sum(value != 0 for row in grid for value in row) // 3
            )
            inputs.add(_signature(grid))
    assert observed_shapes == set(range(10))
    assert len(observed_sizes) >= 4
    assert len(inputs) >= 220


def test_replay_is_deterministic_fresh_and_does_not_touch_global_random_state():
    random.seed(20261006)
    before = random.getstate()
    first = GEN.generate(823, 103, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(823, 103, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(823, 103, difficulty="hard") == second
