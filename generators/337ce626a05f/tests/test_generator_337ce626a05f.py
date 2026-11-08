from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs
GEN = importlib.import_module("puzzle_generators.per_puzzle.337ce626a05f.generator")


def _erase_panel_object(grid, info, panel_index):
    left, right = info["panel_ranges"][panel_index]
    for row in grid:
        for col in range(left, right):
            if row[col] != 0:
                row[col] = 0


def _draw_shape(grid, info, panel_index, shape, color=2, row_offset=0, col_offset=0):
    left, _ = info["panel_ranges"][panel_index]
    for row, col in shape:
        grid[row_offset + row][left + col_offset + col] = color


def test_rule_hash_canonical_pairs_and_input_purity():
    assert GEN.RULE_HASH == "c75668610a13"
    pairs = canonical_pairs(GEN.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        frozen = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]
        assert grid == frozen


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_deterministic_fresh_returns_and_global_rng_purity(difficulty):
    state = random.getstate()
    for seed in range(30):
        sample_index = 1000 + seed
        first = GEN.generate(seed, sample_index, difficulty=difficulty)
        assert random.getstate() == state
        second = GEN.generate(seed, sample_index, difficulty=difficulty)
        assert random.getstate() == state
        assert first == second
        assert first is not second
        assert all(a is not b for a, b in zip(first, second))
        assert GEN.self_check(first) == []
        assert GEN.rule_mirror(first) != first


def test_every_declared_axis_boundary_and_value_is_observable():
    cases = [
        {"layout": value} for value in GEN._LAYOUTS
    ] + [
        {"grid_h": 8}, {"grid_h": 12},
        {"profile_height": 3}, {"profile_height": 7},
        {"profile_peak": 3}, {"profile_peak": 4},
        *({"profile_kind": value} for value in GEN._PROFILE_KINDS),
        {"color_mode": "all_distinct"}, {"color_mode": "majority_shared"},
    ]
    for index, overrides in enumerate(cases):
        grid = GEN.generate(20_000 + index, 17 + index, difficulty="medium", **overrides)
        observed = GEN.observe_overrides(grid)
        for name, value in overrides.items():
            assert observed[name] == value
        assert GEN.self_check(grid) == []

    all_axes = {
        "layout": "compact5",
        "grid_h": 12,
        "profile_height": 7,
        "profile_peak": 4,
        "profile_kind": "zig_down",
        "color_mode": "majority_shared",
    }
    grid = GEN.generate(29_999, 31, difficulty="hard", **all_axes)
    assert GEN.observe_overrides(grid) == all_axes


def test_unknown_override_fails_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis="ignored")


def test_majority_panels_share_profile_but_not_exact_shape():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(20):
            grid = GEN.generate(500 + sample_index, sample_index, difficulty=difficulty)
            obs = GEN.semantic_observables(grid)
            shapes = [obs["panel_shapes"][i] for i in obs["majority_indices"]]
            profiles = [obs["panel_profiles"][i] for i in obs["majority_indices"]]
            assert len(set(profiles)) == 1
            assert len(set(shapes)) == len(shapes)


def test_four_slot_lessons_are_identifiable_and_kill_named_rivals():
    for start in range(4):
        demos = []
        for offset in range(GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(9001, start + offset, difficulty="medium")
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query_grid = GEN.generate(9001, start + GEN.EXAMPLES_NEEDED, difficulty="medium")
        assert GEN.lesson_identifiable(demos, {"input": query_grid}) == []
        assert {GEN.schedule_profile(9001, start + offset) for offset in range(4)} == set(GEN.SCHEDULE_PROFILES)

    fired = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for sample_index in range(40):
        grid = GEN.generate(12_345 + sample_index, sample_index, difficulty="hard")
        truth = GEN.rule_mirror(grid)
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            if witness(grid):
                fired[name] += 1
                assert any(GEN.SEMANTIC_RIVALS[rival](grid) != truth for rival in GEN.WITNESS_RIVALS[name])
    assert all(count > 0 for count in fired.values())


def test_self_check_rejects_mutations_and_negative_recombination():
    base = GEN.generate(71, 0, difficulty="medium", layout="canonical3")
    info = GEN._analyze(base)

    broken_divider = copy.deepcopy(base)
    broken_divider[0][info["divider_columns"][0]] = 0
    assert GEN.self_check(broken_divider)

    blank_panel = copy.deepcopy(base)
    _erase_panel_object(blank_panel, info, 0)
    assert any("exactly one object" in msg for msg in GEN.self_check(blank_panel))

    multicolor = copy.deepcopy(base)
    cell = info["records"][0]["cells"][0]
    left = info["panel_ranges"][0][0]
    old = multicolor[cell[0]][left + cell[1]]
    multicolor[cell[0]][left + cell[1]] = 9 if old != 9 else 7
    assert any("not monochrome" in msg for msg in GEN.self_check(multicolor))

    second_component = copy.deepcopy(base)
    left, right = info["panel_ranges"][0]
    object_cells = {(r, c) for r, row in enumerate(second_component) for c in range(left, right) if row[c] != 0}
    candidate = next(
        (r, c)
        for r in range(len(second_component))
        for c in range(left, right)
        if second_component[r][c] == 0
        and all((r + dr, c + dc) not in object_cells for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)))
    )
    second_component[candidate[0]][candidate[1]] = 2
    assert any("exactly one object" in msg for msg in GEN.self_check(second_component))

    no_majority = copy.deepcopy(base)
    target = info["majority_indices"][0]
    _erase_panel_object(no_majority, info, target)
    _draw_shape(no_majority, info, target, ((0, 0),), color=2)
    assert any("strict-majority" in msg for msg in GEN.self_check(no_majority))
    with pytest.raises(ValueError, match="strict-majority"):
        GEN.rule_mirror(no_majority)

    hidden_consensus = copy.deepcopy(base)
    outlier = info["outlier_indices"][0]
    _erase_panel_object(hidden_consensus, info, outlier)
    _draw_shape(hidden_consensus, info, outlier, GEN._simple_shape(info["majority_profile"], 0), color=2)
    assert any("majority operation is hidden" in msg for msg in GEN.self_check(hidden_consensus))
