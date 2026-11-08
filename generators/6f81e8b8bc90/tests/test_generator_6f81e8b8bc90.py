from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import os
import random
from pathlib import Path

import pytest

TASK_ID = "6f81e8b8bc90"
ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    override = os.environ.get("GENERATOR_UNDER_TEST")
    if not override:
        return importlib.import_module(
            f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        )
    path = Path(override)
    spec = importlib.util.spec_from_file_location(
        f"generator_under_test_{TASK_ID}", path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load_module()


def _canonical_pairs():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                pairs = list(row["train"])
                test = row["test"]
                pairs.extend(test if isinstance(test, list) else [test])
                return pairs
    raise AssertionError("canonical task row not found")


def _norm(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return copy.deepcopy(grid)


def _axis_bounds(name):
    return tuple(map(int, mod.AXES[name]["valid"].split("..")))


def _independent_rule(grid):
    count = sum(value == 3 for row in grid for value in row)
    return [[7] * count for _ in range(count)] if count else [[0]]


def _green_components(grid):
    cells = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 3
    }
    total = 0
    while cells:
        total += 1
        stack = [cells.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (r + dr, c + dc)
                if neighbor in cells:
                    cells.remove(neighbor)
                    stack.append(neighbor)
    return total


def test_rule_hash_version_and_exact_override_surface_are_pinned():
    assert mod.RULE_HASH == "48e63841a0da"
    assert mod.VERSION == "3.0.0"
    assert set(mod.AXES) == {"grid_h", "grid_w", "dot_count"}


def test_all_canonical_pairs_pass_and_match_exact_rule():
    for pair in _canonical_pairs():
        source = _norm(pair["input"])
        expected = _norm(pair["output"])
        assert mod.self_check(source) == []
        assert mod.strict_canonical_like(source) == []
        assert mod.rule_mirror(source) == expected
        assert _independent_rule(source) == expected


def test_every_axis_boundary_combination_works_in_every_band():
    for band in ("easy", "medium", "hard"):
        for height in _axis_bounds("grid_h"):
            for width in _axis_bounds("grid_w"):
                for dot_count in _axis_bounds("dot_count"):
                    grid = mod.generate(
                        91,
                        6,
                        difficulty=band,
                        grid_h=height,
                        grid_w=width,
                        dot_count=dot_count,
                    )
                    assert mod.observe_overrides(grid) == {
                        "grid_h": height,
                        "grid_w": width,
                        "dot_count": dot_count,
                    }
                    assert mod.self_check(grid) == []
                    assert mod.rule_mirror(grid) == _independent_rule(grid)


def test_sample_index_schedule_covers_counts_and_shortcut_rebuttals():
    observed_counts = []
    for sample_index in range(6):
        grid = mod.generate(73, sample_index, difficulty="medium")
        observed = mod.observe_overrides(grid)
        observed_counts.append(observed["dot_count"])
        assert mod.self_check(grid) == []
        assert mod.rule_mirror(grid) == _independent_rule(grid)
        if sample_index in (0, 1):
            assert mod.strict_canonical_like(grid) == []
        else:
            green = observed["dot_count"]
            nonzero = sum(value != 0 for row in grid for value in row)
            green_rows = sum(any(value == 3 for value in row) for row in grid)
            green_cols = sum(
                any(grid[r][c] == 3 for r in range(len(grid)))
                for c in range(len(grid[0]))
            )
            assert nonzero > green
            assert _green_components(grid) < green
            assert green_rows < green
            assert green_cols < green
            assert mod.SEMANTIC_WITNESSES["dominant_non_green_distractor"](grid)
            assert mod.SEMANTIC_WITNESSES[
                "green_positions_span_border_and_interior"
            ](grid)
    assert observed_counts == list(range(2, 8))


def test_every_cyclic_three_demo_lesson_is_identifiable():
    for start in range(6):
        pairs = []
        for sample_index in range(start, start + 4):
            grid = mod.generate(127, sample_index)
            pairs.append({"input": grid, "output": mod.rule_mirror(grid)})
        assert mod.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_determinism_freshness_and_global_random_purity():
    before = random.getstate()
    first = mod.generate(123, 6, difficulty="hard")
    after_first = random.getstate()
    second = mod.generate(123, 6, difficulty="hard")
    after_second = random.getstate()
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after_first == after_second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert mod.generate(123, 6, difficulty="hard") == second


def test_self_check_rejects_targeted_impostors():
    lawful = mod.generate(37, 5, difficulty="medium")
    assert mod.self_check(lawful) == []

    no_green = [[0 for _ in range(6)] for _ in range(5)]
    assert mod.self_check(no_green)

    singleton = copy.deepcopy(no_green)
    singleton[2][3] = 3
    assert mod.self_check(singleton)

    output_color_leak = copy.deepcopy(lawful)
    output_color_leak[0][0] = 7
    assert mod.self_check(output_color_leak)

    two_distractor_colors = copy.deepcopy(lawful)
    existing = next(
        value
        for row in two_distractor_colors
        for value in row
        if value not in (0, 3)
    )
    replacement = next(color for color in (1, 2, 4, 5, 6, 8, 9) if color != existing)
    cell = next(
        (r, c)
        for r, row in enumerate(two_distractor_colors)
        for c, value in enumerate(row)
        if value == existing
    )
    two_distractor_colors[cell[0]][cell[1]] = replacement
    assert mod.self_check(two_distractor_colors)

    weak_distractor = [[0 for _ in range(6)] for _ in range(5)]
    for r, c in ((0, 0), (2, 2), (4, 4)):
        weak_distractor[r][c] = 3
    weak_distractor[1][1] = 2
    assert mod.self_check(weak_distractor)

    short_line = [[0 for _ in range(6)] for _ in range(5)]
    for c in range(4):
        short_line[2][c] = 3
    assert mod.self_check(short_line)

    solid_2x2 = [[0 for _ in range(6)] for _ in range(5)]
    for r in range(2):
        for c in range(2):
            solid_2x2[r][c] = 3
    assert mod.self_check(solid_2x2)

    wrong_shape = [[0 for _ in range(5)] for _ in range(4)]
    wrong_shape[0][0] = wrong_shape[2][2] = 3
    assert mod.self_check(wrong_shape)


def test_negative_recombination_is_rejected_while_rule_remains_total():
    grid = mod.generate(43, 6)
    remaining = {value for row in grid for value in row if value != 3}
    replacement = next(color for color in range(1, 10) if color not in remaining and color != 7)
    impostor = [
        [replacement if value == 3 else value for value in row]
        for row in grid
    ]
    assert mod.self_check(impostor)
    assert mod.rule_mirror(impostor) == [[0]]


def test_unknown_override_rejects_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        mod.generate(1, 2, difficulty="easy", texture="scattered")
