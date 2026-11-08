from __future__ import annotations

import json
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.cf976dae6b92 import generator as gen
from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)


def _canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row not found")


def test_python_mirror_matches_every_canonical_pair():
    row = _canonical_row()
    pairs = [*row["train"], *row["test"]]
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_all_schedule_profiles_and_direction_signatures_are_realized():
    profiles = set()
    directions = set()
    for sample_index in range(36):
        grid = gen.generate(4401, sample_index, difficulty="medium")
        observed = gen.observe_overrides(grid)
        profiles.add(f"rows={observed['row_order']}|cols={observed['col_order']}")
        directions.add(gen.analyze_scene(grid)["facts"]["direction_signature"])
    assert profiles == set(gen.SCHEDULE_PROFILES)
    assert len(directions) == 16


def test_exact_override_boundaries_are_observable():
    for grid_h in (7, 18):
        for grid_w in (7, 18):
            for row_order in gen.ROW_ORDERS:
                for col_order in gen.COL_ORDERS:
                    requested = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "row_order": row_order,
                        "col_order": col_order,
                    }
                    grid = gen.generate(991, 3, difficulty="easy", **requested)
                    assert gen.self_check(grid, meta={"overrides": requested}) == []
                    assert gen.observe_overrides(grid) == requested


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=7)


def test_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_lessons_refute_named_competitors():
    demos = []
    for sample_index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(8221, sample_index, difficulty="medium")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(8221, gen.EXAMPLES_NEEDED, difficulty="medium")
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []


def test_noncanonical_size_refutes_canonical_size_shortcut():
    grid = gen.generate(77, 1, difficulty="easy", grid_h=7, grid_w=8)
    expected = gen.rule_mirror(grid)
    assert gen.SEMANTIC_RIVALS["only_transform_13x13"](grid) != expected
    assert gen.SEMANTIC_WITNESSES["noncanonical_size_refutes_13_only"](grid)


@pytest.mark.parametrize("bad_value", [True, 7.0, "7"])
def test_dimension_overrides_reject_non_exact_integers(bad_value):
    """A coercive dimension override can hide malformed controller payloads."""
    with pytest.raises(TypeError, match="override must be an integer"):
        gen.generate(13, 0, grid_h=bad_value)
