"""Focused semantic and regression tests for generator 3ae696dbdba9."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.check_generator_override_contract import _build_cases

TASK_ID = "3ae696dbdba9"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _pairs():
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_and_all_canonical_pairs():
    row = _canonical_row()
    digest = hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == digest == "116e45f72631"
    assert len(_pairs()) == 3
    for pair in _pairs():
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_default_schedule_axes_are_exact_and_band_live():
    for band in ("easy", "medium", "hard"):
        profiles = []
        for sample_index in range(15):
            grid = GEN.generate(31_337, sample_index, difficulty=band)
            profiles.append(GEN.schedule_profile(31_337, sample_index, band))
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) in (
                {"grid_h": 10, "grid_w": 15, "component_count": 3, "max_gap_columns": 2,
                 "gap_profile": "mixed", "control_mode": "one", "color_mode": "distinct",
                 "edge_profile": "interior"},
                {"grid_h": 12, "grid_w": 14, "component_count": 2, "max_gap_columns": 1,
                 "gap_profile": "short", "control_mode": "none", "color_mode": "reused",
                 "edge_profile": "interior"},
                {"grid_h": 10, "grid_w": 16, "component_count": 3, "max_gap_columns": 2,
                 "gap_profile": "mixed", "control_mode": "one", "color_mode": "distinct",
                 "edge_profile": "interior"},
                {"grid_h": 14, "grid_w": 17, "component_count": 4, "max_gap_columns": 2,
                 "gap_profile": "mixed", "control_mode": "one", "color_mode": "distinct",
                 "edge_profile": "interior"},
                {"grid_h": 14, "grid_w": 18, "component_count": 5, "max_gap_columns": 3,
                 "gap_profile": "long", "control_mode": "one", "color_mode": "reused",
                 "edge_profile": "touching"},
            )
        assert set(profiles) == set(GEN.SCHEDULE_PROFILES)
    assert GEN.schedule_profile(1, 0, "easy") != GEN.schedule_profile(1, 0, "medium")


def test_override_boundaries_are_exact_and_unknowns_fail_closed():
    cases = [
        {"grid_h": 10}, {"grid_h": 16}, {"grid_w": 12}, {"grid_w": 20},
        {"component_count": 2}, {"component_count": 5},
        {"max_gap_columns": 1}, {"max_gap_columns": 3},
        {"gap_profile": "short"}, {"gap_profile": "mixed"}, {"gap_profile": "long"},
        {"control_mode": "none"}, {"control_mode": "one"},
        {"color_mode": "distinct"}, {"color_mode": "reused"},
        {"edge_profile": "interior"}, {"edge_profile": "touching"},
    ]
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for case_index, overrides in enumerate(cases):
            grid = GEN.generate(50_000 + band_index * 100 + case_index, case_index,
                                difficulty=band, **overrides)
            observed = GEN.observe_overrides(grid)
            assert all(observed[key] == value for key, value in overrides.items())
            assert GEN.self_check(grid, meta={"overrides": overrides}) == []
    with pytest.raises(TypeError):
        GEN.generate(1, 0, nonexistent_axis="x")


def test_four_targeted_impostors_fail_closed_but_oracle_remains_broad():
    valid = GEN.generate(9_001, 3, difficulty="medium")
    impostors = {}
    impostors["all_background"] = [[0 for _ in row] for row in valid]
    impostors["already_closed"] = GEN.rule_mirror(valid)
    impostors["undersized"] = [[0] * 11 for _ in range(9)]

    touching = copy.deepcopy(valid)
    placed = False
    for r, row in enumerate(touching):
        for c, value in enumerate(row):
            if not value:
                continue
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < len(touching) and 0 <= nc < len(row) and touching[nr][nc] == 0:
                    touching[nr][nc] = 9 if value != 9 else 8
                    placed = True
                    break
            if placed:
                break
        if placed:
            break
    assert placed
    impostors["different_colors_touch"] = touching

    for name, grid in impostors.items():
        assert GEN.self_check(grid), name
        if grid and grid[0]:
            assert GEN.rule_mirror(grid)  # broad oracle execution is distinct from lesson validity


def test_repeated_color_components_refute_global_color_closure():
    grid = GEN.generate(77, 1, difficulty="easy")
    assert GEN.observe_overrides(grid)["color_mode"] == "reused"
    expected = GEN.rule_mirror(grid)
    rival = GEN.SEMANTIC_RIVALS["global_same_color_column_closure"](grid)
    assert rival != expected
    assert GEN.self_check(grid) == []


def test_every_sliding_lesson_window_is_identifiable():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(len(GEN.SCHEDULE_PROFILES)):
            pairs = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                index = start + offset
                grid = GEN.generate(80_000 + band_index * 100 + start, index, difficulty=band)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            assert GEN.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = GEN.generate(123_456, 19, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(123_456, 19, difficulty="hard")
    assert first == second and first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(123_456, 19, difficulty="hard") == second


def test_full_override_contract_matrix_is_exact_once_per_band():
    """Fast regression over the override checker's deterministic case matrix."""
    cases = _build_cases(GEN.AXES)
    assert len(cases) == 459
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for case_index, overrides in enumerate(cases):
            grid = GEN.generate(
                810_000 + band_index,
                case_index * 17 + 3,
                difficulty=band,
                **overrides,
            )
            observed = GEN.observe_overrides(grid)
            assert all(observed[name] == value for name, value in overrides.items())
            assert GEN.self_check(grid, meta={"overrides": overrides}) == []


def test_100_lessons_per_band_refute_every_declared_competitor_in_demos():
    """A rival must be contradicted by a visible demo, not only match the query."""
    cycle = len(GEN.SCHEDULE_PROFILES)
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for lesson_index in range(100):
            start = lesson_index % cycle
            seed = 910_000 + band_index * 100_000 + lesson_index
            demos = []
            for offset in range(GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(seed, start + offset, difficulty=band)
                demos.append(
                    {
                        "input": grid,
                        "output": GEN.rule_mirror(copy.deepcopy(grid)),
                    }
                )
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(
                    rival(copy.deepcopy(pair["input"])) != pair["output"]
                    for pair in demos
                ), (band, lesson_index, name)
