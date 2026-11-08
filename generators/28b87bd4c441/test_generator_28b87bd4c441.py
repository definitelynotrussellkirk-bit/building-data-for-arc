from __future__ import annotations

import copy
import importlib

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.28b87bd4c441.generator")


def _canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(gen.TASK_ID)]


def test_canonical_inputs_are_owned_and_strict():
    inputs = _canonical_inputs()
    assert len(inputs) == 4
    for grid in inputs:
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


def test_every_profile_is_exactly_observable_and_deterministic():
    for profile in gen.PROFILE_NAMES:
        first = gen.generate(17, 4, difficulty="hard", scene_profile=profile)
        second = gen.generate(17, 4, difficulty="hard", scene_profile=profile)
        assert first == second
        assert first is not second
        assert gen.self_check(first, difficulty="hard") == []
        assert gen.observe_overrides(first) == {"scene_profile": profile}
        assert gen.rule_mirror(first) != first


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis="x")


def test_self_check_rejects_decisive_mutations():
    grid = gen.generate(3, 1, scene_profile="canonical_down_right_l4")

    missing_marker = copy.deepcopy(grid)
    for row in missing_marker:
        for c, value in enumerate(row):
            if value == 2:
                row[c] = 0
    assert any("marker" in error for error in gen.self_check(missing_marker))

    disconnected = copy.deepcopy(grid)
    blob = [(r, c) for r, row in enumerate(disconnected) for c, value in enumerate(row) if value == 5]
    r, c = blob[-1]
    disconnected[r][c] = 0
    disconnected[0][-1] = 5
    assert any("four-connected" in error for error in gen.self_check(disconnected))

    wrong_color = copy.deepcopy(grid)
    r, c = blob[0]
    wrong_color[r][c] = 3
    assert any("only colors" in error for error in gen.self_check(wrong_color))

    second_marker = copy.deepcopy(grid)
    for r, row in enumerate(second_marker):
        for c, value in enumerate(row):
            if value == 0:
                second_marker[r][c] = 2
                break
        else:
            continue
        break
    assert any("exactly one" in error for error in gen.self_check(second_marker))


def test_hollow_anchor_and_axis_profiles_kill_public_shortcuts():
    hollow = gen.generate(9, 2, scene_profile="row_left_hollow_l3")
    assert gen._witness_hollow_bbox_anchor(hollow)
    assert gen._rival_first_blob_cell_anchor(hollow) != gen.rule_mirror(hollow)
    assert gen._rival_diagonal_only(hollow) != gen.rule_mirror(hollow)


def test_full_profile_cycle_is_identifiable():
    seed = 0
    demos = []
    for sample_index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, sample_index)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(seed, gen.EXAMPLES_NEEDED)
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []
