from __future__ import annotations

import copy
import importlib
import json
from pathlib import Path

MOD = importlib.import_module("puzzle_generators.per_puzzle.87c05932431e.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs():
    rows = []
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == MOD.TASK_ID:
            rows.extend(pair["input"] for pair in row.get("train", []))
            rows.extend(pair["input"] for pair in row.get("test", []))
    return rows


def test_canonical_inputs_are_accepted():
    inputs = _canonical_inputs()
    assert len(inputs) == 8
    assert all(MOD.self_check(grid) == [] for grid in inputs)


def test_all_exact_override_boundaries_are_observable():
    for overrides in (
        {"grid_h": 7, "grid_w": 7, "mask_h": 2, "mask_w": 2, "mask_variant": 0},
        {"grid_h": 18, "grid_w": 18, "mask_h": 4, "mask_w": 4, "mask_variant": 5},
        {"grid_h": 7, "grid_w": 18, "mask_h": 4, "mask_w": 2, "mask_variant": 5},
    ):
        grid = MOD.generate(123, 9, difficulty="hard", **overrides)
        assert MOD.self_check(grid) == []
        assert MOD.observe_overrides(grid) == overrides


def test_replay_freshness_and_unknown_override():
    first = MOD.generate(55, 4, difficulty="medium")
    second = MOD.generate(55, 4, difficulty="medium")
    assert first == second
    assert first is not second and all(a is not b for a, b in zip(first, second))
    try:
        MOD.generate(1, 0, typo_axis=3)
    except ValueError as exc:
        assert "unknown override" in str(exc)
    else:
        raise AssertionError("unknown override was silently accepted")


def test_self_check_rejects_targeted_impostors():
    grid = MOD.generate(77, 2, difficulty="medium")
    impostors = []

    all_background = [[grid[-1][-1] for _ in row] for row in grid]
    impostors.append(all_background)

    broken_separator = copy.deepcopy(grid)
    analysis = MOD._analyze(grid)
    broken_separator[analysis["mask_h"]][0] = analysis["background"]
    impostors.append(broken_separator)

    stray_outside = copy.deepcopy(grid)
    stray_outside[-1][-1] = analysis["foreground"]
    impostors.append(stray_outside)

    extra_color = copy.deepcopy(grid)
    used = set(value for row in grid for value in row)
    extra = next(color for color in range(10) if color not in used)
    extra_color[-1][0] = extra
    impostors.append(extra_color)

    collapsed_mask = copy.deepcopy(grid)
    for r in range(analysis["mask_h"]):
        for c in range(analysis["mask_w"]):
            collapsed_mask[r][c] = analysis["background"]
    impostors.append(collapsed_mask)

    assert all(MOD.self_check(candidate) for candidate in impostors)


def test_python_rule_mirror_is_pure_and_uses_all_three_output_roles():
    grid = MOD.generate(888, 5, difficulty="hard")
    before = copy.deepcopy(grid)
    output = MOD.rule_mirror(grid)
    assert grid == before
    assert output != grid
    analysis = MOD._analyze(grid)
    assert set(value for row in output for value in row) == {
        analysis["background"],
        analysis["foreground"],
        analysis["separator"],
    }


def test_three_consecutive_demos_refute_declared_competitors():
    for band in ("easy", "medium", "hard"):
        demos = []
        for sample_index in range(3):
            inp = MOD.generate(991, sample_index, difficulty=band)
            demos.append({"input": inp, "output": MOD.rule_mirror(inp)})
        query_input = MOD.generate(991, 3, difficulty=band)
        query = {"input": query_input, "output": MOD.rule_mirror(query_input)}
        assert MOD.lesson_identifiable(demos, query) == []
        for competitor in MOD.LESSON_COMPETITORS.values():
            assert any(competitor(demo["input"]) != demo["output"] for demo in demos)
