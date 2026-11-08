from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base
gen = importlib.import_module("puzzle_generators.per_puzzle.1e7eb285f158.generator")


ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs() -> list[tuple[list[list[int]], list[list[int]]]]:
    pairs: list[tuple[list[list[int]], list[list[int]]]] = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != gen.TASK_ID:
                continue
            for split in ("train", "test"):
                for pair in row.get(split, []):
                    pairs.append((pair["input"], pair["output"]))
    return pairs


def test_all_canonical_pairs_are_accepted_and_python_mirror_is_exact_and_pure() -> None:
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for source, expected in pairs:
        grid = copy.deepcopy(source)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == expected
        assert grid == source


def test_ordinary_four_sample_schedule_exposes_both_tie_break_branches() -> None:
    expected = ["unique", "row_tie", "column_tie", "unique"]
    for band in ("easy", "medium", "hard"):
        for seed in (0, 17, 1000):
            actual = [
                gen.semantic_signature(gen.generate(seed, index, difficulty=band))["tie_kind"]
                for index in range(4)
            ]
            assert actual == expected


def test_ordinary_ctx_requests_are_observable_without_fallback_drift() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            captured: list[object] = []
            base.set_ctx_observer(captured.append)
            try:
                grid = gen.generate(seed, seed % 4, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert captured
            ctx = captured[-1]
            observed = gen.observe_overrides(grid)
            for axis in gen.AXES:
                assert observed[axis] == ctx.recorded_draws()[axis]


def test_exact_override_boundaries_and_combinations_are_observable() -> None:
    cases = [
        {"grid_h": 12}, {"grid_h": 21},
        {"grid_w": 12}, {"grid_w": 21},
        {"rect_h": 3}, {"rect_h": 7},
        {"rect_w": 3}, {"rect_w": 7},
        {"foreground_color": 1}, {"foreground_color": 7},
        {"palette_mode": "one_nonzero"}, {"palette_mode": "two_nonzero"},
        {"noise_level": "sparse"}, {"noise_level": "balanced"},
        {"noise_level": "dense"},
        *({"position_bias": mode} for mode in gen.POSITION_BIASES),
        {
            "grid_h": 21,
            "grid_w": 21,
            "rect_h": 7,
            "rect_w": 7,
            "foreground_color": 7,
            "palette_mode": "two_nonzero",
            "noise_level": "dense",
            "position_bias": "bottom_right",
        },
    ]
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = gen.generate(500 + index, 73, difficulty=band, **overrides)
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            for axis, value in overrides.items():
                assert observed[axis] == value


def test_deterministic_replay_returns_fresh_objects_and_preserves_global_rng() -> None:
    random.seed(493_017)
    state = random.getstate()
    first = gen.generate(91, 2, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(91, 2, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_self_check_rejects_targeted_structural_impostors() -> None:
    base_grid = gen.generate(808, 0, difficulty="medium")
    signature = gen.semantic_signature(base_grid)
    top, left, bottom, right = gen._analyze(base_grid)["facts"]["best"]
    foreground = signature["foreground_color"]

    no_target = copy.deepcopy(base_grid)
    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            no_target[row][col] = foreground
    assert any("no all-zero rectangle" in error for error in gen.self_check(no_target))

    output_color_leak = copy.deepcopy(base_grid)
    output_color_leak[0][0] = 8
    assert any("output color 8" in error for error in gen.self_check(output_color_leak))

    absent_replacement = copy.deepcopy(base_grid)
    absent_replacement[0][0] = 9
    assert any("only input colors 0..7" in error for error in gen.self_check(absent_replacement))

    three_textures = gen.generate(811, 0, difficulty="medium", palette_mode="two_nonzero")
    present = {value for row in three_textures for value in row}
    third = next(color for color in range(1, 8) if color not in present)
    changed = False
    for row in range(len(three_textures)):
        for col in range(len(three_textures[0])):
            if three_textures[row][col] != 0:
                three_textures[row][col] = third
                changed = True
                break
        if changed:
            break
    assert any("one or two nonzero" in error for error in gen.self_check(three_textures))

    all_zero = [[0 for _ in range(12)] for _ in range(12)]
    assert gen.self_check(all_zero)

    all_solid = [[2 for _ in range(12)] for _ in range(12)]
    assert any("no all-zero rectangle" in error for error in gen.self_check(all_solid))


def test_lesson_identifiability_rebuts_shortcut_competitors() -> None:
    for band in ("easy", "medium", "hard"):
        pairs = []
        for index in range(4):
            grid = gen.generate(2026, index, difficulty=band)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_invalid_calls_reject_loudly() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(0, 0, texture="legacy")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="expert")
    with pytest.raises(ValueError, match="grid_h"):
        gen.generate(0, 0, grid_h=11)
    with pytest.raises(ValueError, match="palette_mode"):
        gen.generate(0, 0, palette_mode="three_nonzero")
