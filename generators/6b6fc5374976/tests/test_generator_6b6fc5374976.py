from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.coder_synth_verify import ProgramVerifier


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "6b6fc5374976"
GENERATOR = importlib.import_module(
    "puzzle_generators.per_puzzle.6b6fc5374976.generator"
)
CANONICAL = ROOT / "data" / "canonical" / "puzzles.jsonl"
BASE = (
    ROOT
    / "data"
    / "base"
    / "solutions"
    / "banks"
    / "ce088a50599a"
    / "H158__6b6fc5374976.json"
)


def canonical_row():
    for line in CANONICAL.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def canonical_pairs():
    row = canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *tests]


def normalized(cells):
    cells = tuple(cells)
    top = min(row for row, _col in cells)
    left = min(col for _row, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def quarter_turn(cells):
    cells = normalized(cells)
    height = max(row for row, _col in cells) + 1
    return normalized((col, height - 1 - row) for row, col in cells)


def independent_rule(grid):
    height, width = len(grid), len(grid[0])
    positions = {
        color: [
            (row, col)
            for row in range(height)
            for col in range(width)
            if grid[row][col] == color
        ]
        for color in range(10)
    }
    control = next(color for color in (2, 3, 4, 6) if positions[color])
    shape = normalized(positions[1])
    for _ in range({2: 0, 3: 1, 4: 2, 6: 3}[control]):
        shape = quarter_turn(shape)
    marker7, marker8 = positions[7][0], positions[8][0]
    delta = (marker8[0] - marker7[0], marker8[1] - marker7[1])
    output = [[0] * width for _ in range(height)]
    top, left = marker8
    while True:
        placed = [(top + row, left + col) for row, col in shape]
        if not all(0 <= row < height and 0 <= col < width for row, col in placed):
            return output
        if any(grid[row][col] == 5 for row, col in placed):
            return output
        for row, col in placed:
            output[row][col] = 9
        top += delta[0]
        left += delta[1]


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def first_zero(grid, forbidden=()):
    blocked = set(forbidden)
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == 0 and (row, col) not in blocked:
                return row, col
    raise AssertionError("no free zero cell")


def test_rule_sources_are_exactly_synchronized_and_hash_pinned():
    row = canonical_row()
    base = json.loads(BASE.read_text(encoding="utf-8"))
    assert GENERATOR.RULE_HASH == "27a417d278bf"
    assert base["racket_target"]["raw_code"] == row["program_solution"]
    assert base["racket_target"]["target_code"] == row["program_solution"]


def test_all_canonical_pairs_match_with_input_purity_and_a_b_a():
    row = canonical_row()
    pairs = canonical_pairs()
    assert len(pairs) == 5
    inputs = [copy.deepcopy(pair["input"]) for pair in pairs]
    expected = [pair["output"] for pair in pairs]
    for grid, output in zip(inputs, expected):
        snapshot = copy.deepcopy(grid)
        assert GENERATOR.self_check(grid, meta={"canonical": True}) == []
        assert GENERATOR.canonical_like(grid)
        assert independent_rule(grid) == output
        assert grid == snapshot

    with ProgramVerifier(timeout=30) as verifier:
        actual = [verifier.apply(row["program_solution"], grid) for grid in inputs]
        a1 = verifier.apply(row["program_solution"], inputs[0])
        b = verifier.apply(row["program_solution"], inputs[1])
        a2 = verifier.apply(row["program_solution"], inputs[0])
    assert actual == expected
    assert a1 == expected[0]
    assert b == expected[1]
    assert a2 == a1
    assert inputs == [pair["input"] for pair in pairs]


def test_override_boundaries_are_exact_and_observable():
    cases = [
        {
            "grid_h": height,
            "grid_w": width,
            "rotation_control": control,
            "copy_count": copies,
            "template_cells": template_cells,
            "vector_family": family,
            "stop_mode": stop,
        }
        for height in (11, 20)
        for width in (13, 22)
        for control in (2, 6)
        for copies in (2, 6)
        for template_cells in (4, 7)
        for family in GENERATOR.VECTOR_FAMILIES
        for stop in GENERATOR.STOP_MODES
    ]
    accepted = 0
    rejected = 0
    for index, case in enumerate(cases):
        try:
            grid = GENERATOR.generate(7000 + index, 31, difficulty="hard", **case)
        except ValueError as exc:
            assert "infeasible override combination" in str(exc)
            rejected += 1
            continue
        accepted += 1
        assert GENERATOR.self_check(grid, difficulty="hard", meta={"overrides": case}) == []
        assert GENERATOR.observe_overrides(grid) == case
        assert independent_rule(grid)
    assert accepted >= 100
    assert accepted + rejected == len(cases)
    with pytest.raises(TypeError):
        GENERATOR.generate(1, 1, nonexistent_axis=True)


def test_sample_schedule_exercises_every_rotation_in_each_lesson():
    for band in ("easy", "medium", "hard"):
        for block in range(30):
            controls = [
                GENERATOR.observe_overrides(
                    GENERATOR.generate(9000 + block, block * 4 + offset, difficulty=band)
                )["rotation_control"]
                for offset in range(4)
            ]
            assert controls == [2, 3, 4, 6]


def test_structural_self_check_rejects_targeted_impostors():
    grid = GENERATOR.generate(
        12345,
        7,
        difficulty="hard",
        rotation_control=6,
        copy_count=4,
        template_cells=6,
        vector_family="diagonal",
        stop_mode="wall",
    )
    assert GENERATOR.self_check(grid) == []

    missing_marker = copy.deepcopy(grid)
    marker8 = next(
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 8
    )
    missing_marker[marker8[0]][marker8[1]] = 0
    assert any("exactly one 7 and one 8" in msg for msg in GENERATOR.self_check(missing_marker))

    duplicate_control = copy.deepcopy(grid)
    point = first_zero(duplicate_control)
    duplicate_control[point[0]][point[1]] = 2
    assert any("exactly one rotation control" in msg for msg in GENERATOR.self_check(duplicate_control))

    disconnected_template = copy.deepcopy(grid)
    blue = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 1
    ]
    disconnected_template[blue[0][0]][blue[0][1]] = 0
    far = first_zero(disconnected_template, blue)
    disconnected_template[far[0]][far[1]] = 1
    assert any("4-connected" in msg for msg in GENERATOR.self_check(disconnected_template))

    symmetric_template = copy.deepcopy(grid)
    for row, col in blue:
        symmetric_template[row][col] = 0
    square = None
    for row in range(len(grid) - 1):
        for col in range(len(grid[0]) - 1):
            cells = {(row, col), (row + 1, col), (row, col + 1), (row + 1, col + 1)}
            if all(symmetric_template[r][c] == 0 for r, c in cells):
                square = cells
                break
        if square:
            break
    assert square is not None
    for row, col in square:
        symmetric_template[row][col] = 1
    assert any("four distinct quarter-turn" in msg for msg in GENERATOR.self_check(symmetric_template))

    early_wall = copy.deepcopy(grid)
    facts = GENERATOR._facts(grid)
    control = facts["rotation_control"]
    shape = GENERATOR._controlled_shape(facts["template"], control)
    marker8 = next(
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 8
    )
    first_placement = GENERATOR._shape_at(shape, marker8)
    wall_cell = next(
        point for point in first_placement if early_wall[point[0]][point[1]] == 0
    )
    early_wall[wall_cell[0]][wall_cell[1]] = 5
    assert any("lawful placements" in msg for msg in GENERATOR.self_check(early_wall))


def test_negative_recombination_is_rejected_but_oracle_remains_executable():
    row = canonical_row()
    grid = GENERATOR.generate(55, 8, difficulty="medium", rotation_control=3)
    bad = copy.deepcopy(grid)
    control = next(
        (r, c)
        for r in range(len(bad))
        for c in range(len(bad[0]))
        if bad[r][c] in (2, 3, 4, 6)
    )
    bad[control[0]][control[1]] = 9  # 9 is absent from every other input scene part.
    assert any("rotation control" in msg for msg in GENERATOR.self_check(bad))
    with ProgramVerifier(timeout=30) as verifier:
        output = verifier.apply(row["program_solution"], bad)
    assert len(output) == len(bad)
    assert len(output[0]) == len(bad[0])


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(8675309)
    before = random.getstate()
    first = GENERATOR.generate(77, 19, difficulty="hard")
    after = random.getstate()
    second = GENERATOR.generate(77, 19, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(row1 is not row2 for row1, row2 in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
    assert before == after


def test_200_draw_linked_semantic_census_and_disjoint_stability():
    for seed_base in (100_000, 300_000):
        for band_index, band in enumerate(("easy", "medium", "hard")):
            counts = {
                "valid": 0,
                "edge": 0,
                "wall": 0,
                "cardinal": 0,
                "diagonal": 0,
            }
            controls = set()
            copies = set()
            template_sizes = set()
            inputs = set()
            outputs = set()
            for offset in range(200):
                grid = GENERATOR.generate(
                    seed_base + band_index * 1000 + offset,
                    offset + 7919,
                    difficulty=band,
                )
                assert GENERATOR.self_check(grid, difficulty=band) == []
                facts = GENERATOR.observe_overrides(grid)
                counts["valid"] += int(GENERATOR.canonical_like(grid))
                counts[facts["stop_mode"]] += 1
                counts[facts["vector_family"]] += 1
                controls.add(facts["rotation_control"])
                copies.add(facts["copy_count"])
                template_sizes.add(facts["template_cells"])
                inputs.add(frozen(grid))
                outputs.add(frozen(independent_rule(grid)))
            assert counts["valid"] == 200
            assert counts["edge"] > 0 and counts["wall"] > 0
            assert counts["cardinal"] > 0 and counts["diagonal"] > 0
            assert controls == {2, 3, 4, 6}
            assert len(copies) >= 2
            assert len(template_sizes) >= 2
            assert len(inputs) >= 198
            assert len(outputs) >= 198
