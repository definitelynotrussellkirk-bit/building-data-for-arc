from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

gen = importlib.import_module("puzzle_generators.per_puzzle.64592477ccc8.generator")


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "64592477ccc8"


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _pairs(row):
    pairs = list(row["train"])
    test = row["test"]
    pairs.extend(test if isinstance(test, list) else [test])
    return pairs


def _mutations(grid):
    _, features, errors = gen._scene_analysis(grid)
    assert not errors
    first, second = features["boxes"][:2]

    missing_corner = copy.deepcopy(grid)
    missing_corner[first["r0"]][first["c0"]] = 0

    extra_interior = copy.deepcopy(grid)
    row = first["r0"] + 1 if first["height"] > 2 else first["r0"]
    col = first["c0"] + 1 if first["width"] > 2 else first["c0"]
    extra_interior[row][col] = first["color"]

    non_corner = copy.deepcopy(grid)
    non_corner[first["r0"]][first["c0"]] = 0
    replacement = (first["r0"], first["c0"] + 1)
    if replacement in {
        (first["r0"], first["c0"]),
        (first["r0"], first["c1"]),
        (first["r1"], first["c0"]),
        (first["r1"], first["c1"]),
    }:
        replacement = (first["r0"] + 1, first["c0"])
    non_corner[replacement[0]][replacement[1]] = first["color"]

    overlap = copy.deepcopy(grid)
    for row, col in (
        (second["r0"], second["c0"]),
        (second["r0"], second["c1"]),
        (second["r1"], second["c0"]),
        (second["r1"], second["c1"]),
    ):
        overlap[row][col] = 0
    c0 = first["c1"]
    c1 = min(len(grid[0]) - 1, c0 + 2)
    if c1 == c0:
        c0 -= 2
    r0 = first["r0"]
    r1 = min(len(grid) - 1, r0 + 2)
    if r1 == r0:
        r0 -= 2
    for row, col in ((r0, c0), (r0, c1), (r1, c0), (r1, c1)):
        overlap[row][col] = second["color"]

    return {
        "missing_corner": missing_corner,
        "extra_interior": extra_interior,
        "non_corner_marker": non_corner,
        "overlapping_outline": overlap,
    }


def test_canonical_inputs_are_accepted_and_mirror_all_outputs():
    for pair in _pairs(_canonical_row()):
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == [
            [int(value) for value in row] for row in pair["output"]
        ]


def test_schedule_witnesses_all_geometry_branches():
    scenes = [gen.generate(314159, index, difficulty="medium", n_colors=3) for index in range(4)]
    analyses = [gen._scene_analysis(scene)[1] for scene in scenes]
    assert analyses[0]["has_width_2"]
    assert analyses[1]["has_height_2"]
    assert analyses[2]["all_thick"]
    assert analyses[3]["has_width_2"] and analyses[3]["has_height_2"]
    assert all(gen.self_check(scene) == [] for scene in scenes)


def test_all_exact_override_boundaries_are_realized():
    for height in (7, 12):
        for width in (9, 14):
            for n_colors in (2, 3):
                grid = gen.generate(
                    11,
                    3,
                    difficulty="hard",
                    grid_h=height,
                    grid_w=width,
                    n_colors=n_colors,
                )
                assert gen.observe_overrides(grid) == {
                    "grid_h": height,
                    "grid_w": width,
                    "n_colors": n_colors,
                }


def test_self_check_rejects_four_targeted_impostors():
    grid = gen.generate(2718, 2, difficulty="medium", n_colors=2)
    mutations = _mutations(grid)
    assert set(mutations) == {
        "missing_corner",
        "extra_interior",
        "non_corner_marker",
        "overlapping_outline",
    }
    for name, mutated in mutations.items():
        assert gen.self_check(mutated), name


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(8675309)
    before = random.getstate()
    first = gen.generate(42, 1, difficulty="easy")
    after = random.getstate()
    second = gen.generate(42, 1, difficulty="easy")
    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))


def test_negative_recombination_is_rejected_by_teaching_distribution():
    grid = gen.generate(99, 0, difficulty="easy", n_colors=2)
    _, features, errors = gen._scene_analysis(grid)
    assert not errors
    first = features["boxes"][0]
    corrupted = copy.deepcopy(grid)
    corrupted[first["r0"]][first["c0"]] = 1
    assert 1 not in {box["color"] for box in features["boxes"]}
    assert gen.self_check(corrupted)
