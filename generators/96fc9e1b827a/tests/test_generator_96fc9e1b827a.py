from __future__ import annotations

import copy
import importlib
import importlib.util
import itertools
import random

import pytest

from puzzle_generators import base
gen = importlib.import_module("puzzle_generators.per_puzzle.96fc9e1b827a.generator")
from reviewer_support import canonical_pairs, find_root


def _canonical_pairs():
    return canonical_pairs(gen.TASK_ID, root=find_root(__file__), labeled_only=True)


def _labeled_generated(seed: int, start: int, difficulty: str):
    pairs = []
    for offset in range(4):
        grid = gen.generate(seed, start + offset, difficulty=difficulty)
        pairs.append({"input": grid, "output": gen.solve_intended(grid)})
    return pairs


def test_rule_hash_is_pinned_to_current_authority():
    assert gen.RULE_HASH == "0fb26a20e01c"


def test_canonical_inputs_are_accepted_and_strict():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.solve_intended(grid) == pair["output"]


def test_declared_canonical_shortcuts_really_fit_all_canonical_labels():
    pairs = _canonical_pairs()
    assert {"leftmost_object", "largest_bbox_area", "widest_object"} <= set(
        gen.CANONICAL_SHORTCUTS
    )
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(copy.deepcopy(pair["input"])) == pair["output"] for pair in pairs), name


def test_all_override_combinations_are_constructive_and_observable():
    axis_values = {
        "grid_h": (10, 18),
        "grid_w": (17, 24),
        "target_shape": ("c_shape", "staircase", "pyramid", "irregular"),
        "target_slot": ("left", "right", "bottom"),
        "distractor_style": ("compact", "shortcut"),
    }
    keys = tuple(axis_values)
    for index, values in enumerate(itertools.product(*(axis_values[key] for key in keys))):
        overrides = dict(zip(keys, values))
        grid = gen.generate(10_000 + index, 20_000 + index, difficulty="easy", **overrides)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        assert gen.observe_overrides(grid) == overrides


def test_unknown_and_badly_typed_overrides_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, misspelled_axis=1)
    with pytest.raises((TypeError, ValueError), match="grid_h"):
        gen.generate(0, 0, grid_h=True)
    with pytest.raises((TypeError, ValueError), match="target_shape"):
        gen.generate(0, 0, target_shape=3)


def test_default_schedule_has_profile_support_and_shortcut_counterexamples():
    expected_profiles = {(10, 17, 4), (10, 18, 4), (11, 18, 4)}
    for difficulty in ("easy", "medium", "hard"):
        for start in (0, 12, 24):
            grids = [gen.generate(777, start + offset, difficulty=difficulty) for offset in range(4)]
            signatures = {
                (len(grid), len(grid[0]), len({value for row in grid for value in row}))
                for grid in grids
            }
            assert signatures & expected_profiles
            assert any(gen.strict_canonical_like(grid) == [] for grid in grids)
            for name, rival in gen.CANONICAL_SHORTCUTS.items():
                assert any(rival(grid) != gen.solve_intended(grid) for grid in grids), name


def test_each_four_pair_lesson_is_identifiable_under_every_query_rotation():
    for difficulty in ("easy", "medium", "hard"):
        for start in (0, 11, 22, 33):
            pairs = _labeled_generated(91_337, start, difficulty)
            assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, pairs[query_index]) == []


def test_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert gen.self_check(copy.deepcopy(grid)), name


def test_generation_is_replayable_fresh_and_global_rng_pure():
    random.seed(991)
    before = random.getstate()
    first = gen.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = gen.generate(42, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


def test_default_draw_provenance_matches_observed_axes():
    for difficulty in ("easy", "medium", "hard"):
        for offset in range(12):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = gen.generate(80_000 + offset, 300 + offset, difficulty=difficulty)
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            assert captured[0].recorded_draws() == gen.observe_overrides(grid)
            assert captured[0].overrides_used() == {}


def test_workspace_shortcut_probe_replays_declared_rivals_and_witnesses():
    root = find_root(__file__)
    probe_path = (
        root
        / "generators"
        / gen.TASK_ID
        / "workspace"
        / "probe_shortcuts.py"
    )
    spec = importlib.util.spec_from_file_location("probe_shortcuts", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.build_report(seed=91_337, starts=range(4))
    assert report["task_id"] == gen.TASK_ID
    assert report["rule_hash"] == gen.RULE_HASH
    assert set(report["canonical_shortcuts"]) == set(gen.CANONICAL_SHORTCUTS)
    assert all(
        evidence["fits_count"] == evidence["canonical_pair_count"] == 3
        for evidence in report["canonical_shortcuts"].values()
    )
    assert set(report["generated_witnesses"]) == set(gen.CANONICAL_SHORTCUTS)
    for name, witness in report["generated_witnesses"].items():
        grid = witness["input"]
        assert gen.self_check(grid) == [], name
        assert gen.solve_intended(grid) == witness["intended_output"]
        assert gen.CANONICAL_SHORTCUTS[name](grid) == witness["rival_output"]
        assert witness["intended_output"] != witness["rival_output"]
        assert witness["difficulty"] in {"easy", "medium", "hard"}
