from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.39ca907f7cf4.generator")


def _canonical_pairs():
    for line in Path("data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return list(row["train"]) + list(row["test"])
    raise AssertionError("canonical task not found")


def test_canonical_inputs_and_outputs_match_rule_mirror():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_rule_hash_and_exact_override_boundaries_are_observable():
    assert gen.RULE_HASH == "c2f0790b1442"
    cases = (
        {"grid_h": 7, "grid_w": 9, "n": 3, "marker_corner": "tl", "target_size": 3},
        {"grid_h": 7, "grid_w": 9, "n": 4, "marker_corner": "br", "target_size": 5},
        {"grid_h": 12, "grid_w": 14, "n": 3, "marker_corner": "bl", "target_size": 4},
        {"grid_h": 12, "grid_w": 14, "n": 4, "marker_corner": "tr", "target_size": 5},
    )
    for index, overrides in enumerate(cases):
        grid = gen.generate(9173, index + 1, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid) == []


@pytest.mark.parametrize("unknown", ["texture", "palette_kind", "typo_axis"])
def test_unknown_overrides_reject_loudly(unknown):
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, **{unknown: "anything"})


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(4815162342)
    state = random.getstate()
    first = gen.generate(44, 7, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(44, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == gen.generate(44, 7, difficulty="medium")


def test_self_check_rejects_targeted_impostors():
    valid = gen.generate(99, 3, grid_h=9, grid_w=11, n=4, marker_corner="tl", target_size=5)
    assert gen.self_check(valid) == []

    no_marker = copy.deepcopy(valid)
    no_marker[0][0] = 0
    assert any("occupied corner" in reason for reason in gen.self_check(no_marker))

    two_markers = copy.deepcopy(valid)
    two_markers[-1][-1] = next(color for color in range(1, 10) if color not in {v for row in valid for v in row})
    assert any("exactly one occupied corner" in reason for reason in gen.self_check(two_markers))

    enlarged_marker = copy.deepcopy(valid)
    enlarged_marker[0][1] = enlarged_marker[0][0]
    assert any("singleton" in reason for reason in gen.self_check(enlarged_marker))

    distance_tie = [[0] * 9 for _ in range(7)]
    distance_tie[0][0] = 1
    for r, c in ((1, 3), (1, 4), (2, 3)):
        distance_tie[r][c] = 2
    for r, c in ((3, 1), (4, 1), (3, 2)):
        distance_tie[r][c] = 3
    assert any("one winner" in reason for reason in gen.self_check(distance_tie))

    repeated_color = [[0] * 9 for _ in range(7)]
    repeated_color[0][0] = 1
    for r, c in ((1, 3), (1, 4), (2, 3)):
        repeated_color[r][c] = 2
    for r, c in ((4, 6), (4, 7), (5, 7)):
        repeated_color[r][c] = 2
    assert any("distinct" in reason for reason in gen.self_check(repeated_color))

    tiny_candidate = [[0] * 9 for _ in range(7)]
    tiny_candidate[0][0] = 1
    tiny_candidate[1][2] = tiny_candidate[1][3] = 2
    for r, c in ((4, 5), (4, 6), (5, 6)):
        tiny_candidate[r][c] = 3
    assert any("outside 3..5" in reason for reason in gen.self_check(tiny_candidate))


def test_shortcut_rebuttals_and_every_sliding_lesson_window():
    seed = 20260726
    pairs = []
    for sample_index in range(16):
        grid = gen.generate(seed, sample_index)
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})

    assert sum(gen.strict_canonical_like(pair["input"]) == [] for pair in pairs) >= 5
    for name in (
        "reading_order_first_rebutted",
        "reading_order_last_rebutted",
        "smallest_size_rebutted",
        "largest_size_rebutted",
        "lowest_color_rebutted",
        "highest_color_rebutted",
        "centroid_distance_rebutted",
        "marker_as_answer_rebutted",
        "fixed_2x2_crop_rebutted",
    ):
        assert any(gen.SEMANTIC_WITNESSES[name](pair["input"]) for pair in pairs), name

    for start in range(len(pairs) - gen.EXAMPLES_NEEDED):
        demos = pairs[start : start + gen.EXAMPLES_NEEDED]
        query = pairs[start + gen.EXAMPLES_NEEDED]
        assert gen.lesson_identifiable(demos, query) == []
