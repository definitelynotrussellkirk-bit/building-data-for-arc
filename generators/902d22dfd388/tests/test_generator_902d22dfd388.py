"""Focused regression tests for generator 902d22dfd388."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

TASK_ID = "902d22dfd388"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.902d22dfd388.generator"
)


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical task not found: {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *tests]


def _frame(grid):
    frames = GEN._frame_bboxes(grid)
    assert len(frames) == 1
    return frames[0]


def test_rule_hash_canonical_pairs_input_purity_and_a_b_a_are_pinned():
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "3a6fc1c246e2"
    pairs = _canonical_pairs()
    assert len(pairs) == 3

    inputs_before = [copy.deepcopy(pair["input"]) for pair in pairs]
    outputs_a = []
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        outputs_a.append(GEN.rule_mirror(pair["input"]))
    outputs_b = [GEN.rule_mirror(pair["input"]) for pair in reversed(pairs)]
    outputs_a_again = [GEN.rule_mirror(pair["input"]) for pair in pairs]

    assert outputs_a == [pair["output"] for pair in pairs]
    assert outputs_b == [pair["output"] for pair in reversed(pairs)]
    assert outputs_a_again == outputs_a
    assert [pair["input"] for pair in pairs] == inputs_before


def test_canonical_shortcuts_are_characterized_truthfully():
    pairs = _canonical_pairs()
    train, test = pairs[:2], pairs[2]

    # Frame-relative centering fits both demonstrations but is killed by the
    # official query, whose frame is offset from the canvas centre.
    assert all(
        GEN._solve_frame_relative(pair["input"]) == pair["output"]
        for pair in train
    )
    assert GEN._solve_frame_relative(test["input"]) != test["output"]

    # Cropping every non-7 cell globally fits all canonical pairs because they
    # contain no outside distractors.  Generated controls must kill it.
    assert all(
        GEN._solve_global_non7(pair["input"]) == pair["output"]
        for pair in pairs
    )
    control = GEN.generate(44, 1, difficulty="easy")
    assert GEN.semantic_observables(control)["outside_control_present"] is True
    assert GEN._solve_global_non7(control) != GEN.rule_mirror(control)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_public_axis_boundary_product_is_exactly_observable(difficulty):
    case = 0
    for grid_h in (8, 14):
        for grid_w in (8, 14):
            for content_cells in (3, 8):
                for content_colors in (2, 3):
                    for outside_count in (0, 2):
                        requested = {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "content_cells": content_cells,
                            "content_colors": content_colors,
                            "outside_count": outside_count,
                        }
                        grid = GEN.generate(
                            1000 + case,
                            case % 13,
                            difficulty=difficulty,
                            **requested,
                        )
                        assert GEN.self_check(grid) == []
                        assert GEN.observe_overrides(grid) == requested
                        case += 1


def test_unknown_override_and_unknown_difficulty_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=7)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 0, difficulty="expert")


def test_self_check_rejects_six_targeted_structural_impostors():
    base = GEN.generate(303, 1, difficulty="medium")
    assert GEN.self_check(base) == []
    r1, c1, r2, c2 = _frame(base)

    # 1. Missing frame.
    missing = copy.deepcopy(base)
    for r in range(len(missing)):
        for c in range(len(missing[0])):
            if missing[r][c] == 7:
                missing[r][c] = 0
    assert GEN.self_check(missing)

    # 2. Broken frame outline.
    broken = copy.deepcopy(base)
    broken[r1][c1 + 1] = 0
    assert GEN.self_check(broken)

    # 3. Empty framed interior.
    empty = copy.deepcopy(base)
    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            empty[r][c] = 0
    assert any("3..8 cells" in error for error in GEN.self_check(empty))

    # 4. Single-colour content.
    monochrome = copy.deepcopy(base)
    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            if monochrome[r][c] not in (0, 7):
                monochrome[r][c] = 2
    assert any("2..3 colors" in error for error in GEN.self_check(monochrome))

    # 5. Three outside cells exceed the declared lawful manifold.
    too_many_outside = copy.deepcopy(base)
    outside_slots = [
        (r, c)
        for r in range(len(base))
        for c in range(len(base[0]))
        if not (r1 <= r <= r2 and c1 <= c <= c2)
        and too_many_outside[r][c] == 0
    ]
    for r, c in outside_slots[:3]:
        too_many_outside[r][c] = 9
    assert any("outside distractor count" in error for error in GEN.self_check(too_many_outside))

    # 6. A solid filled rectangle hides the crop/hole distinction.
    filled = copy.deepcopy(base)
    for r in range(r1 + 1, r2):
        for c in range(c1 + 1, c2):
            filled[r][c] = 0
    filled[r1 + 1][c1 + 1] = 2
    filled[r1 + 1][c1 + 2] = 3
    filled[r1 + 2][c1 + 1] = 3
    filled[r1 + 2][c1 + 2] = 2
    assert any("zero hole" in error for error in GEN.self_check(filled))


def test_every_sliding_three_profile_window_identifies_the_rule():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(len(GEN.SCHEDULE_PROFILES)):
            grids = [
                GEN.generate(404 + start, start + offset, difficulty=difficulty)
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            demos = [
                {"input": grid, "output": GEN.rule_mirror(grid)}
                for grid in grids[: GEN.EXAMPLES_NEEDED]
            ]
            query = {"input": grids[-1], "output": GEN.rule_mirror(grids[-1])}
            assert GEN.lesson_identifiable(demos, query) == []
            for rival_name in GEN.SEMANTIC_RIVALS:
                assert any(
                    GEN.SEMANTIC_RIVALS[rival_name](demo["input"]) != demo["output"]
                    for demo in demos
                ), (difficulty, start, rival_name)


def test_stationary_anchor_is_lawful_and_motion_is_not_required():
    grid = next(
        GEN.generate(505, index, difficulty="medium")
        for index in range(8)
        if GEN.schedule_profile(505, index, "medium") == "anchor_stationary"
    )
    observed = GEN.semantic_observables(grid)
    assert observed["crop_already_canvas_centered"] is True
    assert observed["visible_translation"] is False
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) != grid  # the frame is still removed


def test_replay_returns_fresh_objects_and_preserves_process_global_rng():
    random.seed(20260728)
    state = random.getstate()
    first = GEN.generate(606, 7, difficulty="hard")
    second = GEN.generate(606, 7, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
