from __future__ import annotations

import copy
import importlib.util
import random
import sys
from pathlib import Path

import pytest


TASK_ID = "3e5b763caa3d"

# Bootstrap the portable reviewer helpers from either a full repository or the
# isolated runtime assembled by ``arcpuzzles check --stage task_tests``.
for ancestor in Path(__file__).resolve().parents:
    full_runtime = ancestor / "shared" / "runtime"
    if (full_runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(full_runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break
else:  # pragma: no cover - gives a useful import error in malformed packets
    raise RuntimeError("reviewer_support.py not found above task test")

from reviewer_support import canonical_pairs, find_root

ROOT = find_root(__file__)
GENERATOR_PATH = ROOT / "generators" / TASK_ID / "generator.py"
if not GENERATOR_PATH.is_file():
    GENERATOR_PATH = (
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    )
EXPECTED_RULE_HASH = "da67ea740136"
EXPECTED_AXES = {
    "grid_h",
    "grid_w",
    "axis_mode",
    "divider_color",
    "cells",
    "n_distinct_colors",
}
CANONICAL_PROFILES = {
    (7, 7, 7),
    (9, 7, 8),
    (8, 7, 6),
    (7, 9, 8),
    (9, 9, 7),
}


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        f"review_{TASK_ID}", GENERATOR_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict[str, list[list[int]]]]:
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return (
        len(grid),
        len(grid[0]),
        len({value for row in grid for value in row}),
    )


def _divider(grid: list[list[int]]) -> tuple[int, int]:
    h, w = len(grid), len(grid[0])
    hits = []
    for column in range(w):
        values = {grid[row][column] for row in range(h)}
        if len(values) == 1 and next(iter(values)) != 0:
            hits.append((column, next(iter(values))))
    assert len(hits) == 1
    return hits[0]


def test_selected_rule_contract_matches_every_canonical_pair():
    gen = _load_generator()

    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    assert set(gen.AXES) == EXPECTED_AXES
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS in ((), [])
    assert gen.EXAMPLES_NEEDED == 4

    for pair in _canonical_pairs():
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before, "rule_mirror mutated its input"


def test_exact_axes_are_observable_across_boundary_combinations():
    gen = _load_generator()
    cases = (
        {
            "grid_h": 7,
            "grid_w": 7,
            "axis_mode": "left",
            "divider_color": 1,
            "cells": 6,
            "n_distinct_colors": 4,
        },
        {
            "grid_h": 8,
            "grid_w": 9,
            "axis_mode": "center",
            "divider_color": 5,
            "cells": 9,
            "n_distinct_colors": 5,
        },
        {
            "grid_h": 9,
            "grid_w": 11,
            "axis_mode": "right",
            "divider_color": 9,
            "cells": 12,
            "n_distinct_colors": 6,
        },
    )

    for difficulty in (None, "easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = gen.generate(101 + index, 17 + index, difficulty=difficulty, **requested)
            assert gen.self_check(grid, difficulty=difficulty) == []
            assert gen.observe_overrides(grid) == requested
            assert gen.generate(
                101 + index, 17 + index, difficulty=difficulty, **requested
            ) == grid


def test_invalid_and_unknown_overrides_are_rejected():
    gen = _load_generator()
    bad_calls = (
        {"grid_h": 6},
        {"grid_h": True},
        {"grid_w": 8},
        {"axis_mode": "diagonal"},
        {"divider_color": 2},
        {"cells": 7},
        {"n_distinct_colors": 3},
        {"typo_axis": 1},
    )
    for kwargs in bad_calls:
        with pytest.raises((TypeError, ValueError), match=".+"):
            gen.generate(3, 4, **kwargs)

    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(3, 4, difficulty="impossible")


def test_self_check_rejects_rule_ambiguous_mutations():
    gen = _load_generator()
    legal = gen.generate(
        77,
        2,
        grid_h=7,
        grid_w=7,
        axis_mode="center",
        divider_color=5,
        cells=6,
        n_distinct_colors=4,
    )
    assert gen.self_check(legal) == []
    axis, divider_color = _divider(legal)

    no_divider = copy.deepcopy(legal)
    no_divider[0][axis] = 0

    right_side_content = copy.deepcopy(legal)
    right_side_content[0][axis + 1] = 4

    second_divider = copy.deepcopy(legal)
    for row in range(len(second_divider)):
        second_divider[row][0] = 8

    full_one_color = [[4 for _ in row] for row in legal]
    ragged = [row[:] for row in legal]
    ragged[-1].pop()

    fixtures = {
        "divider_gap": no_divider,
        "right_side_content": right_side_content,
        "second_uniform_full_column": second_divider,
        "full_one_color": full_one_color,
        "ragged": ragged,
    }
    for name, grid in fixtures.items():
        assert gen.self_check(grid), name

    # The intended divider itself remains a uniform, nonzero full-height line.
    assert all(row[axis] == divider_color for row in legal)


def test_default_schedule_hits_all_canonical_profiles_and_witnesses():
    gen = _load_generator()
    seen_profiles = set()
    seen_schedule_profiles = set()

    for difficulty in (None, "easy", "medium", "hard"):
        band_profiles = set()
        for sample_index in range(20):
            grid = gen.generate(20261007, sample_index, difficulty=difficulty)
            assert gen.self_check(grid, difficulty=difficulty) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen.rule_mirror(grid) != grid
            band_profiles.add(_profile(grid))
            seen_profiles.add(_profile(grid))
            profile_name = gen.schedule_profile(20261007, sample_index, difficulty)
            seen_schedule_profiles.add(profile_name)
            assert profile_name in gen.SCHEDULE_PROFILES
            assert any(predicate(grid) for predicate in gen.SEMANTIC_WITNESSES.values())
        assert band_profiles == CANONICAL_PROFILES

    assert seen_profiles == CANONICAL_PROFILES
    assert seen_schedule_profiles == set(gen.SCHEDULE_PROFILES)


def test_canonical_shortcuts_fit_official_pairs_but_each_four_demo_window_refutes_them():
    gen = _load_generator()
    canonical = _canonical_pairs()

    assert set(gen.CANONICAL_SHORTCUTS) == {
        "grid_center_axis",
        "fixed_gray_axis",
    }
    assert set(gen.LESSON_COMPETITORS) == set(gen.CANONICAL_SHORTCUTS)
    for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical), name

    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(717, sample_index, difficulty=difficulty)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                717, start + gen.EXAMPLES_NEEDED, difficulty=difficulty
            )
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(pair["input"]) != pair["output"] for pair in demos
                ), (difficulty, start, name)


def test_declared_witnesses_really_refute_their_named_rivals():
    gen = _load_generator()
    for sample_index in range(16):
        grid = gen.generate(4242, sample_index)
        official = gen.rule_mirror(grid)
        for witness_name, predicate in gen.SEMANTIC_WITNESSES.items():
            if not predicate(grid):
                continue
            rivals = gen.WITNESS_RIVALS[witness_name]
            assert any(
                gen.SEMANTIC_RIVALS[name](grid) != official for name in rivals
            ), witness_name


def test_generation_is_deterministic_and_does_not_touch_global_random_state():
    gen = _load_generator()
    first = gen.generate(991, 7, difficulty="hard")
    second = gen.generate(991, 7, difficulty="hard")
    assert first == second

    random.seed(123456)
    expected = [random.random() for _ in range(6)]
    random.seed(123456)
    gen.generate(991, 7, difficulty="hard")
    actual = [random.random() for _ in range(6)]
    assert actual == expected
