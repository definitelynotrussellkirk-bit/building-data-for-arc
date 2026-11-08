from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import (
    canonical_pairs,
    canonical_rule_hash,
    canonical_rule_source,
)


gen = importlib.import_module("puzzle_generators.per_puzzle.1b46e014e17c.generator")

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "1b46e014e17c"
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/9f005a7005fe/"
    "hard_63_boolean_gallery_from_two_templates__1b46e014e17c.json"
)


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    return pairs


def _first_zero_outside_roles(grid: list[list[int]]) -> tuple[int, int]:
    analysis = gen._analyze(grid)
    frames = analysis["frames"]
    for row in range(len(grid) - 1):
        for col in range(len(grid[0])):
            inside_frame_bbox = any(
                frame["r0"] <= row <= frame["r1"]
                and frame["c0"] <= col <= frame["c1"]
                for frame in frames
            )
            if grid[row][col] == 0 and not inside_frame_bbox:
                return row, col
    raise AssertionError("fixture has no zero outside the frame roles")


def test_rule_pin_and_python_mirror_match_every_canonical_pair():
    assert gen.VERSION == "2.0.0"
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "bd6e91262627"

    for pair in _canonical_pairs():
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]

    selected = json.loads(BASE_PATH.read_text(encoding="utf-8"))["racket_target"]
    assert selected["target_code"] == canonical_rule_source(TASK_ID)
    assert selected["raw_code"] == selected["target_code"]


def test_every_two_demo_schedule_window_identifies_the_rule_in_every_band():
    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        seed = 1701 + band_index
        for start in range(len(gen.SCHEDULE_PROFILES)):
            demos = []
            for sample_index in (start, start + 1):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(seed, start + 2, difficulty=difficulty)
            assert gen.lesson_identifiable(demos, {"input": query_grid}) == [], (
                difficulty,
                start,
            )

            anchor = demos[0 if start % 2 == 0 else 1]["input"]
            assert all(witness(anchor) for witness in gen.SEMANTIC_WITNESSES.values())
            expected = gen.rule_mirror(anchor)
            for rival_name, rival in gen.SEMANTIC_RIVALS.items():
                assert rival(anchor) != expected, (difficulty, start, rival_name)


def test_exact_override_boundaries_and_ordinary_schedule_are_observable():
    cases = [
        {
            "grid_h": 10,
            "grid_w": 18,
            "frame_inner_size": 3,
            "code_profile": "three_unique",
            "source_palette": "canonical",
        },
        {
            "grid_h": 12,
            "grid_w": 20,
            "frame_inner_size": 5,
            "code_profile": "four_heavy_repeat",
            "source_palette": "alternate",
        },
        {
            "grid_h": 11,
            "grid_w": 18,
            "frame_inner_size": 4,
            "code_profile": "four_all",
            "source_palette": "alternate",
        },
    ]
    for difficulty in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = gen.generate(
                6100 + index,
                index,
                difficulty=difficulty,
                **requested,
            )
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == requested

    expected_schedule = [
        (10, 18, 4, "four_all", "canonical"),
        (10, 18, 4, "three_with_repeat", "canonical"),
        (11, 19, 3, "four_all", "alternate"),
        (10, 18, 4, "three_unique", "canonical"),
        (12, 20, 5, "four_all", "canonical"),
        (10, 18, 4, "four_with_repeat", "canonical"),
        (11, 18, 4, "four_all", "alternate"),
        (10, 18, 4, "four_heavy_repeat", "canonical"),
    ]
    for sample_index, expected in enumerate(expected_schedule):
        grid = gen.generate(777, sample_index, difficulty="medium")
        assert tuple(gen.observe_overrides(grid).values()) == expected

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)


def test_replay_is_fresh_deterministic_and_process_global_rng_pure():
    random.seed(20260816)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 8
    assert first != second


def test_structural_self_check_rejects_four_targeted_impostors():
    grid = gen.generate(4201, 0, difficulty="hard")
    assert gen.self_check(grid) == []
    analysis = gen._analyze(grid)

    broken_frame = copy.deepcopy(grid)
    frame = analysis["frames"][0]
    broken_frame[frame["r0"]][frame["c0"]] = 0
    assert gen.self_check(broken_frame)

    stray_cell = copy.deepcopy(grid)
    row, col = _first_zero_outside_roles(stray_cell)
    stray_cell[row][col] = 1
    assert any("non-role" in error for error in gen.self_check(stray_cell))

    mixed_source = copy.deepcopy(grid)
    dr, dc = next(iter(frame["support"]))
    source_row = frame["r0"] + 1 + dr
    source_col = frame["c0"] + 1 + dc
    original_color = mixed_source[source_row][source_col]
    mixed_source[source_row][source_col] = 8 if original_color != 8 else 1
    assert any("monochrome" in error for error in gen.self_check(mixed_source))

    invalid_code_row = copy.deepcopy(grid)
    code_col = next(col for col, value in enumerate(invalid_code_row[-1]) if value)
    invalid_code_row[-1][code_col] = 2
    assert any("bottom-row" in error for error in gen.self_check(invalid_code_row))
