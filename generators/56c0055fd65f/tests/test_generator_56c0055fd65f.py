from __future__ import annotations

import copy
import importlib
import random

import pytest
from reviewer_support import canonical_pairs, find_root

GEN = importlib.import_module("puzzle_generators.per_puzzle.56c0055fd65f.generator")
ROOT = find_root(__file__)


def _canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(GEN.TASK_ID, root=ROOT)]


def test_rule_pin_and_canonical_inputs_are_accepted():
    assert GEN.RULE_HASH == "d0be87fb4806"
    inputs = _canonical_inputs()
    assert len(inputs) == 5
    assert all(GEN.self_check(grid) == [] for grid in inputs)


def test_all_bands_emit_every_branch_and_each_schedule_refutes_shortcuts():
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            rows = []
            for profile in GEN.SCHEDULE_PROFILES:
                grid = GEN.generate(seed, seed * 20 + profile, difficulty=band)
                assert GEN.self_check(grid) == []
                observed = GEN.semantic_observables(grid)
                assert observed["hole_counts"] == [0, 1, 2]
                rows.append((grid, GEN.rule_mirror(grid), observed))

            # At least two rows keep the strong same-area/same-box 0/1 witness,
            # so every 3-of-4 query rotation still contains one such example.
            assert sum(row[2]["equal_area_zero_one"] for row in rows) >= 2
            assert sum(row[2]["equal_bbox_zero_one"] for row in rows) >= 2
            for shortcut in GEN.CANONICAL_SHORTCUTS.values():
                assert any(shortcut(grid) != truth for grid, truth, _ in rows)


def test_profile_zero_replays_canonical_component_morphology():
    """The canonical-profile schedule must include the solid zero-hole case."""
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            grid = GEN.generate(seed, 0, difficulty=band)
            analysis = GEN._analysis(grid)
            by_holes = analysis["by_holes"]
            assert len(by_holes[0]) == 6
            assert sorted(GEN._bbox_dims(by_holes[0])) == [2, 3]
            assert len(by_holes[1]) == 8
            assert GEN._bbox_dims(by_holes[1]) == (3, 3)
            assert len(by_holes[2]) == 13
            assert sorted(GEN._bbox_dims(by_holes[2])) == [3, 5]
            truth = GEN.rule_mirror(grid)
            assert all(shortcut(grid) == truth for shortcut in GEN.CANONICAL_SHORTCUTS.values())


def test_shape_profile_does_not_fix_semantic_roles_to_one_layout():
    """Layout sampling must be independent of the four morphology profiles."""
    for profile in GEN.SCHEDULE_PROFILES:
        orders = set()
        has_interior_component = False
        for seed in range(40):
            grid = GEN.generate(seed, profile, difficulty="medium")
            analysis = GEN._analysis(grid)
            orders.add(analysis["position_order"])
            height, width = len(grid), len(grid[0])
            for component in analysis["components"]:
                r0, c0, r1, c1 = GEN._bbox(component)
                if r0 > 0 and c0 > 0 and r1 < height - 1 and c1 < width - 1:
                    has_interior_component = True
        assert len(orders) >= 3
        assert has_interior_component


def test_override_boundaries_are_exact_and_band_independent():
    for band in ("easy", "medium", "hard"):
        for height in (11, 18):
            for width in (11, 18):
                for include in (False, True):
                    grid = GEN.generate(
                        19,
                        7,
                        difficulty=band,
                        grid_h=height,
                        grid_w=width,
                        include_distractor=include,
                    )
                    assert GEN.self_check(grid) == []
                    assert GEN.observe_overrides(grid) == {
                        "grid_h": height,
                        "grid_w": width,
                        "include_distractor": include,
                    }


def test_unknown_override_rejects_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, difficulty="easy", typo_axis=3)


def test_replay_fresh_returns_and_global_rng_purity():
    random.seed(99173)
    before = random.getstate()
    first = GEN.generate(3, 8, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(3, 8, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert second[0][0] != 9


def test_declared_mutation_fixtures_are_rejected_without_mutation():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        frozen = copy.deepcopy(grid)
        errors = GEN.self_check(grid)
        assert errors, name
        assert grid == frozen, name


def test_three_demo_schedule_identifies_unseen_query_profile():
    for start in (0, 11, 22, 33):
        rows = []
        for offset in range(4):
            grid = GEN.generate(1234 + start, start + offset, difficulty="medium")
            rows.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(rows[:3], rows[3]) == []


def test_every_query_rotation_of_four_profile_lesson_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            start = seed * 7
            rows = []
            for offset in range(4):
                grid = GEN.generate(seed, start + offset, difficulty=band)
                rows.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for query_index, query in enumerate(rows):
                demos = [row for index, row in enumerate(rows) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []


def test_canonical_shortcuts_fit_canonical_but_generated_witness_refutes_them():
    for grid in _canonical_inputs():
        truth = GEN.rule_mirror(grid)
        for shortcut in GEN.CANONICAL_SHORTCUTS.values():
            assert shortcut(grid) == truth
    generated = GEN.generate(17, 3, difficulty="medium")
    truth = GEN.rule_mirror(generated)
    assert all(shortcut(generated) != truth for shortcut in GEN.CANONICAL_SHORTCUTS.values())
