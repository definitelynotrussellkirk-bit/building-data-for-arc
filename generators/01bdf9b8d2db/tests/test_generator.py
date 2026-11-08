"""Focused contract and semantic regression tests for 01bdf9b8d2db."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "review_generator_01bdf9b8d2db", HOME / "generator.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _norm_grid(value):
    return [[int(cell) for cell in row] if isinstance(row, str) else list(row)
            for row in value]


def _canonical_pairs():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    pairs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") != gen.TASK_ID:
            continue
        train = row.get("train") or []
        test = row.get("test") or []
        if isinstance(test, dict):
            test = [test]
        for pair in [*train, *test]:
            pairs.append({
                "input": _norm_grid(pair["input"]),
                "output": _norm_grid(pair["output"]),
            })
    return pairs


def _regions(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    regions = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            cells = []
            while todo:
                cr, cc = todo.pop()
                cells.append((cr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            grid[nr][nc] != 5 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            regions.append(cells)
    return regions


def _reference_output(grid):
    out = [[5 if value == 5 else 0 for value in row] for row in grid]
    for cells in _regions(grid):
        markers = [grid[r][c] for r, c in cells if grid[r][c] not in (0, 5)]
        assert len(markers) == 1
        for r, c in cells:
            out[r][c] = markers[0]
    return out


def _profile(grid):
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def test_authority_pin_and_all_canonical_pairs():
    assert gen.RULE_HASH == "816bf3c1378a"
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert _reference_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_realized_and_observable(difficulty):
    cases = (
        dict(grid_h=7, grid_w=10, n_vdivs=1, n_hdivs=0, n_gaps=0),
        dict(grid_h=10, grid_w=13, n_vdivs=3, n_hdivs=2, n_gaps=2),
        dict(grid_h=8, grid_w=12, n_vdivs=2, n_hdivs=1, n_gaps=1),
    )
    for index, requested in enumerate(cases):
        grid = gen.generate(110 + index, 7 + index, difficulty=difficulty, **requested)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == requested
        assert len(grid) == requested["grid_h"]
        assert len(grid[0]) == requested["grid_w"]


@pytest.mark.parametrize("key,value", [
    ("typo_axis", 1),
    ("grid_h", 6), ("grid_h", 11),
    ("grid_w", 9), ("grid_w", 14),
    ("n_vdivs", 0), ("n_vdivs", 4),
    ("n_hdivs", -1), ("n_hdivs", 3),
    ("n_gaps", -1), ("n_gaps", 3),
    ("grid_h", True), ("n_gaps", 1.0), ("grid_w", "10"),
])
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_defaults_are_deterministic_lawful_and_do_not_touch_global_rng(difficulty):
    random.seed(8675309)
    before = random.getstate()
    for index in range(40):
        first = gen.generate(700 + index, index, difficulty=difficulty)
        second = gen.generate(700 + index, index, difficulty=difficulty)
        assert first == second
        assert first is not second
        assert all(a is not b for a, b in zip(first, second))
        assert gen.self_check(first) == []
        for region in _regions(first):
            markers = [first[r][c] for r, c in region if first[r][c] not in (0, 5)]
            assert len(markers) == 1
    assert random.getstate() == before


def test_gap_schedule_makes_every_three_demo_lesson_refute_rectangle_fill():
    assert set(gen.SCHEDULE_PROFILES) == {"plain", "gapped"}
    for start in range(30):
        grids = [gen.generate(991, start + offset, difficulty="hard") for offset in range(3)]
        assert {gen.schedule_profile(991, start + offset, "hard") for offset in range(3)} == {
            "plain", "gapped"
        }
        decisive = [grid for grid in grids if gen.SEMANTIC_WITNESSES[
            "divider_gap_requires_connectivity"
        ](grid)]
        assert decisive
        assert any(
            gen.SEMANTIC_RIVALS["independent_rectangles"](grid) != _reference_output(grid)
            for grid in decisive
        )
        demos = [{"input": grid, "output": _reference_output(grid)} for grid in grids]
        query_grid = gen.generate(991, start + 3, difficulty="hard")
        assert gen.lesson_identifiable(
            demos, {"input": query_grid, "output": _reference_output(query_grid)}
        ) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_each_band_has_dense_exact_canonical_profile_support(difficulty):
    canonical_profiles = {_profile(pair["input"]) for pair in _canonical_pairs()}
    draws = [gen.generate(1200 + i, i * 7 + 2, difficulty=difficulty) for i in range(90)]
    exact = sum(_profile(grid) in canonical_profiles for grid in draws)
    assert exact >= 45


def test_nine_chamber_profile_repeats_marker_colors_like_canonical_test():
    found = None
    for index in range(300):
        grid = gen.generate(2300 + index, index, difficulty="hard")
        observed = gen.observe_overrides(grid)
        if observed == {
            "grid_h": 9, "grid_w": 13, "n_vdivs": 2,
            "n_hdivs": 2, "n_gaps": 0,
        }:
            found = grid
            break
    assert found is not None
    markers = [found[r][c] for region in _regions(found) for r, c in region
               if found[r][c] not in (0, 5)]
    assert len(markers) == 9
    assert len(set(markers)) == 7
    assert _profile(found) == (9, 13, 9)


@pytest.mark.parametrize("n_gaps", [0, 1, 2])
def test_requested_gap_count_is_exact(n_gaps):
    grid = gen.generate(
        808, 4, grid_h=7, grid_w=10, n_vdivs=3, n_hdivs=2, n_gaps=n_gaps
    )
    assert gen.observe_overrides(grid)["n_gaps"] == n_gaps
    assert gen.self_check(grid) == []


def test_validator_rejects_missing_and_conflicting_markers():
    grid = gen.generate(440, 2, grid_h=9, grid_w=13, n_vdivs=2, n_hdivs=2, n_gaps=0)
    regions = _regions(grid)

    missing = copy.deepcopy(grid)
    marker = next((r, c) for r, c in regions[0] if missing[r][c] not in (0, 5))
    missing[marker[0]][marker[1]] = 0
    assert any("exactly one marker" in reason for reason in gen.self_check(missing))

    conflicting = copy.deepcopy(grid)
    target = next((r, c) for r, c in regions[1] if conflicting[r][c] == 0)
    conflicting[target[0]][target[1]] = 9
    assert any("exactly one marker" in reason for reason in gen.self_check(conflicting))
