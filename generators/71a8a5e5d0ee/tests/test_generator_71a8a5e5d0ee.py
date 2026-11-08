from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "71a8a5e5d0ee"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError("canonical task row not found")


def _pair(seed: int, sample_index: int, band: str):
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_generator_71a8a5e5d0ee_rule_hash_and_canonical_authority():
    assert GEN.RULE_HASH == "75f502e2e53c"
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_generator_71a8a5e5d0ee_profile_schedule_covers_decisive_branches():
    for band in ("easy", "medium", "hard"):
        signatures = [
            GEN.semantic_signature(GEN.generate(123, index, difficulty=band))
            for index in range(6)
        ]
        assert [row["template_size"] for row in signatures] == [3, 4, 3, 5, 4, 5]
        assert [row["marker_count"] for row in signatures] == [2, 2, 3, 1, 3, 2]
        assert all(row["strict_canonical_like"] for row in signatures[:3])
        assert not any(row["strict_canonical_like"] for row in signatures[3:])
        assert signatures[0]["clipped_stamps"] == 0
        assert signatures[1]["clipped_stamps"] == 0
        assert signatures[2]["clipped_stamps"] >= 1
        assert signatures[4]["clipped_stamps"] >= 1


def test_generator_71a8a5e5d0ee_exact_override_boundaries_are_observable():
    for band in ("easy", "medium", "hard"):
        for height in (5, 14):
            for width in (8, 18):
                for marker_count in (1, 3):
                    for sample_index in range(6):
                        grid = GEN.generate(
                            9001,
                            sample_index,
                            difficulty=band,
                            grid_h=height,
                            grid_w=width,
                            n_markers=marker_count,
                        )
                        assert GEN.self_check(grid) == []
                        assert GEN.observe_overrides(grid) == {
                            "grid_h": height,
                            "grid_w": width,
                            "n_markers": marker_count,
                        }

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, texture="warm")
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")


def test_generator_71a8a5e5d0ee_self_check_rejects_targeted_impostors():
    base = GEN.generate(314159, 4, difficulty="medium")
    facts = GEN._analyze(base)["facts"]

    no_template = copy.deepcopy(base)
    for row, col in facts["template_cells"]:
        no_template[row][col] = 0

    no_markers = copy.deepcopy(base)
    for row, col in facts["markers"]:
        no_markers[row][col] = 0

    split_template_color = copy.deepcopy(base)
    changed = min(facts["template_cells"])
    replacement = next(
        color
        for color in range(1, 9)
        if color != facts["template_color"]
    )
    split_template_color[changed[0]][changed[1]] = replacement

    adjacent_markers = copy.deepcopy(base)
    marker = facts["markers"][0]
    placed = False
    for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        row, col = marker[0] + dr, marker[1] + dc
        if (
            0 <= row < len(base)
            and 0 <= col < len(base[0])
            and adjacent_markers[row][col] == 0
        ):
            adjacent_markers[row][col] = 9
            placed = True
            break
    assert placed

    rotationally_symmetric = [[0] * 10 for _ in range(8)]
    for row, col in ((1, 1), (1, 2), (2, 1), (2, 2)):
        rotationally_symmetric[row][col] = 4
    rotationally_symmetric[5][6] = 9

    overlapping_stamps = [[0] * 12 for _ in range(8)]
    for row, col in ((0, 0), (0, 1), (0, 2), (1, 0), (2, 0)):
        overlapping_stamps[row][col] = 5
    overlapping_stamps[4][4] = 9
    overlapping_stamps[4][6] = 9

    impostors = {
        "no_template": no_template,
        "no_markers": no_markers,
        "split_template_color": split_template_color,
        "adjacent_markers": adjacent_markers,
        "rotationally_symmetric": rotationally_symmetric,
        "overlapping_stamps": overlapping_stamps,
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_generator_71a8a5e5d0ee_is_deterministic_fresh_rng_and_input_pure():
    random.seed(771)
    state = random.getstate()
    first = GEN.generate(44, 4, difficulty="hard")
    assert random.getstate() == state
    snapshot = copy.deepcopy(first)
    second = GEN.generate(44, 4, difficulty="hard")
    assert first == second == snapshot
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    first[0][0] = 9 if first[0][0] != 9 else 1
    replay = GEN.generate(44, 4, difficulty="hard")
    assert replay == snapshot
    before = copy.deepcopy(replay)
    GEN.rule_mirror(replay)
    GEN.self_check(replay)
    GEN.strict_canonical_like(replay)
    GEN.observe_overrides(replay)
    assert replay == before
    assert random.getstate() == state


def test_generator_71a8a5e5d0ee_four_demo_lessons_refute_named_rivals():
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            pairs = [_pair(seed, index, band) for index in range(5)]
            assert GEN.lesson_identifiable(pairs[:4], pairs[4]) == []
