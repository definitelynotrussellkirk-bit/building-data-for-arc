"""Portable regressions for the vertical-mirror curriculum.

The independent Python oracle below is intentionally tiny.  Racket remains the
label authority; these tests bind the generator surface, validator, schedule,
and declared rivals to the observable task geometry.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "c4155b3fcecd"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))


def _load_generator():
    spec = importlib.util.spec_from_file_location("reviewed_vertical_mirror_generator", GENERATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def oracle(grid):
    out = [list(row) for row in grid]
    width = len(out[0])
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                out[r][width - 1 - c] = value
    return out


def profile_tuple(grid):
    colors = {value for row in grid for value in row if value}
    return len(grid), len(grid[0]), len(colors)


def source_sides(grid):
    width = len(grid[0])
    sides = set()
    for row in grid:
        for col, value in enumerate(row):
            if not value:
                continue
            if col < width // 2:
                sides.add("left")
            elif col >= (width + 1) // 2:
                sides.add("right")
            else:
                sides.add("axis")
    return sides


def pair(seed, sample_index, band):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": oracle(grid)}


def test_rule_pin_and_all_canonical_pairs():
    assert gen.RULE_HASH == "e45306d2be09"
    assert len(PAIRS) == 4
    shortcut = gen.CANONICAL_SHORTCUTS["mirror_left_side_only"]
    for canonical in PAIRS:
        original = deepcopy(canonical["input"])
        assert gen.self_check(canonical["input"]) == []
        assert gen.rule_mirror(canonical["input"]) == canonical["output"]
        assert shortcut(canonical["input"]) == canonical["output"]
        assert canonical["input"] == original


def test_every_scene_profile_round_trips_and_unknown_axes_reject():
    assert set(gen.AXES) == {"scene_profile"}
    assert tuple(gen.SCHEDULE_PROFILES) == tuple(gen.SCENE_PROFILES)
    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(7100 + index, index, difficulty="easy", scene_profile=profile)
        assert gen.self_check(grid, meta={"overrides": {"scene_profile": profile}}) == []
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == oracle(grid)
    with pytest.raises(ValueError):
        gen.generate(0, 0, typo_axis=1)
    with pytest.raises(ValueError):
        gen.generate(0, 0, scene_profile="not-a-profile")
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="impossible")


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_hits_canonical_profile_and_all_rotations_teach_both_sides(band):
    canonical_profiles = {profile_tuple(item["input"]) for item in PAIRS}
    samples = [pair(1701, index, band) for index in range(20)]
    assert any(profile_tuple(item["input"]) in canonical_profiles for item in samples)

    period = len(gen._PROFILES_BY_BAND[band])
    for start in range(period):
        window = [pair(3301, start + offset, band) for offset in range(gen.EXAMPLES_NEEDED + 1)]
        for query_index in range(len(window)):
            query = window[query_index]
            demos = window[:query_index] + window[query_index + 1 :]
            assert {side for demo in demos for side in source_sides(demo["input"])} == {"left", "right"}
            assert gen.lesson_identifiable(demos, query) == []


def test_right_side_witness_refutes_canonical_left_only_shortcut():
    shortcut = gen.CANONICAL_SHORTCUTS["mirror_left_side_only"]
    assert all(shortcut(item["input"]) == item["output"] for item in PAIRS)
    witnesses = []
    for band in ("easy", "medium", "hard"):
        for index in range(len(gen._PROFILES_BY_BAND[band])):
            grid = gen.generate(8800, index, difficulty=band)
            if "right" in source_sides(grid):
                witnesses.append(grid)
    assert witnesses
    assert all(shortcut(grid) != oracle(grid) for grid in witnesses)


def test_every_declared_witness_is_real_and_refutes_its_claimed_rivals():
    grids = [
        gen.generate(9900 + index, index, difficulty=band)
        for band in ("easy", "medium", "hard")
        for index in range(len(gen._PROFILES_BY_BAND[band]))
    ]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        candidates = [grid for grid in grids if gen.SEMANTIC_WITNESSES[witness_name](grid)]
        assert candidates, witness_name
        for rival_name in rival_names:
            rival = gen.SEMANTIC_RIVALS[rival_name]
            assert any(rival(grid) != oracle(grid) for grid in candidates), (witness_name, rival_name)


def test_self_check_rejects_non_singletons_axis_cells_and_mirror_collisions():
    adjacent = [[0] * 7 for _ in range(5)]
    adjacent[1][1] = 2
    adjacent[1][2] = 3
    assert gen.self_check(adjacent)

    on_axis = [[0] * 7 for _ in range(5)]
    on_axis[1][1] = 2
    on_axis[3][3] = 3
    assert gen.self_check(on_axis)

    mirror_pair = [[0] * 7 for _ in range(5)]
    mirror_pair[1][1] = 2
    mirror_pair[1][5] = 3
    assert gen.self_check(mirror_pair)

    one_seed = [[0] * 7 for _ in range(5)]
    one_seed[1][1] = 2
    assert gen.self_check(one_seed)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 7 for _ in range(5)], [[10] * 7 for _ in range(5)]],
)
def test_malformed_inputs_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_generation_is_deterministic_and_does_not_touch_global_random_state():
    random.seed(431)
    before = random.getstate()
    first = gen.generate(12345, 17, difficulty="hard")
    after = random.getstate()
    second = gen.generate(12345, 17, difficulty="hard")
    assert before == after
    assert first == second
