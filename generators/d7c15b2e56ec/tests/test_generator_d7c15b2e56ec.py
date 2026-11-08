from __future__ import annotations

import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

TASK = "d7c15b2e56ec"
MOD = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "data/base/solutions/training/7d1f7ee8__d7c15b2e56ec.json"


def canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            return row
    raise AssertionError(f"missing canonical row {TASK}")


def all_pairs(row):
    return [*row["train"], *row["test"]]


def component_key(component):
    return frozenset(component.cells)


def test_canonical_inputs_and_outputs_are_accepted():
    row = canonical_row()
    assert len(row["train"]) == 3
    assert len(row["test"]) == 1
    for pair in all_pairs(row):
        assert MOD.self_check(pair["input"]) == []
        assert MOD.rule_mirror(pair["input"]) == pair["output"]


def test_rule_hash_and_selected_task_source_are_synced():
    row = canonical_row()
    canonical = row["program_solution"]
    digest = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert MOD.RULE_HASH == digest == "0c27de3a540b"
    base = json.loads(BASE_PATH.read_text())
    assert base["racket_target"]["target_code"] == canonical
    # raw_code is deliberately preserved as archival executable source.
    assert base["racket_target"]["raw_code"] != canonical


def test_exact_overrides_round_trip_at_boundaries():
    cases = [
        dict(grid_h=12, grid_w=30, group_count=1, max_depth=2,
             distractor_count=0, include_solid=False, palette_kind="warm"),
        dict(grid_h=30, grid_w=30, group_count=3, max_depth=4,
             distractor_count=3, include_solid=True, palette_kind="cool"),
        dict(grid_h=24, grid_w=24, group_count=2, max_depth=3,
             distractor_count=2, include_solid=False, palette_kind="broad"),
    ]
    for seed, overrides in enumerate(cases, start=11):
        grid = MOD.generate(seed, seed * 13, difficulty="hard", **overrides)
        observed = MOD.observe_overrides(grid)
        assert len(grid) == overrides["grid_h"]
        assert len(grid[0]) == overrides["grid_w"]
        for axis in ("group_count", "max_depth", "distractor_count", "include_solid"):
            assert observed[axis] == overrides[axis]
        assert MOD.self_check(grid) == []


def test_impossible_combinations_and_unknowns_reject_loudly():
    with pytest.raises(ValueError):
        MOD.generate(1, 2, grid_h=12, grid_w=12, group_count=3, max_depth=4)
    with pytest.raises(ValueError):
        MOD.generate(1, 2, texture="single_frame")
    with pytest.raises(ValueError):
        MOD.generate(1, 2, difficulty="extreme")


def test_self_check_rejects_targeted_semantic_impostors():
    grid = MOD.generate(
        17,
        29,
        grid_h=16,
        grid_w=16,
        group_count=1,
        max_depth=2,
        distractor_count=0,
        include_solid=False,
        palette_kind="broad",
    )
    components = MOD._components(grid)
    containers, roots, descendants = MOD._relations(components)
    root = next(i for i in roots if descendants[i])
    inner = descendants[root][0]

    only_outer = [[0 for _ in row] for row in grid]
    for r, c in components[root].cells:
        only_outer[r][c] = components[root].color
    assert MOD.self_check(only_outer)

    broken_outer = [row[:] for row in grid]
    r, c = components[root].cells[0]
    broken_outer[r][c] = 0
    assert MOD.self_check(broken_outer)

    same_color = [row[:] for row in grid]
    for r, c in components[inner].cells:
        same_color[r][c] = components[root].color
    assert any("no component would change" in e for e in MOD.self_check(same_color))

    crossing = [[0] * 12 for _ in range(12)]
    MOD.draw_frame(crossing, 1, 1, 7, 7, 1)
    MOD.draw_frame(crossing, 5, 5, 10, 10, 2)
    assert any("cross" in e for e in MOD.self_check(crossing))

    non_frame_container = [[0] * 12 for _ in range(12)]
    for r in range(1, 9):
        non_frame_container[r][4] = 1
    for c in range(1, 9):
        non_frame_container[4][c] = 1
    MOD.draw_frame(non_frame_container, 2, 2, 3, 3, 2)
    assert MOD.self_check(non_frame_container)


def test_default_distribution_is_deterministic_fresh_and_semantic():
    inputs = set()
    branch_counts = Counter()
    for band in ("easy", "medium", "hard"):
        for seed in range(200):
            sample_index = 1000 + seed * 19
            random.seed(911)
            state = random.getstate()
            first = MOD.generate(seed, sample_index, difficulty=band)
            assert random.getstate() == state
            second = MOD.generate(seed, sample_index, difficulty=band)
            assert first == second
            assert first is not second and first[0] is not second[0]
            assert MOD.self_check(first) == []
            observed = MOD.observe_overrides(first)
            branch_counts[("group_count", observed["group_count"])] += 1
            branch_counts[("max_depth", observed["max_depth"])] += 1
            branch_counts[("distractor_count", observed["distractor_count"])] += 1
            branch_counts[("include_solid", observed["include_solid"])] += 1
            output = MOD.rule_mirror(first)
            assert output != first
            inputs.add(tuple(map(tuple, first)))
    assert len(inputs) >= 590
    for value in (1, 2, 3):
        assert branch_counts[("group_count", value)] > 0
    for value in (2, 3, 4):
        assert branch_counts[("max_depth", value)] > 0
    for value in (0, 1, 2, 3):
        assert branch_counts[("distractor_count", value)] > 0
    assert branch_counts[("include_solid", False)] > 0
    assert branch_counts[("include_solid", True)] > 0
