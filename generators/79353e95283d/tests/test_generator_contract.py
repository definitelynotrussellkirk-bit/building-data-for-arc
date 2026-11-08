"""Behavioral regressions for panel-AND teaching and override contracts."""
from __future__ import annotations

import importlib.util
import itertools
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


TASK = "79353e95283d"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("and_generator_under_test", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
STATES = {(0, 0), (0, 1), (1, 0), (1, 1)}


def states(grid):
    return {(row[c], row[c + 4]) for row in grid for c in range(3)}


def overlap(grid):
    return sum(row[c] == row[c + 4] == 1 for row in grid for c in range(3))


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_draws_teach_all_four_boolean_inputs(band):
    # Restoring identical-panel patterns or filling away a negative witness fails.
    for seed in range(40):
        for index in range(4):
            grid = GEN.generate(seed, index, difficulty=band)
            assert states(grid) == STATES, (band, seed, index)
            assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_rotated_four_pair_window_teaches_size_and_separator_independence(band):
    # Crossing axes prevents a spurious size/color correlation; every holdout
    # leaves both heights and both separator roles represented in demonstrations.
    for seed in range(8):
        for start in range(4):
            grids = [GEN.generate(seed, start+i, difficulty=band) for i in range(4)]
            assert {(len(g) == 3, g[0][3] == 5) for g in grids} == {
                (True, True), (True, False), (False, True), (False, False)}
            for held_out in range(4):
                demos = [g for i, g in enumerate(grids) if i != held_out]
                assert any(len(g) == 3 for g in demos)
                assert any(len(g) > 3 for g in demos)
                assert any(g[0][3] == 5 for g in demos)
                assert any(g[0][3] != 5 for g in demos)


@pytest.mark.parametrize("pattern", ["random", "blob", "stripes", "checker", "border", "diagonal"])
def test_pattern_proposals_keep_truth_witnesses_and_alias_is_equivalent(pattern):
    for seed in range(6):
        args = {"grid_h": 3, "sep_color": 5}
        grid = GEN.generate(seed, 0, panel_pattern=pattern, **args)
        assert states(grid) == STATES
        assert grid == GEN.generate(seed, 0, texture=pattern, **args)


@pytest.mark.parametrize("texture", [None, "no_aligned", "all_aligned", "same_panels"])
def test_shape_and_separator_overrides_work_in_every_branch(texture):
    for height, color in itertools.product([1, 3, 18], [2, 5, 9]):
        grid = GEN.generate(17, 3, grid_h=height, sep_color=color, texture=texture)
        assert len(grid) == height
        assert all(len(row) == 7 and row[3] == color for row in grid)
        assert GEN.self_check(grid) == []
        if texture == "no_aligned":
            assert overlap(grid) == 0
        elif texture == "all_aligned":
            assert overlap(grid) == 3*height
        elif texture == "same_panels":
            assert all(row[:3] == row[4:] for row in grid)


def test_minimum_overlap_honors_capacity_boundaries():
    for height in [1, 3, 18]:
        for minimum in [1, 3*height]:
            grid = GEN.generate(7, 0, grid_h=height, aligned_pairs_target=minimum)
            assert overlap(grid) >= minimum
        with pytest.raises(ValueError):
            GEN.generate(7, 0, grid_h=height, aligned_pairs_target=3*height+1)


@pytest.mark.parametrize("axis,value", [
    ("grid_h", True), ("grid_h", 3.5), ("grid_h", "3"),
    ("grid_h", 0), ("grid_h", 19), ("sep_color", 0),
    ("sep_color", 1), ("sep_color", 99), ("sep_color", 5.0),
    ("left_density", float("nan")), ("left_density", -0.1),
    ("right_density", 1.1), ("right_density", True),
    ("panel_pattern", "typo"), ("texture", "typo"),
    ("aligned_pairs_target", True), ("aligned_pairs_target", 0),
    ("unknown_axis", 1),
])
def test_bad_override_is_rejected(axis, value):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(0, 0, **{axis: value})


def test_none_overrides_are_absent_and_conflicting_aliases_are_rejected():
    expected = GEN.generate(4, 5)
    assert GEN.generate(4, 5, **dict.fromkeys(GEN.AXES)) == expected
    with pytest.raises(ValueError):
        GEN.generate(4, 5, panel_pattern="random", texture="checker")


@pytest.mark.parametrize("grid", [
    None, [], [[]], [[0]*7, [0]*6], [[0, 0, 0, 99, 0, 0, 0]],
    [[True, 0, 0, 5, 1, 0, 0]], [[1.0, 0, 0, 5, 1, 0, 0]],
    [[0, 0, 0, 5, 0, 0, 0]]*19,
])
def test_self_check_rejects_malformed_inputs_without_crashing(grid):
    assert GEN.self_check(grid)


def test_canonical_examples_remain_in_domain():
    for pair in canonical_pairs(TASK, root=ROOT):
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []


def test_lesson_hook_rejects_copy_shortcut_when_query_needs_and():
    # Hand-labeled equal-panel demonstrations fit copying; the query distinguishes it.
    demo = {"input": [[1, 0, 1, 5, 1, 0, 1]], "output": [[2, 0, 2]]}
    query = {"input": [[1, 0, 1, 5, 0, 1, 1]], "output": [[0, 0, 2]]}
    assert GEN.lesson_identifiable([demo, demo, demo], query)


def test_lesson_hook_accepts_literal_complete_truth_table_evidence():
    demo = {
        "input": [[0, 0, 1, 5, 0, 1, 0], [1, 0, 1, 5, 1, 0, 1]],
        "output": [[0, 0, 0], [2, 0, 2]],
    }
    # Same shape/sep keeps canonical profile rivals irrelevant to this query.
    query = {"input": [[1, 0, 1, 5, 0, 1, 1], [0, 1, 0, 5, 1, 1, 0]],
             "output": [[0, 0, 2], [0, 2, 0]]}
    assert GEN.lesson_identifiable([demo], query) == []


@pytest.mark.parametrize("call", [
    {"seed": True}, {"seed": False}, {"seed": 1.0}, {"seed": 1.75}, {"seed": "1"},
    {"sample_index": True}, {"sample_index": False}, {"sample_index": -1},
    {"difficulty": True}, {"difficulty": False}, {"difficulty": 0},
    {"difficulty": 1.0}, {"difficulty": "__invalid_difficulty__"},
])
def test_generate_rejects_invalid_top_level_call_scalars(call):
    arguments = {"seed": 991, "sample_index": 0, "difficulty": "easy"}
    arguments.update(call)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**arguments)


def test_retained_gray_separator_shortcut_counterexample_matches_generator_contract():
    """The canonical-fitting separator shortcut is refuted by an emitted case."""
    import hashlib
    import json

    evidence = json.loads((HOME / "counterexamples/gray-separator-only.json").read_text())
    source_hash = hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest()
    grid = evidence["input"]
    assert evidence["generator"]["sha256"] == source_hash
    assert GEN.generate(0, 2) == grid
    assert GEN.self_check(grid) == []
    assert GEN._boolean_rival(grid, mask=8) == evidence["intended_output_racket"]
    assert GEN._gray_separator_only(grid) == evidence["rival_output"]
    assert evidence["canonical_fit"]["all_fit"] is True
    assert evidence["disagrees"] is True
