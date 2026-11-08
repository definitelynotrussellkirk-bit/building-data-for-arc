from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import os
import random
from collections import Counter
from pathlib import Path

import pytest

TASK_ID = "97e1d2aa0bc3"
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
                return [pair for split in ("train", "test") for pair in row[split]]
    raise AssertionError("canonical task row not found")


def _independent_rule(grid):
    output = []
    for row in grid:
        counts = Counter(value for value in row if value not in (0, 7))
        top_count = max(counts.values())
        targets = [color for color, count in counts.items() if count == top_count]
        assert len(targets) == 1
        target = targets[0]
        output.append([0 if value == target else target for value in row])
    return output


def _axis_boundary(spec):
    lo, hi = map(int, spec["valid"].split(".."))
    return (lo, hi)


def test_rule_hash_version_and_override_surface_are_pinned():
    assert mod.RULE_HASH == "aaa71b99c62e"
    assert mod.VERSION == "3.0.0"
    assert set(mod.AXES) == {"grid_h", "grid_w"}


def test_all_canonical_pairs_pass_and_match_exact_rule():
    for pair in _canonical_pairs():
        source = copy.deepcopy(pair["input"])
        assert mod.self_check(source) == []
        assert mod.rule_mirror(source) == pair["output"]
        assert _independent_rule(source) == pair["output"]


def test_every_declared_dimension_boundary_works_in_every_band():
    h_values = _axis_boundary(mod.AXES["grid_h"])
    w_values = _axis_boundary(mod.AXES["grid_w"])
    for band in ("easy", "medium", "hard"):
        for height in h_values:
            for width in w_values:
                grid = mod.generate(
                    91,
                    5,
                    difficulty=band,
                    grid_h=height,
                    grid_w=width,
                )
                assert (len(grid), len(grid[0])) == (height, width)
                assert mod.observe_overrides(grid) == {
                    "grid_h": height,
                    "grid_w": width,
                }
                assert mod.self_check(grid) == []
                assert mod.rule_mirror(grid) == _independent_rule(grid)


def test_schedule_covers_noise_branches_and_layouts():
    observed_layout_signatures = set()
    saw_seven = False
    saw_no_seven = False
    saw_seven_dominant_shortcut_rebuttal = False
    for sample_index in range(6):
        grid = mod.generate(73, sample_index, difficulty="medium", grid_h=3, grid_w=10)
        assert mod.self_check(grid) == []
        saw_seven |= any(7 in row for row in grid)
        saw_no_seven |= all(7 not in row for row in grid)
        row_signatures = []
        for row in grid:
            counts = Counter(value for value in row if value not in (0, 7))
            target = max(counts, key=counts.get)
            assert any(value not in (0, 7, target) for value in row)
            if row.count(7) > counts[target]:
                most_frequent_nonzero = Counter(value for value in row if value != 0).most_common(1)[0][0]
                assert most_frequent_nonzero == 7
                saw_seven_dominant_shortcut_rebuttal = True
            row_signatures.append(tuple(index for index, value in enumerate(row) if value == target))
        observed_layout_signatures.add(tuple(row_signatures))
        assert mod.rule_mirror(grid) == _independent_rule(grid)
    assert saw_seven and saw_no_seven
    assert saw_seven_dominant_shortcut_rebuttal
    assert len(observed_layout_signatures) >= 3


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


def test_self_check_rejects_four_targeted_impostors():
    lawful = mod.generate(37, 1, difficulty="medium", grid_h=3, grid_w=10)
    assert mod.self_check(lawful) == []

    all_background = [[0 for _ in range(10)] for _ in range(3)]
    assert mod.self_check(all_background)

    repeated_target = copy.deepcopy(lawful)
    first_counts = Counter(v for v in repeated_target[0] if v not in (0, 7))
    first_target = max(first_counts, key=first_counts.get)
    second_counts = Counter(v for v in repeated_target[1] if v not in (0, 7))
    second_target = max(second_counts, key=second_counts.get)
    repeated_target[1] = [first_target if v == second_target else v for v in repeated_target[1]]
    assert mod.self_check(repeated_target)

    tied_mode = copy.deepcopy(lawful)
    counts = Counter(v for v in tied_mode[0] if v not in (0, 7))
    target = max(counts, key=counts.get)
    noise = next(v for v in tied_mode[0] if v not in (0, 7, target))
    target_positions = [i for i, v in enumerate(tied_mode[0]) if v == target]
    for index in target_positions[: (counts[target] - counts[noise]) // 2]:
        tied_mode[0][index] = noise
    assert mod.self_check(tied_mode)

    hidden_inversion = copy.deepcopy(lawful)
    row_target = max(
        Counter(v for v in hidden_inversion[0] if v not in (0, 7)),
        key=Counter(v for v in hidden_inversion[0] if v not in (0, 7)).get,
    )
    hidden_inversion[0] = [row_target] * len(hidden_inversion[0])
    assert mod.self_check(hidden_inversion)

    invalid_color = copy.deepcopy(lawful)
    invalid_color[0][0] = 10
    assert mod.self_check(invalid_color)


def test_unknown_override_rejects_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        mod.generate(1, 2, difficulty="easy", texture="scattered")
