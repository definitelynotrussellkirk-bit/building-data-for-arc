from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path


TASK_ID = "441d3a994cf6"
MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.441d3a994cf6.generator"
)
REPO = Path(__file__).resolve().parents[1]


def _canonical_inputs() -> list[list[list[int]]]:
    for line in (REPO / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return [pair["input"] for split in ("train", "test") for pair in row[split]]
    raise AssertionError("canonical task missing")


def _target_motifs(grid):
    return [
        cells
        for kind, cells in MODULE._analyze_grid(grid)["motifs"]
        if kind == MODULE._TARGET
    ]


def test_canonical_inputs_are_accepted() -> None:
    canonical = _canonical_inputs()
    assert len(canonical) == 4
    assert all(MODULE.self_check(grid) == [] for grid in canonical)


def test_sequential_episode_schedule_covers_all_counterexamples() -> None:
    seen = set()
    for sample_index in range(3):
        grid = MODULE.generate(17, sample_index, difficulty="medium")
        analysis = MODULE._analyze_grid(grid)
        assert MODULE.self_check(grid, difficulty="medium") == []
        seen.update(kind for kind, _ in analysis["motifs"] if kind != MODULE._TARGET)
    assert seen == {
        MODULE._HORIZONTAL,
        MODULE._MISMATCH,
        MODULE._LONG,
        MODULE._FILLED,
    }


def test_exact_overrides_are_observable_at_boundaries() -> None:
    for band in ("easy", "medium", "hard"):
        for h, w, gaps in ((8, 8, 1), (14, 14, 4)):
            grid = MODULE.generate(
                23,
                4,
                difficulty=band,
                grid_h=h,
                grid_w=w,
                gap_count=gaps,
            )
            assert (len(grid), len(grid[0])) == (h, w)
            assert MODULE.observe_overrides(grid)["gap_count"] == gaps
            assert MODULE.self_check(grid, meta={"gap_count": gaps}) == []


def test_determinism_fresh_returns_and_global_rng_preservation() -> None:
    random.seed(918273)
    before_state = random.getstate()
    first = MODULE.generate(101, 7, difficulty="hard")
    after_state = random.getstate()
    second = MODULE.generate(101, 7, difficulty="hard")
    assert after_state == before_state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert MODULE.generate(101, 7, difficulty="hard") == second


def test_self_check_rejects_targeted_impostors() -> None:
    grid = MODULE.generate(29, 2, difficulty="medium", grid_h=10, grid_w=10, gap_count=2)
    targets = _target_motifs(grid)
    assert len(targets) == 2

    drop_endpoint = copy.deepcopy(grid)
    r, c = targets[0][0]
    drop_endpoint[r][c] = 0

    novel_mismatch = copy.deepcopy(grid)
    used = {value for row in grid for value in row}
    novel = next(color for color in range(1, 10) if color not in used)
    r, c = targets[0][-1]
    novel_mismatch[r][c] = novel

    fill_every_target = copy.deepcopy(grid)
    for upper, lower in targets:
        r = (upper[0] + lower[0]) // 2
        c = upper[1]
        fill_every_target[r][c] = fill_every_target[upper[0]][c]

    transpose = [list(row) for row in zip(*grid)]

    solid_block = copy.deepcopy(grid)
    color = next(value for row in grid for value in row if value)
    for r in range(2):
        for c in range(2):
            solid_block[r][c] = color

    impostors = {
        "drop_endpoint": drop_endpoint,
        "novel_mismatch": novel_mismatch,
        "fill_every_target": fill_every_target,
        "transpose": transpose,
        "solid_block": solid_block,
    }
    for name, impostor in impostors.items():
        assert MODULE.self_check(impostor), name
