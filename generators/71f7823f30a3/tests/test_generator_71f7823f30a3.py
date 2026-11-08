from __future__ import annotations

import copy
import importlib.util
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN_PATH = ROOT / "puzzle_generators/per_puzzle/71f7823f30a3/generator.py"
BASE_PATH = ROOT / "data/base/solutions/banks/56b8d7075625/E161__71f7823f30a3.json"


def _load_generator():
    spec = importlib.util.spec_from_file_location("generator_71f7823f30a3", GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _canonical_inputs():
    row = json.loads(BASE_PATH.read_text())
    context = row["visible_context"]
    return [pair["input"] for pair in context["train"]] + [pair["input"] for pair in context["test_inputs"]]


def _mirror_target(grid):
    for r, row in enumerate(grid):
        anchors = [c for c, value in enumerate(row) if value == 9]
        if len(anchors) != 1:
            continue
        anchor = anchors[0]
        for c, value in enumerate(row):
            if value in (0, 9):
                continue
            target = 2 * anchor - c
            if 0 <= target < len(row) and row[target] == 0:
                return r, target, value
    raise AssertionError("no mirror target found")


def test_rule_hash_is_pinned_to_selected_authority():
    gen = _load_generator()
    assert gen.RULE_HASH == "2f1f3e5388a0"


def test_self_check_accepts_every_canonical_input():
    gen = _load_generator()
    for grid in _canonical_inputs():
        assert gen.self_check(grid) == []


def test_generated_inputs_teach_row_local_bidirectional_rule():
    gen = _load_generator()
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(20):
            grid = gen.generate(seed, seed % 3, difficulty=difficulty)
            assert gen.self_check(grid, difficulty=difficulty) == []
            observed = gen.observe_overrides(grid)
            assert observed["n_anchor_rows"] < observed["grid_h"]
            assert observed["source_count"] >= observed["n_anchor_rows"]
            analysis = gen._analyze_grid(grid)
            assert analysis["left_count"] > 0
            assert analysis["right_count"] > 0
            assert not any(all(grid[r][c] == 9 for r in range(len(grid))) for c in range(len(grid[0])))


def test_all_exact_override_axes_are_observable():
    gen = _load_generator()
    cases = [
        dict(grid_h=4, grid_w=7, n_anchor_rows=2, source_count=4,
             anchor_profile="shared", side_balance="left_heavy",
             palette_kind="warm", orphan_profile="empty"),
        dict(grid_h=10, grid_w=15, n_anchor_rows=3, source_count=5,
             anchor_profile="varied", side_balance="right_heavy",
             palette_kind="mixed", orphan_profile="colored"),
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(900 + index, index, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides


def test_self_check_rejects_four_structural_impostors():
    gen = _load_generator()
    grid = gen.generate(1234, 0, difficulty="medium")

    duplicate_anchor = copy.deepcopy(grid)
    anchored_row = next(r for r, row in enumerate(duplicate_anchor) if 9 in row)
    empty = next(c for c, value in enumerate(duplicate_anchor[anchored_row]) if value == 0)
    duplicate_anchor[anchored_row][empty] = 9
    assert any("at most one" in error for error in gen.self_check(duplicate_anchor))

    occupied_target = copy.deepcopy(grid)
    row, column, value = _mirror_target(occupied_target)
    occupied_target[row][column] = value
    assert any("nonempty mirror target" in error for error in gen.self_check(occupied_target))

    one_sided = copy.deepcopy(grid)
    for row in one_sided:
        anchors = [c for c, value in enumerate(row) if value == 9]
        if not anchors:
            continue
        anchor = anchors[0]
        for c in range(anchor + 1, len(row)):
            if row[c] not in (0, 9):
                row[c] = 0
    assert any("both sides" in error for error in gen.self_check(one_sided))

    full_height_axis = [[0] * 9 for _ in range(4)]
    for row in full_height_axis:
        row[4] = 9
        row[2] = 1
    full_height_axis[0][6] = 2
    full_height_axis[0][2] = 0
    assert any("row without" in error for error in gen.self_check(full_height_axis))


def test_generation_is_deterministic_fresh_and_rng_pure():
    gen = _load_generator()
    random.seed(777)
    state = random.getstate()
    first = gen.generate(42, 2, difficulty="hard")
    second = gen.generate(42, 2, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert first != second
    assert random.getstate() == state


def test_sequential_three_example_schedule_contains_disambiguators():
    gen = _load_generator()
    observed = [gen.observe_overrides(gen.generate(321, index, difficulty="medium")) for index in range(3)]
    assert {row["side_balance"] for row in observed} == {"left_heavy", "right_heavy"}
    assert "varied" in {row["anchor_profile"] for row in observed}
    assert "colored" in {row["orphan_profile"] for row in observed}
    assert {row["palette_kind"] for row in observed} == {"warm", "cool", "mixed"}
