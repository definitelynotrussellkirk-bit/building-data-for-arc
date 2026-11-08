"""Focused regression tests for generator 34700cab1c3c."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT / "puzzle_generators" / "per_puzzle" / "34700cab1c3c" / "generator.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_34700cab1c3c", GENERATOR_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_inputs():
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != "34700cab1c3c":
                continue
            tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [pair["input"] for pair in [*row["train"], *tests]]
    raise AssertionError("canonical task 34700cab1c3c is missing")


def paint(grid, shape, top, left, color):
    for r, c in shape:
        grid[top + r][left + c] = color


def blank(h=8, w=10):
    return [[0 for _ in range(w)] for _ in range(h)]


def test_rule_hash_and_every_canonical_input_is_owned():
    generator = load_generator()
    assert generator.RULE_HASH == "1259a82b7164"
    inputs = canonical_inputs()
    assert len(inputs) == 3
    for grid in inputs:
        assert generator.self_check(grid) == []
        assert generator.strict_canonical_like(grid) == []


def test_override_boundaries_are_exact_and_observable_in_every_band():
    generator = load_generator()
    cases = (
        {"grid_h": 8, "grid_w": 10, "n_blobs": 2},
        {"grid_h": 10, "grid_w": 12, "n_blobs": 3},
    )
    for band in ("easy", "medium", "hard"):
        for case in cases:
            grid = generator.generate(1701, 29, difficulty=band, **case)
            observed = generator.observe_overrides(grid)
            assert {key: observed[key] for key in case} == case
            assert generator.self_check(grid, difficulty=band) == []


def test_three_demo_schedule_refutes_named_rivals_and_identifies_query():
    generator = load_generator()
    demos = []
    for sample_index in range(3):
        grid = generator.generate(998877, sample_index)
        demos.append({
            "input": grid,
            "output": generator._local_output(grid, "transpose"),
        })
    query_grid = generator.generate(998877, 3)
    query = {
        "input": query_grid,
        "output": generator._local_output(query_grid, "transpose"),
    }
    assert generator.lesson_identifiable(demos, query) == []
    assert any(generator._has_square_asymmetric(pair["input"]) for pair in demos)
    for name, competitor in generator._LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        assert not survives or competitor(query["input"]) == query["output"], name


def test_self_check_rejects_five_targeted_impostors():
    generator = load_generator()
    wide = ((0, 0), (0, 1), (0, 2), (1, 0))
    tall = ((0, 0), (0, 1), (1, 0), (2, 0))

    symmetric = blank()
    paint(symmetric, ((0, 0), (0, 1), (1, 0), (1, 1)), 1, 1, 2)
    paint(symmetric, ((0, 0), (0, 1), (1, 0), (1, 1)), 4, 6, 3)

    split_color = blank()
    paint(split_color, wide, 0, 0, 2)
    paint(split_color, tall, 5, 0, 2)
    paint(split_color, wide, 0, 6, 3)

    colliding_outputs = blank()
    paint(colliding_outputs, wide, 0, 0, 2)
    paint(colliding_outputs, tall, 2, 0, 3)

    out_of_bounds = blank()
    paint(out_of_bounds, tall, 0, 8, 2)
    paint(out_of_bounds, wide, 5, 0, 3)

    wrong_size = blank()
    paint(wrong_size, ((0, 0), (1, 0), (1, 1)), 0, 0, 2)
    paint(wrong_size, wide, 4, 5, 3)

    impostors = {
        "transpose_symmetric": symmetric,
        "one_color_split_across_objects": split_color,
        "transposed_footprints_collide": colliding_outputs,
        "transposed_footprint_out_of_bounds": out_of_bounds,
        "three_cell_object": wrong_size,
    }
    for name, grid in impostors.items():
        assert generator.self_check(grid), name


def test_negative_recombination_is_rejected_but_valid_part_remains_present():
    generator = load_generator()
    grid = generator.generate(481516, 23, grid_h=8, grid_w=10, n_blobs=2)
    comps = generator._components(grid)
    assert len(comps) == 2
    mutated = copy.deepcopy(grid)
    victim = comps[0]
    for r, c in victim["cells"]:
        mutated[r][c] = 0
    r1, c1, _, _ = victim["bbox"]
    square = ((0, 0), (0, 1), (1, 0), (1, 1))
    for r, c in square:
        mutated[r1 + r][c1 + c] = victim["color"]
    assert generator.self_check(mutated)
    remaining_colors = {value for row in mutated for value in row if value != 0}
    assert len(remaining_colors) == 2


def test_replay_is_deterministic_fresh_and_process_rng_pure():
    generator = load_generator()
    random.seed(20260725)
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


def test_disjoint_seed_stability_and_semantic_branch_support():
    generator = load_generator()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [
            generator.generate(100000 + band_index * 10000 + i, i, difficulty=band)
            for i in range(200)
        ]
        strict = sum(not generator.strict_canonical_like(grid) for grid in grids)
        # strict_canonical_like returns [] on hit, so count the inverse explicitly.
        strict_hits = len(grids) - strict
        assert strict_hits >= 10, (band, strict_hits)
        for name, witness in generator.SEMANTIC_WITNESSES.items():
            hits = sum(bool(witness(grid)) for grid in grids)
            assert hits > 0, (band, name)
        signatures = {
            tuple(tuple(row) for row in grid)
            for grid in grids
        }
        assert len(signatures) >= 190, (band, len(signatures))
