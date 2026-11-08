"""Focused regression tests for generator 1180c5a8d3c2 (ARC 7c008303)."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

gen = importlib.import_module("puzzle_generators.per_puzzle.1180c5a8d3c2.generator")

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_FILES = (
    ROOT / "data/base/solutions/training/7c008303__1180c5a8d3c2.json",
    ROOT / "data/base/solutions/augmented/7c008303__87600611f795.json",
)


def _canonical_inputs():
    for path in AUTHORITY_FILES:
        row = json.loads(path.read_text())
        visible = row["visible_context"]
        for pair in visible.get("train", []):
            yield pair["input"]
        for pair in visible.get("test_inputs", []):
            yield pair["input"]


def _parse(grid):
    parsed, errors = gen._analysis(grid)
    assert not errors, errors
    assert parsed is not None
    return parsed


def _rule_mirror(grid):
    parsed = _parse(grid)
    r1, c1, r2, c2 = parsed["mask_bounds"]
    key = parsed["key_values"]
    h, w = r2 - r1, c2 - c1
    half_h, half_w = h // 2, w // 2
    out = []
    for r in range(h):
        row = []
        for c in range(w):
            if grid[r1 + r][c1 + c] != 3:
                row.append(0)
                continue
            index = (2 if r >= half_h else 0) + (1 if c >= half_w else 0)
            row.append(key[index])
        out.append(row)
    return out


def test_accepts_every_canonical_input_from_every_authority_row():
    inputs = list(_canonical_inputs())
    assert len(inputs) == 8
    for grid in inputs:
        assert gen.self_check(grid) == []


def test_canonical_rule_mirror_matches_all_available_authority_outputs():
    checked = 0
    for path in AUTHORITY_FILES:
        row = json.loads(path.read_text())
        for pair in row["visible_context"].get("train", []):
            assert _rule_mirror(pair["input"]) == pair["output"]
            checked += 1
    assert checked == 7


def test_exact_axes_are_observable_at_boundaries():
    for h in (8, 14):
        for w in (8, 14):
            for corner in gen.KEY_CORNERS:
                for repeat in (False, True):
                    grid = gen.generate(
                        101,
                        7,
                        difficulty="easy",
                        grid_h=h,
                        grid_w=w,
                        key_corner=corner,
                        repeat_key=repeat,
                    )
                    assert gen.observe_overrides(grid) == {
                        "grid_h": h,
                        "grid_w": w,
                        "key_corner": corner,
                        "repeat_key": repeat,
                    }
                    assert gen.self_check(grid) == []


def test_canonical_size_and_repeated_key_regressions_are_generatable():
    grid = gen.generate(
        17,
        3,
        difficulty="medium",
        grid_h=9,
        grid_w=9,
        key_corner="tr",
        repeat_key=True,
    )
    parsed = _parse(grid)
    assert len(grid) == len(grid[0]) == 9
    assert parsed["key_corner"] == "tr"
    assert len(set(parsed["key_values"])) == 3
    assert tuple(parsed["mask_bounds"]) == (3, 0, 9, 6)


def test_every_generated_pair_witnesses_all_four_key_regions():
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            grid = gen.generate(seed, seed * 11 + 5, difficulty=band)
            parsed = _parse(grid)
            assert all(item["green"] > 0 for item in parsed["region_counts"])
            assert all(item["zero"] > 0 for item in parsed["region_counts"])
            output = _rule_mirror(grid)
            assert len(output) == parsed["mask_bounds"][2] - parsed["mask_bounds"][0]
            assert len(output[0]) == parsed["mask_bounds"][3] - parsed["mask_bounds"][1]


def _mutations(base):
    parsed = _parse(base)
    cross_r, cross_c = parsed["cross_r"], parsed["cross_c"]
    key_corner = parsed["key_corner"]
    key_bounds = gen._quadrants(len(base), len(base[0]), cross_r, cross_c)[key_corner]
    mask_bounds = parsed["mask_bounds"]
    empty_corner = next(
        corner
        for corner in gen.KEY_CORNERS
        if corner not in (key_corner, parsed["mask_corner"])
    )
    empty_bounds = gen._quadrants(len(base), len(base[0]), cross_r, cross_c)[empty_corner]

    broken_cross = copy.deepcopy(base)
    broken_cross[cross_r][0 if cross_c != 0 else 1] = 0
    yield "broken_cross", broken_cross

    key_hole = copy.deepcopy(base)
    kr1, kc1, _, _ = key_bounds
    key_hole[kr1][kc1] = 0
    yield "key_hole", key_hole

    key_two_colors = copy.deepcopy(base)
    key_two_colors[kr1][kc1] = 1
    key_two_colors[kr1][kc1 + 1] = 2
    key_two_colors[kr1 + 1][kc1] = 1
    key_two_colors[kr1 + 1][kc1 + 1] = 2
    yield "key_two_colors", key_two_colors

    polluted_empty = copy.deepcopy(base)
    er1, ec1, _, _ = empty_bounds
    polluted_empty[er1][ec1] = 5
    yield "polluted_empty", polluted_empty

    adjacent_pattern = copy.deepcopy(base)
    mr1, mc1, mr2, mc2 = mask_bounds
    for r in range(mr1, mr2):
        for c in range(mc1, mc2):
            adjacent_pattern[r][c] = 0
    adjacent_pattern[er1][ec1] = 3
    yield "adjacent_pattern", adjacent_pattern

    region_missing_green = copy.deepcopy(base)
    first_region = gen._region_cells(mr2 - mr1, mc2 - mc1)[0]
    for r, c in first_region:
        region_missing_green[mr1 + r][mc1 + c] = 0
    yield "region_missing_green", region_missing_green

    region_missing_zero = copy.deepcopy(base)
    second_region = gen._region_cells(mr2 - mr1, mc2 - mc1)[1]
    for r, c in second_region:
        region_missing_zero[mr1 + r][mc1 + c] = 3
    yield "region_missing_zero", region_missing_zero


def test_self_check_rejects_targeted_structural_impostors():
    base = gen.generate(
        999,
        4,
        difficulty="medium",
        grid_h=11,
        grid_w=12,
        key_corner="tl",
        repeat_key=False,
    )
    rejected = {}
    for name, grid in _mutations(base):
        errors = gen.self_check(grid)
        assert errors, name
        rejected[name] = errors
    assert len(rejected) == 7


def test_replay_is_fresh_and_does_not_touch_process_global_rng():
    random.seed(24680)
    state = random.getstate()
    first = gen.generate(321, 9, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(321, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 99
    third = gen.generate(321, 9, difficulty="hard")
    assert third == second
