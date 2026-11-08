"""Regression and semantic-contract tests for b8078ba8f836."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from itertools import product
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "b8078ba8f836"
HOME = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def independent_rule(grid):
    out = [list(row) for row in grid]
    positions = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((r, c))
    for color, points in positions.items():
        if len(points) != 2:
            continue
        (r1, c1), (r2, c2) = points
        if r1 == r2:
            for c in range(min(c1, c2), max(c1, c2) + 1):
                out[r1][c] = color
        elif c1 == c2:
            for r in range(min(r1, r2), max(r1, r2) + 1):
                out[r][c1] = color
    return out


def pair(grid):
    return {"input": grid, "output": independent_rule(grid)}


def test_rule_pin_and_exact_axis_contract():
    assert GEN.RULE_HASH == "48fc6f20bbde"
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 3
    assert GEN.SCHEDULE_PROFILES == ("canonical", "counterexample")
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "n_horizontal_pairs",
        "n_vertical_pairs",
        "n_singletons",
        "distractor_profile",
    }


def test_all_canonical_inputs_are_accepted_and_match_rule_authority():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for item in pairs:
        assert GEN.self_check(item["input"]) == []
        assert GEN.strict_canonical_like(item["input"]) == []
        assert independent_rule(item["input"]) == item["output"]
        assert GEN.rule_mirror(item["input"]) == item["output"]


def test_declared_wrong_rules_fit_every_canonical_example():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    expected = {"connect_unaligned_L", "ignore_exact_count"}
    assert set(GEN.CANONICAL_SHORTCUTS) == expected
    assert set(GEN.SEMANTIC_RIVALS) == expected
    assert set(GEN.LESSON_COMPETITORS) == expected
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(item["input"]) == item["output"] for item in pairs), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": h,
            "grid_w": w,
            "n_horizontal_pairs": nh,
            "n_vertical_pairs": nv,
            "n_singletons": ns,
            "distractor_profile": profile,
        }
        for h, w, nh, nv, ns, profile in product(
            (8, 12), (8, 14), (1, 2), (1, 2), (0, 2), ("canonical", "counterexample")
        )
    ],
)
def test_boundary_overrides_are_constructive_exact_and_observable(band, overrides):
    grid = GEN.generate(183, 7, difficulty=band, **overrides)
    assert GEN.self_check(grid, difficulty=band) == []
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.rule_mirror(grid) == independent_rule(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"grid_h": 7},
        {"grid_h": 13},
        {"grid_w": 7},
        {"grid_w": 15},
        {"n_horizontal_pairs": 0},
        {"n_horizontal_pairs": 3},
        {"n_vertical_pairs": 0},
        {"n_vertical_pairs": 3},
        {"n_singletons": -1},
        {"n_singletons": 3},
        {"distractor_profile": "unknown"},
        {"grid_h": True},
        {"grid_w": 8.5},
        {"n_singletons": "1"},
        {"unknown_axis": 1},
        {"difficulty": "impossible"},
    ],
)
def test_invalid_controls_are_rejected(kwargs):
    kwargs = dict(kwargs)
    difficulty = kwargs.pop("difficulty", None)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, difficulty=difficulty, **kwargs)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_three_step_schedule_supplies_both_semantic_counterexamples(band):
    profiles = [GEN.schedule_profile(911, index, band) for index in range(9)]
    assert profiles == ["canonical", "counterexample", "counterexample"] * 3
    for index, profile in enumerate(profiles):
        grid = GEN.generate(911, index, difficulty=band)
        assert GEN.observe_overrides(grid)["distractor_profile"] == profile
        if profile == "counterexample":
            assert GEN.SEMANTIC_WITNESSES["unaligned_pair_ignored"](grid)
            assert GEN.SEMANTIC_WITNESSES["triplet_ignored"](grid)
            truth = independent_rule(grid)
            assert GEN.SEMANTIC_RIVALS["connect_unaligned_L"](grid) != truth
            assert GEN.SEMANTIC_RIVALS["ignore_exact_count"](grid) != truth


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_consecutive_four_window_and_query_rotation_refutes_all_rivals(band):
    for start in range(9):
        lesson = [pair(GEN.generate(1207 + start, start + offset, difficulty=band))
                  for offset in range(4)]
        for query_index, query in enumerate(lesson):
            demos = [item for index, item in enumerate(lesson) if index != query_index]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(item["input"]) != item["output"] for item in demos), (
                    band,
                    start,
                    query_index,
                    name,
                )


def test_generation_is_deterministic_fresh_and_helpers_are_pure():
    for band in (None, "easy", "medium", "hard"):
        for index in range(15):
            first = GEN.generate(77, index, difficulty=band)
            second = GEN.generate(77, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert GEN.self_check(first, difficulty=band) == []
            original = deepcopy(first)
            assert GEN.rule_mirror(first) == independent_rule(first)
            for fn in (
                *GEN.SEMANTIC_RIVALS.values(),
                *GEN.SEMANTIC_WITNESSES.values(),
            ):
                fn(first)
                assert first == original


def test_self_check_rejects_semantic_near_misses_but_accepts_color_role_swaps():
    good = GEN.generate(
        202,
        1,
        grid_h=10,
        grid_w=12,
        n_horizontal_pairs=1,
        n_vertical_pairs=1,
        n_singletons=1,
        distractor_profile="counterexample",
    )
    assert GEN.self_check(good) == []

    colors = sorted({value for row in good for value in row if value})
    a, b = colors[:2]
    swapped = [[b if value == a else a if value == b else value for value in row]
               for row in good]
    assert GEN.self_check(swapped) == []

    ragged = deepcopy(good)
    ragged[0].pop()
    assert GEN.self_check(ragged)

    bad_color = deepcopy(good)
    bad_color[0][0] = 10
    assert GEN.self_check(bad_color)

    positions = {}
    for r, row in enumerate(good):
        for c, value in enumerate(row):
            if value:
                positions.setdefault(value, []).append((r, c))
    pair_color, points = next((color, pts) for color, pts in positions.items()
                              if len(pts) == 2 and pts[0][0] == pts[1][0])
    too_many = deepcopy(good)
    free = next((r, c) for r, row in enumerate(too_many) for c, value in enumerate(row)
                if value == 0 and all(r != pr and c != pc for pr, pc in points))
    too_many[free[0]][free[1]] = pair_color
    assert GEN.self_check(too_many)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_population_has_strict_canonical_support_and_scene_diversity(band):
    grids = [GEN.generate(314, index, difficulty=band) for index in range(60)]
    strict = sum(not GEN.strict_canonical_like(grid) for grid in grids)
    assert strict >= 15
    observed = [GEN.observe_overrides(grid) for grid in grids]
    assert {item["distractor_profile"] for item in observed} == {
        "canonical",
        "counterexample",
    }
    assert len({tuple(tuple(row) for row in grid) for grid in grids}) >= 55


def test_retained_counterexample_refutes_both_canonical_shortcuts():
    import json

    fixture = json.loads((HOME / "counterexamples" / "exact_count_and_alignment.json").read_text())
    grid = fixture["input"]
    assert GEN.self_check(grid) == []
    assert GEN.rule_mirror(grid) == fixture["intended_output"]
    assert GEN.SEMANTIC_WITNESSES["unaligned_pair_ignored"](grid)
    assert GEN.SEMANTIC_WITNESSES["triplet_ignored"](grid)
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert rival(grid) == fixture["rival_outputs"][name]
        assert fixture["rival_outputs"][name] != fixture["intended_output"]
