from __future__ import annotations

import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


GEN = importlib.import_module("puzzle_generators.per_puzzle.9bd8e3019126.generator")


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_is_pinned_to_selected_canonical_source():
    assert GEN.RULE_HASH == canonical_rule_hash(GEN.TASK_ID)


def test_all_canonical_pairs_are_accepted_and_python_mirror_is_exact():
    pairs = canonical_pairs(GEN.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_every_sliding_four_demo_window_contains_all_relation_profiles():
    expected = set(GEN.SCHEDULE_PROFILES)
    assert GEN.EXAMPLES_NEEDED == 4
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            profiles = {
                GEN.observe_overrides(GEN.generate(700 + start, start + offset, difficulty=band))["profile"]
                for offset in range(GEN.EXAMPLES_NEEDED)
            }
            assert profiles == expected


def test_exact_override_axes_round_trip_at_boundaries_and_unknown_keys_reject():
    cases = (
        {"grid_h": 8, "grid_w": 11, "profile": "partial_same_bbox", "a_color": 1, "b_color": 1},
        {"grid_h": 9, "grid_w": 13, "profile": "partial_mismatched_bbox", "a_color": 9, "b_color": 2},
        {"grid_h": 8, "grid_w": 12, "profile": "a_subset_b", "a_color": 4, "b_color": 6},
        {"grid_h": 9, "grid_w": 11, "profile": "b_subset_a", "a_color": 7, "b_color": 3},
    )
    for index, overrides in enumerate(cases):
        grid = GEN.generate(810 + index, index, difficulty="hard", **overrides)
        assert GEN.observe_overrides(grid) == overrides
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, __override_contract_unknown_axis__=1)


def test_named_profile_discriminators_really_change_the_answer():
    grids = {
        profile: GEN.generate(900 + index, index, difficulty="hard", profile=profile)
        for index, profile in enumerate(GEN.SCHEDULE_PROFILES)
    }
    mismatch = grids["partial_mismatched_bbox"]
    assert GEN.rule_mirror(mismatch) != GEN.SEMANTIC_RIVALS[
        "center-align the two cropped shapes"
    ](mismatch)

    for profile in ("a_subset_b", "b_subset_a"):
        grid = grids[profile]
        assert GEN.rule_mirror(grid) != GEN.SEMANTIC_RIVALS[
            "use B-minus-A in the directional panel"
        ](grid)

    for grid in grids.values():
        assert GEN.rule_mirror(grid) != GEN.SEMANTIC_RIVALS[
            "keep every Boolean panel on the full shared canvas"
        ](grid)
        assert GEN.rule_mirror(grid) != GEN.SEMANTIC_RIVALS[
            "swap the union and intersection panels"
        ](grid)
        assert GEN.rule_mirror(grid) != GEN.SEMANTIC_RIVALS[
            "recolor four copies of A"
        ](grid)


def test_every_four_demo_lesson_refutes_all_named_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos = []
            for offset in range(GEN.EXAMPLES_NEEDED):
                grid = GEN.generate(1000 + start, start + offset, difficulty=band)
                demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
            query_grid = GEN.generate(
                2000 + start,
                start + GEN.EXAMPLES_NEEDED,
                difficulty=band,
            )
            query = {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []
            for competitor in GEN.LESSON_COMPETITORS.values():
                assert not all(
                    competitor(demo["input"]) == demo["output"] for demo in demos
                )


def test_structural_self_check_rejects_targeted_impostors():
    grid = GEN.generate(3000, 1, difficulty="medium")
    analysis = GEN._analyze(grid)
    components = analysis["components"]

    one_object = [row[:] for row in grid]
    for r, c in components[1]["cells"]:
        one_object[r][c] = 0
    assert any("exactly two" in reason for reason in GEN.self_check(one_object))

    three_objects = [row[:] for row in grid]
    used_colors = {analysis["a_color"], analysis["b_color"], 0}
    extra_color = next(color for color in range(1, 10) if color not in used_colors)
    occupied = {cell for component in components for cell in component["cells"]}
    target = next(
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if (r, c) not in occupied
        and all((r + dr, c + dc) not in occupied for dr, dc in GEN._DIRS4)
    )
    three_objects[target[0]][target[1]] = extra_color
    assert any("exactly two" in reason for reason in GEN.self_check(three_objects))

    ragged = [row[:] for row in grid]
    ragged[0] = ragged[0][:-1]
    assert GEN.self_check(ragged) == ["grid must be rectangular"]

    illegal_cell = [row[:] for row in grid]
    illegal_cell[0][0] = 10
    assert GEN.self_check(illegal_cell) == ["cells must be literal ARC integers 0..9"]

    boolean_cell = [row[:] for row in grid]
    boolean_cell[0][0] = True
    assert GEN.self_check(boolean_cell) == ["cells must be literal ARC integers 0..9"]


def test_generation_is_deterministic_fresh_and_preserves_process_global_rng():
    state_before = random.getstate()
    first = GEN.generate(4242, 3, difficulty="hard")
    state_after = random.getstate()
    assert state_after == state_before

    expected = _freeze(first)
    first[0][0] = (first[0][0] + 1) % 10
    second = GEN.generate(4242, 3, difficulty="hard")
    assert _freeze(second) == expected
    assert second is not first
    assert all(a is not b for a, b in zip(first, second))
