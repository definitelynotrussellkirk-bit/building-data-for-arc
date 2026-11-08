"""Focused contract tests for 95be702ec4db."""
from __future__ import annotations

import copy
import hashlib
import json
import random

import pytest
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "95be702ec4db"
ROOT = find_root(__file__)
CANONICAL = canonical_path(ROOT)
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _canonical_row() -> dict:
    for line in CANONICAL.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def test_rule_hash_and_every_canonical_input_are_accepted():
    row = _canonical_row()
    canonical = row["program_solution"]
    expected = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == expected
    for split in ("train", "test"):
        pairs = row[split] if isinstance(row[split], list) else [row[split]]
        for pair in pairs:
            original = copy.deepcopy(pair["input"])
            assert GEN.self_check(pair["input"]) == []
            assert pair["input"] == original


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_generation_is_deterministic_valid_and_global_rng_pure(difficulty):
    random.seed(5119)
    before = random.getstate()
    first = GEN.generate(17, 2, difficulty=difficulty)
    after = random.getstate()
    second = GEN.generate(17, 2, difficulty=difficulty)
    assert before == after
    assert first == second
    assert first is not second and first[0] is not second[0]
    assert GEN.self_check(first) == []


def test_n_frames_and_width_overrides_are_strict_and_observable():
    for n_frames, width in ((3, 18), (3, 22), (4, 27), (5, 30)):
        grid = GEN.generate(41, 0, difficulty="medium", n_frames=n_frames, grid_w=width)
        assert len(grid[0]) == width
        assert len(GEN._frame_facts(grid)) == n_frames
        assert GEN.self_check(grid) == []
    for case in (
        {"n_frames": 2},
        {"n_frames": 6},
        {"n_frames": True},
        {"grid_w": 17, "n_frames": 3},
        {"grid_w": 29, "n_frames": 5},
        {"grid_h": "9"},
        {"unknown_axis": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(41, 0, difficulty="medium", **case)


def test_self_check_rejects_broken_border_empty_frame_and_two_shape_colors():
    grid = GEN.generate(77, 0, difficulty="medium", n_frames=3, grid_w=22)
    facts = GEN._frame_facts(grid)

    broken = copy.deepcopy(grid)
    r0, c0, _, _ = facts[0]["bbox"]
    broken[r0][c0 + 2] = 0

    empty = copy.deepcopy(grid)
    for r, c in facts[1]["inner_cells"]:
        empty[r][c] = 0

    two_colors = copy.deepcopy(grid)
    r, c = next(iter(facts[2]["shape_cells"]))
    two_colors[r][c] = 8 if two_colors[r][c] != 8 else 7

    assert GEN.self_check(broken)
    assert GEN.self_check(empty)
    assert GEN.self_check(two_colors)
