from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


TASK_ID = "89c85768abe1"
REPO_ROOT = Path(__file__).resolve().parents[3]
GENERATOR_PATH = REPO_ROOT / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
sys.path.insert(0, str(REPO_ROOT / "shared" / "runtime"))


def load_generator():
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    with CANONICAL_PATH.open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [*row["train"], *tests]
    raise AssertionError(f"canonical task {TASK_ID} is missing")


def signature(grid):
    return tuple(tuple(row) for row in grid)


def color_positions(grid):
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((r, c))
    return positions


def test_rule_pin_and_every_canonical_pair_is_owned():
    generator = load_generator()
    assert generator.RULE_HASH == "d273f364d771"
    assert generator.VERSION == "2.1.0"
    assert set(generator.AXES) == {"grid_h", "grid_w", "rectangles"}

    pairs = canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        assert generator.self_check(pair["input"]) == []
        assert generator.strict_canonical_like(pair["input"]) == []
        assert generator.rule_mirror(pair["input"]) == pair["output"]


def test_exact_overrides_are_total_observable_and_unknown_controls_fail():
    generator = load_generator()
    cases = ((7, 9, 2), (14, 16, 4), (7, 16, 3), (14, 9, 4))
    for band in ("easy", "medium", "hard"):
        for sample_index, (height, width, rectangles) in enumerate(cases):
            grid = generator.generate(
                20261003,
                sample_index,
                difficulty=band,
                grid_h=height,
                grid_w=width,
                rectangles=rectangles,
            )
            assert generator.self_check(grid, difficulty=band) == []
            assert generator.observe_overrides(grid) == {
                "grid_h": height,
                "grid_w": width,
                "rectangles": rectangles,
            }

    with pytest.raises((TypeError, ValueError), match="unknown override"):
        generator.generate(1, 0, mystery_axis=7)
    with pytest.raises((TypeError, ValueError), match="grid_h"):
        generator.generate(1, 0, grid_h=True)
    with pytest.raises((TypeError, ValueError), match="grid_h"):
        generator.generate(1, 0, grid_h=6)
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        generator.generate(1, 0, difficulty="impossible")


def test_default_schedule_hits_canonical_profiles_and_both_orientations_in_every_band():
    generator = load_generator()
    assert generator.EXAMPLES_NEEDED == 2
    assert tuple(generator.SCHEDULE_PROFILES) == (
        "canonical_anchor",
        "anti_diagonal_counterexample",
    )
    expected_anchor = {
        "easy": (8, 10, 2),
        "medium": (9, 11, 2),
        "hard": (10, 10, 2),
    }

    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [
            generator.generate(700000 + band_index * 10000 + i, i, difficulty=band)
            for i in range(40)
        ]
        assert all(generator.self_check(grid, difficulty=band) == [] for grid in grids)
        assert all(generator.strict_canonical_like(grid) == [] for grid in grids)
        assert any(
            generator.observe_overrides(grid)
            == {
                "grid_h": expected_anchor[band][0],
                "grid_w": expected_anchor[band][1],
                "rectangles": expected_anchor[band][2],
            }
            for grid in grids
        )
        assert any(generator.SEMANTIC_WITNESSES["anti_diagonal_pair"](grid) for grid in grids)
        assert any(not generator.SEMANTIC_WITNESSES["anti_diagonal_pair"](grid) for grid in grids)
        assert len({signature(grid) for grid in grids}) >= 38


def test_main_diagonal_shortcut_fits_canonical_but_generated_counterexamples_refute_it():
    generator = load_generator()
    assert set(generator.CANONICAL_SHORTCUTS) == {
        "main_diagonal_only",
        "homogeneous_orientation_only",
    }
    shortcut = generator.CANONICAL_SHORTCUTS["main_diagonal_only"]
    for pair in canonical_pairs():
        assert shortcut(pair["input"]) == pair["output"]

    for band in ("easy", "medium", "hard"):
        counterexamples = [
            generator.generate(424242, index, difficulty=band)
            for index in range(1, 12, 2)
        ]
        assert counterexamples
        for grid in counterexamples:
            assert generator.schedule_profile(424242, 1, band) == "anti_diagonal_counterexample"
            assert generator.SEMANTIC_WITNESSES["anti_diagonal_pair"](grid)
            assert shortcut(grid) != generator.rule_mirror(grid)


def test_every_two_demo_window_is_identifiable_against_named_competitors():
    generator = load_generator()
    assert set(generator.LESSON_COMPETITORS) == {
        "main_diagonal_only",
        "homogeneous_orientation_only",
    }
    for band in ("easy", "medium", "hard"):
        for start in range(18):
            demos = []
            for sample_index in range(start, start + generator.EXAMPLES_NEEDED):
                grid = generator.generate(998877, sample_index, difficulty=band)
                demos.append({"input": grid, "output": generator.rule_mirror(grid)})
            query_grid = generator.generate(
                998877, start + generator.EXAMPLES_NEEDED, difficulty=band
            )
            query = {"input": query_grid, "output": generator.rule_mirror(query_grid)}
            assert generator.lesson_identifiable(demos, query) == []
            for name, competitor in generator.LESSON_COMPETITORS.items():
                assert not all(
                    competitor(pair["input"]) == pair["output"] for pair in demos
                ), (band, start, name)


def test_self_check_rejects_blank_singleton_collinear_overlap_and_ragged_impostors():
    generator = load_generator()

    blank = [[0] * 9 for _ in range(7)]
    singleton = copy.deepcopy(blank)
    singleton[1][1] = 2
    singleton[4][4] = 3
    collinear = copy.deepcopy(blank)
    collinear[1][1] = collinear[1][5] = 2
    collinear[4][2] = collinear[6][7] = 3
    overlap = copy.deepcopy(blank)
    overlap[1][1] = overlap[4][5] = 2
    overlap[2][2] = overlap[5][6] = 3
    ragged = [[0, 2, 0], [0, 0], [0, 2, 0]]

    for name, grid in (
        ("blank", blank),
        ("singleton", singleton),
        ("collinear", collinear),
        ("overlap", overlap),
        ("ragged", ragged),
    ):
        assert generator.self_check(grid), name

    fixtures = dict(generator.mutation_fixtures())
    assert {"blank", "singletons", "collinear_pair", "overlapping_rectangles", "ragged"} <= set(fixtures)
    assert all(generator.self_check(grid) for grid in fixtures.values())


def test_generated_rectangles_are_non_degenerate_and_pairwise_disjoint():
    generator = load_generator()
    for band in ("easy", "medium", "hard"):
        for sample_index in range(80):
            grid = generator.generate(3133700 + sample_index, sample_index, difficulty=band)
            boxes = []
            for color, cells in color_positions(grid).items():
                assert len(cells) == 2, (band, sample_index, color, cells)
                (r1, c1), (r2, c2) = cells
                assert r1 != r2 and c1 != c2
                box = {
                    (r, c)
                    for r in range(min(r1, r2), max(r1, r2) + 1)
                    for c in range(min(c1, c2), max(c1, c2) + 1)
                }
                assert all(not (box & previous) for previous in boxes)
                boxes.append(box)


def test_replay_is_deterministic_fresh_and_process_rng_pure():
    generator = load_generator()
    random.seed(20261003)
    before = random.getstate()
    first = generator.generate(777, 19, difficulty="hard")
    after = random.getstate()
    second = generator.generate(777, 19, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert generator.generate(777, 19, difficulty="hard") == second


def test_mixed_orientation_counterexamples_refute_homogeneous_orientation_shortcut():
    generator = load_generator()
    assert "homogeneous_orientation_only" in generator.CANONICAL_SHORTCUTS
    shortcut = generator.CANONICAL_SHORTCUTS["homogeneous_orientation_only"]
    for pair in canonical_pairs():
        assert shortcut(pair["input"]) == pair["output"]

    for band in ("easy", "medium", "hard"):
        for sample_index in range(1, 12, 2):
            grid = generator.generate(606060, sample_index, difficulty=band)
            profile = generator.semantic_profile(grid)
            assert profile["main_diagonal_pairs"] > 0, (band, sample_index, profile)
            assert profile["anti_diagonal_pairs"] > 0, (band, sample_index, profile)
            assert generator.SEMANTIC_WITNESSES["mixed_pair_orientations"](grid)
            assert shortcut(grid) != generator.rule_mirror(grid)
