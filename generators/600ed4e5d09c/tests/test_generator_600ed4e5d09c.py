"""Source-bound regression tests for generator 600ed4e5d09c."""
from __future__ import annotations

import copy
import hashlib
import json

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK = "600ed4e5d09c"
ROOT = find_root(__file__)
GEN, _SOURCE, _SHA = load_selected_generator(TASK, root=ROOT)


def canonical_program():
    programs = set()
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            programs.add(row["program_solution"])
    assert len(programs) == 1
    return programs.pop()


def test_original_labels_match_python_mirror():
    for pair in canonical_pairs(TASK, root=ROOT, labeled_only=True):
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_generated_scenes_are_lawful_and_drop_the_spurious_bottom_left_anchor(difficulty):
    for index in range(12):
        grid = GEN.generate(1000 + index, index, difficulty=difficulty)
        assert grid[-1][0] == 0
        assert GEN.self_check(grid) == []
        output = GEN.rule_mirror(grid)
        assert output != grid
        assert len(output) == len(grid) and len(output[0]) == len(grid[0])


def test_dimension_and_palette_controls_are_live_and_strict():
    warm = GEN.generate(7, 0, grid_h=30, grid_w=30, palette_kind="warm")
    cool = GEN.generate(7, 0, grid_h=30, grid_w=30, palette_kind="cool")
    assert (len(warm), len(warm[0])) == (30, 30)
    assert (len(cool), len(cool[0])) == (30, 30)
    assert warm != cool
    assert {warm[0][0], GEN.frame_color(warm)} <= set(GEN.PALETTES["warm"])
    assert {cool[0][0], GEN.frame_color(cool)} <= set(GEN.PALETTES["cool"])


@pytest.mark.parametrize("kwargs", [
    {"grid_h": True}, {"grid_w": 31}, {"palette_kind": "bad"},
    {"palette_size": 3}, {"texture": "no_frame"}, {"difficulty": "expert"},
])
def test_invalid_and_dead_controls_fail_closed(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **kwargs)


def test_self_check_rejects_old_broken_anchor_and_semantic_damage():
    grid = GEN.generate(9, 2, difficulty="medium")
    old = copy.deepcopy(grid)
    old[-1][0] = GEN.frame_color(old)
    assert GEN.self_check(old)
    no_target = copy.deepcopy(grid)
    select = no_target[0][0]
    no_target[0][0] = 0
    for r, row in enumerate(no_target):
        for c, value in enumerate(row):
            if value == select:
                no_target[r][c] = 0
    assert GEN.self_check(no_target)


def test_rule_hash_matches_unique_canonical_program():
    source = canonical_program()
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert GEN.RULE_HASH == digest == "f96ec5618f89"
