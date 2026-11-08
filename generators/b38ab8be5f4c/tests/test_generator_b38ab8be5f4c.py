"""Focused regressions for the guide-color crop generator."""
from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.b38ab8be5f4c import generator as gen


ROOT = Path(__file__).resolve().parents[1]


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row not found")


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_owned() -> None:
    assert gen.RULE_HASH == "439c1e733337"
    row = _canonical_row()
    pairs = [*row["train"], row["test"]]
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        frozen = copy.deepcopy(grid)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == gen._coerce_grid(pair["output"])
        assert grid == frozen


def test_exact_override_boundaries_are_observable_in_every_band() -> None:
    cases = (
        {"grid_h": 8, "grid_w": 10, "marker_col": 0, "guide": 1,
         "target_shape": "tee4", "target_zone": "left", "bbox_intruder": False},
        {"grid_h": 10, "grid_w": 13, "marker_col": 9, "guide": 9,
         "target_shape": "ring8", "target_zone": "right", "bbox_intruder": True},
        {"grid_h": 9, "grid_w": 12, "marker_col": 5, "guide": 4,
         "target_shape": "stair5", "target_zone": "center", "bbox_intruder": False},
    )
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = gen.generate(700 + index, 17 + index, difficulty=band, **overrides)
            assert gen.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
            observed = gen.observe_overrides(grid)
            assert {key: observed[key] for key in overrides} == overrides


def test_every_sliding_lesson_window_refutes_named_competitors() -> None:
    # LCM of the 3/4/20 schedules is 60; every possible start residue is tested.
    for band in ("easy", "medium", "hard"):
        for start in range(60):
            demos = [_pair(gen.generate(991, start + offset, difficulty=band)) for offset in range(4)]
            query = _pair(gen.generate(991, start + 4, difficulty=band))
            assert gen.lesson_identifiable(demos, query) == [], (band, start)
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), (band, start, name)


def test_decisive_counterexamples_fire_in_each_four_sample_block() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(0, 40, 4):
            grids = [gen.generate(1234, start + offset, difficulty=band) for offset in range(4)]
            assert any(gen.SEMANTIC_WITNESSES["marker_not_column_zero"](grid) for grid in grids)
            assert any(gen.SEMANTIC_WITNESSES["bbox_contains_other_color"](grid) for grid in grids)
            assert any(gen.SEMANTIC_WITNESSES["target_not_largest"](grid) for grid in grids)
            assert {gen.observe_overrides(grid)["target_zone"] for grid in grids} == {
                "left", "center", "right"
            }


def test_raw_crop_preserves_bbox_intruder_and_refutes_masking() -> None:
    grid = gen.generate(
        44, 3, difficulty="medium", target_shape="ring8", bbox_intruder=True,
        marker_col=7, target_zone="center",
    )
    facts = gen._analyze(grid)
    assert facts["target"]["bbox_intruder"] is True
    output = gen.rule_mirror(grid)
    assert any(value not in (0, facts["guide"]) for row in output for value in row)
    assert output != gen.SEMANTIC_RIVALS["mask_non_guide_inside_bbox"](grid)
    assert output != gen.SEMANTIC_RIVALS["guide_only_from_column_zero"](grid)


def test_self_check_rejects_targeted_structural_impostors() -> None:
    base = gen.generate(88, 8, difficulty="medium", bbox_intruder=False)
    facts = gen._analyze(base)
    guide = facts["guide"]
    mutations = {}

    no_marker = copy.deepcopy(base)
    no_marker[0][facts["marker_col"]] = 0
    mutations["no_marker"] = no_marker

    two_markers = copy.deepcopy(base)
    two_markers[0][(facts["marker_col"] + 1) % len(base[0])] = guide
    mutations["two_markers"] = two_markers

    missing_guide_body = copy.deepcopy(base)
    replacement = next(color for color in range(1, 10) if color not in facts["body_colors"])
    for row, col in facts["target"]["cells"]:
        missing_guide_body[row][col] = replacement
    mutations["missing_guide_body"] = missing_guide_body

    disconnected_guide = copy.deepcopy(base)
    row, col = facts["target"]["cells"][0]
    disconnected_guide[row][col] = 0
    destination = next(
        (r, c)
        for r in range(2, len(base) - 1)
        for c in range(len(base[0]))
        if disconnected_guide[r][c] == 0
        and all(abs(r - rr) + abs(c - cc) > 1 for rr, cc in facts["target"]["cells"])
    )
    disconnected_guide[destination[0]][destination[1]] = guide
    mutations["disconnected_guide"] = disconnected_guide

    nonblank_row1 = copy.deepcopy(base)
    nonblank_row1[1][0] = next(color for color in facts["body_colors"] if color != guide)
    mutations["nonblank_row1"] = nonblank_row1

    missing_distractor = copy.deepcopy(base)
    distractor_color = next(color for color in facts["body_colors"] if color != guide)
    for r in range(1, len(base)):
        for c in range(len(base[0])):
            if missing_distractor[r][c] == distractor_color:
                missing_distractor[r][c] = 0
    mutations["missing_distractor"] = missing_distractor

    for name, grid in mutations.items():
        assert gen.self_check(grid), name


def test_negative_recombination_absent_guide_is_rejected_and_oracle_undefined() -> None:
    grid = gen.generate(510, 6, difficulty="hard")
    facts = gen._analyze(grid)
    absent = next(color for color in range(1, 10) if color not in facts["body_colors"])
    recombined = copy.deepcopy(grid)
    recombined[0][facts["marker_col"]] = absent
    assert absent not in {value for row in recombined[1:] for value in row}
    assert any("absent from the body" in error for error in gen.self_check(recombined))
    with pytest.raises(ValueError):
        gen.rule_mirror(recombined)


def test_determinism_fresh_returns_input_purity_and_global_rng() -> None:
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(55, 89, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(55, 89, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    frozen = copy.deepcopy(second)
    assert gen.rule_mirror(second) == gen.rule_mirror(second)
    assert second == frozen
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(55, 89, difficulty="hard") == frozen


def test_invalid_override_calls_reject_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=1)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(0, 0, grid_h=7)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(0, 0, marker_col=10)
