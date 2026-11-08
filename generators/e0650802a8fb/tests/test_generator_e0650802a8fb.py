"""Focused regression tests for the e0650802a8fb generator repair."""
from __future__ import annotations

import copy
import importlib
import importlib.util
from pathlib import Path
import random
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


try:
    GENERATOR = importlib.import_module(
        "puzzle_generators.per_puzzle.e0650802a8fb.generator"
    )
except ModuleNotFoundError:
    _path = Path(__file__).resolve().parents[1] / "generator.py"
    _spec = importlib.util.spec_from_file_location(
        "review_generator_e0650802a8fb", _path
    )
    assert _spec is not None and _spec.loader is not None
    GENERATOR = importlib.util.module_from_spec(_spec)
    sys.modules[_spec.name] = GENERATOR
    _spec.loader.exec_module(GENERATOR)


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": GENERATOR.rule_mirror(grid)}


def _positions(grid: list[list[int]], color: int) -> set[tuple[int, int]]:
    return {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }


def test_rule_hash_and_all_canonical_pairs_are_pinned_and_accepted() -> None:
    assert GENERATOR.RULE_HASH == "040cfb38300e"
    pairs = canonical_pairs(GENERATOR.TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    overlap_profiles = set()
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GENERATOR.self_check(pair["input"]) == []
        assert GENERATOR.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original
        overlap_profiles.add(GENERATOR._analyze(pair["input"])["scene_profile"])
    assert "endpoint_mixed" in overlap_profiles or "endpoint_overwrite" in overlap_profiles


def test_row_major_first_appearance_not_numeric_order_owns_crossings() -> None:
    grid = [[0] * 8 for _ in range(8)]
    # Row-major order is 9 then 2; both paths cross at (2, 2).
    grid[0][0] = grid[4][4] = 9
    grid[0][4] = grid[4][0] = 2
    output = GENERATOR.rule_mirror(grid)
    assert output[2][2] == 2
    assert GENERATOR._rival_numeric_ascending(grid)[2][2] == 9


def test_unknown_and_invalid_overrides_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GENERATOR.generate(1, 0, typo_axis="interior_cross")
    for overrides in (
        {"grid_h": 7},
        {"grid_w": 15},
        {"pair_count": 1},
        {"pair_count": True},
        {"scene_profile": "cross"},
    ):
        with pytest.raises(ValueError):
            GENERATOR.generate(1, 0, **overrides)


def test_every_axis_is_exact_and_observable_at_boundaries() -> None:
    cases = [
        {"grid_h": 8, "grid_w": 8, "pair_count": 2, "scene_profile": "disjoint"},
        {"grid_h": 8, "grid_w": 14, "pair_count": 4, "scene_profile": "interior_cross"},
        {"grid_h": 14, "grid_w": 8, "pair_count": 3, "scene_profile": "endpoint_overwrite"},
        {"grid_h": 14, "grid_w": 14, "pair_count": 4, "scene_profile": "endpoint_survive"},
        {"grid_h": 10, "grid_w": 12, "pair_count": 2, "scene_profile": "controls"},
    ]
    for index, overrides in enumerate(cases):
        grid = GENERATOR.generate(97, index, difficulty="hard", **overrides)
        assert GENERATOR.observe_overrides(grid) == overrides
        assert GENERATOR.self_check(grid, meta={"overrides": overrides}) == []


def test_five_sample_schedule_kills_every_named_rival_in_each_sliding_window() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(4):
            for start in range(5):
                demos = [
                    _pair(GENERATOR.generate(seed, start + offset, difficulty=band))
                    for offset in range(GENERATOR.EXAMPLES_NEEDED)
                ]
                query = _pair(
                    GENERATOR.generate(
                        seed,
                        start + GENERATOR.EXAMPLES_NEEDED,
                        difficulty=band,
                    )
                )
                profiles = {
                    GENERATOR.observe_overrides(pair["input"])["scene_profile"]
                    for pair in demos
                }
                assert profiles == set(GENERATOR.SCHEDULE_PROFILES)
                assert GENERATOR.lesson_identifiable(demos, query) == []
                for name, competitor in GENERATOR.LESSON_COMPETITORS.items():
                    assert any(
                        competitor(pair["input"]) != pair["output"]
                        for pair in demos
                    ), name


def test_control_profile_teaches_exactly_two_and_diagonal_conditions() -> None:
    grid = GENERATOR.generate(
        301,
        4,
        grid_h=10,
        grid_w=10,
        pair_count=3,
        scene_profile="controls",
    )
    analysis = GENERATOR._analyze(grid)
    assert len(analysis["axis_pairs"]) == 1
    assert len(analysis["singletons"]) == 1
    assert len(analysis["triples"]) == 1
    output = GENERATOR.rule_mirror(grid)
    for group in ("axis_pairs", "singletons", "triples"):
        for color in analysis[group]:
            assert _positions(output, color) == _positions(grid, color)
    assert GENERATOR._rival_fill_axis_pairs(grid) != output
    assert GENERATOR._rival_use_outermost_same_color_cells(grid) != output


def test_endpoint_profiles_cover_both_original_endpoint_outcomes() -> None:
    overwrite = GENERATOR.generate(
        811, 0, grid_h=10, grid_w=10, pair_count=2,
        scene_profile="endpoint_overwrite",
    )
    survive = GENERATOR.generate(
        811, 1, grid_h=10, grid_w=10, pair_count=2,
        scene_profile="endpoint_survive",
    )
    for grid, expected in ((overwrite, "overwrite"), (survive, "survive")):
        analysis = GENERATOR._analyze(grid)
        assert analysis["scene_profile"] == f"endpoint_{expected}"
        point, owner, other = analysis["endpoint_crossings"][0]
        result = GENERATOR.rule_mirror(grid)
        if expected == "overwrite":
            assert result[point[0]][point[1]] == other
        else:
            assert result[point[0]][point[1]] == owner


def test_self_check_rejects_rule_hiding_impostors() -> None:
    blank = [[0] * 8 for _ in range(8)]
    one_target = [[0] * 8 for _ in range(8)]
    one_target[0][0] = one_target[3][3] = 4
    axis_only = [[0] * 8 for _ in range(8)]
    axis_only[2][1] = axis_only[2][6] = 5
    singleton_mutation = GENERATOR.generate(19, 0, scene_profile="disjoint")
    first_color = next(v for row in singleton_mutation for v in row if v)
    hits = sorted(_positions(singleton_mutation, first_color))
    singleton_mutation[hits[-1][0]][hits[-1][1]] = 0
    for impostor in (blank, one_target, axis_only, singleton_mutation):
        assert GENERATOR.self_check(impostor)


def test_replay_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(6421)
    expected_global = [random.random() for _ in range(8)]
    random.seed(6421)

    first = GENERATOR.generate(31337, 17, difficulty="medium")
    second = GENERATOR.generate(31337, 17, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    first[0][0] = 9 if first[0][0] != 9 else 8
    third = GENERATOR.generate(31337, 17, difficulty="medium")
    assert third == second
    assert [random.random() for _ in range(8)] == expected_global


def test_rule_mirror_does_not_mutate_input() -> None:
    grid = GENERATOR.generate(51, 6, difficulty="hard")
    original = copy.deepcopy(grid)
    output = GENERATOR.rule_mirror(grid)
    assert grid == original
    assert output != grid


def test_controls_keep_the_selected_frame_when_only_one_dimension_is_overridden() -> None:
    grid = GENERATOR.generate(
        22,
        0,
        difficulty="easy",
        scene_profile="controls",
        grid_w=10,
    )
    assert len(grid[0]) == 10
    assert GENERATOR.observe_overrides(grid)["scene_profile"] == "controls"
    assert GENERATOR.self_check(grid) == []


def test_workspace_probe_checks_every_cyclic_lesson_start() -> None:
    probe_path = Path(__file__).resolve().parents[1] / "workspace" / "lesson_probe.py"
    spec = importlib.util.spec_from_file_location("e0650802a8fb_lesson_probe", probe_path)
    assert spec is not None and spec.loader is not None
    probe = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = probe
    spec.loader.exec_module(probe)

    report = probe.run_probe(seed_count=1, bands=("easy",))
    assert report["status"] == "pass"
    assert report["canonical"]["accepted"] == 5
    assert report["per_band"]["easy"]["windows"] == 5
    assert report["per_band"]["easy"]["profile_complete_windows"] == 5
    assert report["per_band"]["easy"]["rival_complete_windows"] == 5
