"""Regression tests for the first-dihedral-match generator repair."""

from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT
    / "puzzle_generators"
    / "per_puzzle"
    / "4a3e2293a089"
    / "generator.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_4a3e2293a089", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == "4a3e2293a089":
                return [*row["train"], *row["test"]]
    raise AssertionError("canonical task 4a3e2293a089 is missing")


def clone(grid):
    return [row[:] for row in grid]


def test_canonical_ties_are_accepted_and_python_mirror_matches_all_outputs():
    generator = load_generator()
    pairs = canonical_pairs()

    assert [len(generator._analyze(pair["input"])["matches"]) for pair in pairs] == [
        2,
        2,
        1,
        2,
    ]
    for pair in pairs:
        assert generator.self_check(pair["input"]) == []
        assert generator.strict_canonical_like(pair["input"]) == []
        assert generator._rule_mirror(pair["input"]) == pair["output"]


def test_four_sample_schedule_covers_the_answer_bearing_branches():
    generator = load_generator()
    observed = [
        generator.observe_overrides(generator.generate(123, index, difficulty="medium"))
        for index in range(4)
    ]
    assert observed == [
        {
            "guide_cells": 4,
            "n_matches": 1,
            "selected_rank": 0,
            "match_orientation": "different",
        },
        {
            "guide_cells": 5,
            "n_matches": 2,
            "selected_rank": 0,
            "match_orientation": "same",
        },
        {
            "guide_cells": 6,
            "n_matches": 1,
            "selected_rank": 1,
            "match_orientation": "different",
        },
        {
            "guide_cells": 5,
            "n_matches": 2,
            "selected_rank": 1,
            "match_orientation": "different",
        },
    ]

    episodes = []
    for index in range(5):
        grid = generator.generate(123, index, difficulty="medium")
        episodes.append({"input": grid, "output": generator._rule_mirror(grid)})
    assert generator.lesson_identifiable(episodes[:4], episodes[4]) == []


def test_exact_override_boundaries_are_observable_in_every_band():
    generator = load_generator()
    for band in ("easy", "medium", "hard"):
        grid = generator.generate(
            91,
            37,
            difficulty=band,
            grid_h=10,
            grid_w=16,
            guide_cells=6,
            n_matches=2,
            selected_rank=1,
            match_orientation="different",
        )
        assert (len(grid), len(grid[0])) == (10, 16)
        assert generator.observe_overrides(grid) == {
            "guide_cells": 6,
            "n_matches": 2,
            "selected_rank": 1,
            "match_orientation": "different",
        }
        assert generator.self_check(grid) == []


def test_structural_checker_rejects_targeted_impostors():
    generator = load_generator()

    valid_unique = generator.generate(71, 0, difficulty="hard")
    analysis = generator._analyze(valid_unique)
    guide = analysis["guide"]
    selected = analysis["candidates"][analysis["matches"][0]]

    no_guide = [[0 if value == 1 else value for value in row] for row in valid_unique]
    assert generator.self_check(no_guide)

    no_match = clone(valid_unique)
    for r, c in selected["cells"]:
        no_match[r][c] = 0
    replacement = next(
        shape
        for shape in generator._shape_classes(guide["size"])
        if generator._orbit_key(shape) != generator._orbit_key(guide["norm"])
    )
    r0, c0, _, _ = selected["bbox"]
    for r, c in replacement:
        no_match[r0 + r][c0 + c] = selected["color"]
    assert generator.self_check(no_match)

    tied = generator.generate(72, 1, difficulty="hard")
    tied_analysis = generator._analyze(tied)
    nonmatch_rank = next(
        rank for rank in range(3) if rank not in set(tied_analysis["matches"])
    )
    nonmatch = tied_analysis["candidates"][nonmatch_rank]
    three_matches = clone(tied)
    for r, c in nonmatch["cells"]:
        three_matches[r][c] = 0
    r0, c0, _, _ = nonmatch["bbox"]
    for r, c in tied_analysis["guide"]["norm"]:
        three_matches[r0 + r][c0 + c] = nonmatch["color"]
    assert generator.self_check(three_matches)

    touching = clone(valid_unique)
    gr, gc = guide["cells"][0]
    candidate_color = analysis["candidates"][0]["color"]
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = gr + dr, gc + dc
        if 0 <= nr < len(touching) and 0 <= nc < len(touching[0]) and touching[nr][nc] == 0:
            touching[nr][nc] = candidate_color
            break
    assert generator.self_check(touching)

    duplicate_color = clone(valid_unique)
    first, second = analysis["candidates"][:2]
    for r, c in second["cells"]:
        duplicate_color[r][c] = first["color"]
    assert generator.self_check(duplicate_color)


def test_replay_freshness_and_process_global_rng_purity():
    generator = load_generator()
    random.seed(8675309)
    before = random.getstate()
    first = generator.generate(77, 3, difficulty="medium")
    after = random.getstate()
    second = generator.generate(77, 3, difficulty="medium")

    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
