from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

generator = importlib.import_module("puzzle_generators.per_puzzle.324e3e599c28.generator")


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "324e3e599c28"
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"
BASE = (
    ROOT
    / "data/base/solutions/banks/bfb58307fa26"
    / "M35__324e3e599c28.json"
)


def _canonical_row() -> dict:
    for line in CANONICAL.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def _all_pairs() -> list[dict]:
    row = _canonical_row()
    return list(row["train"]) + list(row["test"])


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _mirror(grid):
    out = copy.deepcopy(grid)
    anchors = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    ]
    if len(anchors) != 1:
        return out
    ar, ac = anchors[0]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            rr, cc = 2 * ar - r, 2 * ac - c
            if (
                value not in (0, 9)
                and 0 <= rr < len(grid)
                and 0 <= cc < len(grid[0])
                and out[rr][cc] == 0
            ):
                out[rr][cc] = value
    return out


def test_rule_hash_and_selected_task_rule_are_synchronized():
    row = _canonical_row()
    digest = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    base = json.loads(BASE.read_text())

    assert digest == generator.RULE_HASH == "040d2eefe2c6"
    assert base["racket_target"]["target_code"] == row["program_solution"]


def test_all_canonical_pairs_pass_structural_check_and_independent_mirror():
    for pair in _all_pairs():
        grid = copy.deepcopy(pair["input"])
        before = copy.deepcopy(grid)
        assert generator.self_check(grid) == []
        assert _mirror(grid) == pair["output"]
        assert grid == before


def test_exact_override_boundaries_are_observable():
    cases = [
        dict(grid_h=9, grid_w=9, n_cells=3, n_colors=1, primary_color=1),
        dict(grid_h=12, grid_w=12, n_cells=4, n_colors=2, primary_color=8),
    ]
    for index, overrides in enumerate(cases):
        grid = generator.generate(
            100 + index,
            index,
            difficulty=("easy", "hard")[index],
            **overrides,
        )
        assert (len(grid), len(grid[0])) == (
            overrides["grid_h"],
            overrides["grid_w"],
        )
        observed = generator.observe_overrides(grid)
        assert observed == {
            "n_cells": overrides["n_cells"],
            "n_colors": overrides["n_colors"],
            "primary_color": overrides["primary_color"],
        }
        assert generator.self_check(grid) == []


def test_sample_index_schedule_covers_all_semantic_layouts_per_lesson():
    layouts = [
        generator._classify_layout(generator.generate(77, index))
        for index in range(3)
    ]
    assert layouts == ["diagonal", "horizontal", "vertical"]


def test_deterministic_replay_is_fresh_and_global_rng_pure():
    random.seed(271828)
    state = random.getstate()
    first = generator.generate(17, 29, difficulty="hard")
    assert random.getstate() == state
    second = generator.generate(17, 29, difficulty="hard")
    assert random.getstate() == state

    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert generator.generate(17, 29, difficulty="hard") == second


def test_self_check_rejects_targeted_semantic_impostors():
    base = generator.generate(
        101,
        0,
        grid_h=11,
        grid_w=11,
        n_cells=4,
        n_colors=2,
        primary_color=3,
    )
    anchors = generator._anchor_cells(base)
    cells = sorted(generator._blob_cells(base))
    ar, ac = anchors[0]

    impostors = {}

    grid = copy.deepcopy(base)
    grid[ar][ac] = 0
    impostors["missing anchor"] = grid

    grid = copy.deepcopy(base)
    grid[0][0] = 9
    impostors["multiple anchors"] = grid

    grid = copy.deepcopy(base)
    r, c = cells[-1]
    grid[r][c] = 0
    grid[0][0] = 4
    impostors["disconnected source"] = grid

    grid = copy.deepcopy(base)
    grid[ar][ac] = 0
    grid[1][1] = 9
    impostors["out-of-bounds reflection"] = grid

    grid = copy.deepcopy(base)
    r, c = cells[0]
    rr, cc = 2 * ar - r, 2 * ac - c
    grid[rr][cc] = grid[r][c]
    impostors["pre-filled reflected target"] = grid

    grid = copy.deepcopy(base)
    for r, c in cells[2:]:
        grid[r][c] = 0
    impostors["too-small source"] = grid

    failures = {
        name: generator.self_check(grid) for name, grid in impostors.items()
    }
    assert all(errors for errors in failures.values()), failures
    assert len(failures) >= 4


def test_semantic_census_covers_layouts_anchor_offsets_colors_and_sizes():
    layouts = set()
    anchor_offsets = set()
    sizes = set()
    color_counts = set()
    primary_colors = set()
    inputs = set()
    outputs = set()

    for band in ("easy", "medium", "hard"):
        for seed in range(500, 560):
            sample_index = seed - 500
            grid = generator.generate(seed, sample_index, difficulty=band)
            assert generator.self_check(grid, difficulty=band) == []
            ar, ac = generator._anchor_cells(grid)[0]
            layouts.add(generator._classify_layout(grid))
            anchor_offsets.add((ar - len(grid) // 2, ac - len(grid[0]) // 2))
            observed = generator.observe_overrides(grid)
            sizes.add(observed["n_cells"])
            color_counts.add(observed["n_colors"])
            primary_colors.add(observed["primary_color"])
            inputs.add(_frozen(grid))
            outputs.add(_frozen(_mirror(grid)))

    assert layouts == {"diagonal", "horizontal", "vertical"}
    assert (0, 0) in anchor_offsets
    assert any(offset != (0, 0) for offset in anchor_offsets)
    assert sizes == {3, 4}
    assert color_counts == {1, 2}
    assert primary_colors == set(range(1, 9))
    assert len(inputs) >= 170
    assert len(outputs) >= 170
