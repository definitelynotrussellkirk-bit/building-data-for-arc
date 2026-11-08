from __future__ import annotations

import copy
import random
from reviewer_support import canonical_pairs, find_root, load_selected_generator


gen, _source, _source_sha = load_selected_generator("fa3550d200a0", root=find_root(__file__))


def _canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(
        gen.TASK_ID, root=find_root(__file__), labeled_only=True)]


def test_canonical_inputs_pass_structural_self_check():
    inputs = _canonical_inputs()
    assert len(inputs) == 8
    assert all(gen.self_check(grid) == [] for grid in inputs)


def test_exact_override_boundaries_are_observable():
    overrides = {
        "grid_h": 20,
        "grid_w": 24,
        "piece_count": 5,
        "decoy_count": 1,
        "rect_h": 6,
        "rect_w": 6,
        "canvas_side": "right",
        "palette_kind": "primary",
    }
    for seed in range(8):
        grid = gen.generate(seed, 3, difficulty="hard", **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    before = random.getstate()
    first = gen.generate(137, 11, difficulty="medium")
    second = gen.generate(137, 11, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert random.getstate() == before


def test_sequential_lesson_schedule_exposes_decoy_contrast_and_count_range():
    observed = [
        gen.observe_overrides(gen.generate(91, sample_index, difficulty="medium"))
        for sample_index in range(4)
    ]
    assert [row["piece_count"] for row in observed] == [2, 3, 4, 5]
    assert [row["decoy_count"] for row in observed] == [1, 0, 1, 0]
    assert {row["canvas_side"] for row in observed} <= {"left", "right"}


def test_self_check_rejects_four_targeted_impostors():
    original = gen.generate(
        222,
        0,
        difficulty="hard",
        piece_count=3,
        decoy_count=1,
        rect_h=8,
        rect_w=8,
    )
    features, errors = gen._analyze(original)
    assert errors == []

    top, left, bottom, right = features["canvas_bbox"]
    canvas = features["canvas_color"]
    marker_color = next(iter(features["marker_positions"]))

    # 1. Punch a zero hole in the otherwise filled canvas rectangle.
    hole = copy.deepcopy(original)
    hole_cell = next(
        (row, col)
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
        if hole[row][col] == canvas
    )
    hole[hole_cell[0]][hole_cell[1]] = 0
    assert any("zero hole" in error for error in gen.self_check(hole))

    # 2. Duplicate an inside marker color, making its anchor ambiguous.
    duplicate = copy.deepcopy(original)
    duplicate_cell = next(
        (row, col)
        for row in range(top + 1, bottom)
        for col in range(left + 1, right)
        if duplicate[row][col] == canvas
    )
    duplicate[duplicate_cell[0]][duplicate_cell[1]] = marker_color
    assert any("exactly once" in error for error in gen.self_check(duplicate))

    # 3. Remove one matched outside object, leaving a canvas marker unmatched.
    missing_piece = copy.deepcopy(original)
    matched_record = next(record for record in features["piece_records"] if record[0] == "matched")
    for row, col, _value in matched_record[2]:
        missing_piece[row][col] = 0
    assert any("without exactly one matched" in error for error in gen.self_check(missing_piece))

    # 4. Add a second special color to a matched object instead of payload 2.
    extra_special = copy.deepcopy(original)
    used = {value for row in original for value in row}
    replacement = next(color for color in range(1, 10) if color not in used and color != 2)
    payload_cell = next((row, col) for row, col, value in matched_record[2] if value == 2)
    extra_special[payload_cell[0]][payload_cell[1]] = replacement
    assert any("exactly one special marker" in error for error in gen.self_check(extra_special))
