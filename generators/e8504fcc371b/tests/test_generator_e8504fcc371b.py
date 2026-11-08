"""Focused regressions for the Commanded Trail generator."""
from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import os
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "e8504fcc371b"
ROOT = find_root(__file__)


def _load_module():
    module, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    return module


mod = _load_module()


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _command_and_seed(grid):
    commands = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in (1, 2, 3, 4)
    ]
    seeds = [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value in (5, 6, 7, 8, 9)
    ]
    assert len(commands) == len(seeds) == 1
    return commands[0], seeds[0]


def test_rule_hash_version_and_exact_axis_surface_are_pinned():
    assert mod.VERSION == "3.1.0"
    assert mod.RULE_HASH == "72176e994d8a"
    assert set(mod.AXES) == {
        "grid_h",
        "grid_w",
        "code",
        "seed_color",
        "trail_profile",
        "command_relation",
    }


def test_all_canonical_inputs_pass_and_python_mirror_matches_outputs():
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = [[int(value) for value in row] if isinstance(row, str) else list(row) for row in copy.deepcopy(pair["input"])]
        assert mod.self_check(source) == []
        pristine = copy.deepcopy(source)
        assert source == pristine, "self_check mutated canonical input"
        assert mod.strict_canonical_like(source) == []
        expected = [[int(value) for value in row] if isinstance(row, str) else list(row) for row in pair["output"]]
        assert mod._rule_mirror(source) == expected
        assert source == pristine, "rule mirror mutated canonical input"


def test_four_demo_schedule_covers_all_codes_and_both_relations_before_query():
    for seed in range(12):
        grids = [mod.generate(seed, index, difficulty="medium") for index in range(8)]
        observed = [mod.observe_overrides(grid) for grid in grids]
        codes = [item["code"] for item in observed]
        relations = [item["command_relation"] for item in observed]
        assert set(codes[:4]) == {1, 2, 3, 4}
        assert set(relations[:4]) == set(mod.COMMAND_RELATIONS)
        assert set(zip(codes, relations)) == {
            (code, relation)
            for code in (1, 2, 3, 4)
            for relation in mod.COMMAND_RELATIONS
        }
        assert codes[4] == codes[0]
        assert relations[4] != relations[0]
        demos = [{"input": grid, "output": mod._rule_mirror(grid)} for grid in grids[:4]]
        query = {"input": grids[4], "output": mod._rule_mirror(grids[4])}
        assert mod.lesson_identifiable(demos, query) == []



def test_every_four_demo_lesson_refutes_marker_geometry_hybrid():
    def hybrid(grid):
        observed = mod.observe_overrides(grid)
        code = observed["code"]
        direction = code if code in (2, 4) or observed["command_relation"] == "behind_seed" else 4
        return mod._paint_direction(grid, direction)

    for seed in range(12):
        demos = [mod.generate(seed, index, difficulty="medium") for index in range(4)]
        assert any(hybrid(grid) != mod._rule_mirror(grid) for grid in demos)

def test_every_single_axis_boundary_is_exact_in_every_band():
    cases = (
        {"grid_h": 4},
        {"grid_h": 10},
        {"grid_w": 6},
        {"grid_w": 14},
        {"code": 1},
        {"code": 4},
        {"seed_color": 5},
        {"seed_color": 9},
        {"trail_profile": "short"},
        {"trail_profile": "medium"},
        {"trail_profile": "long"},
        {"command_relation": "behind_seed"},
        {"command_relation": "off_axis"},
    )
    for band in ("easy", "medium", "hard"):
        for index, case in enumerate(cases):
            grid = mod.generate(
                9000 + index,
                7000 + index,
                difficulty=band,
                **case,
            )
            observed = mod.observe_overrides(grid)
            assert mod.self_check(grid) == []
            for axis, expected in case.items():
                assert observed[axis] == expected, (band, case, observed)


def test_incompatible_axes_reject_loudly():
    with pytest.raises(ValueError, match="trail_profile='medium' is infeasible"):
        mod.generate(
            1,
            0,
            difficulty="easy",
            grid_h=4,
            code=1,
            trail_profile="medium",
            command_relation="behind_seed",
        )
    with pytest.raises(ValueError, match="cannot be combined"):
        mod.generate(1, 0, texture="no_cmd", code=1)
    with pytest.raises(ValueError, match="unsupported override"):
        mod.generate(1, 0, invented_axis=True)


def test_self_check_rejects_targeted_semantic_impostors():
    lawful = mod.generate(77, 11, difficulty="medium", code=1, seed_color=6)
    assert mod.self_check(lawful) == []
    command, seed = _command_and_seed(lawful)

    missing_command = copy.deepcopy(lawful)
    missing_command[command[0]][command[1]] = 0
    assert mod.self_check(missing_command)

    missing_seed = copy.deepcopy(lawful)
    missing_seed[seed[0]][seed[1]] = 0
    assert mod.self_check(missing_seed)

    command_on_ray = copy.deepcopy(lawful)
    command_on_ray[command[0]][command[1]] = 0
    command_on_ray[seed[0] - 1][seed[1]] = 1
    assert mod.self_check(command_on_ray)

    zero_length = copy.deepcopy(lawful)
    zero_length[seed[0]][seed[1]] = 0
    zero_length[0][seed[1]] = seed[2]
    assert mod.self_check(zero_length)

    unused_replacement = next(color for color in range(5, 10) if color != seed[2])
    absent_replacement = copy.deepcopy(lawful)
    assert all(unused_replacement not in row for row in absent_replacement)
    absent_replacement[command[0]][command[1]] = unused_replacement
    assert mod.self_check(absent_replacement)

    invalid_arc_color = copy.deepcopy(lawful)
    invalid_arc_color[0][0] = 10
    assert mod.self_check(invalid_arc_color)


def test_degenerate_textures_are_distinct_and_rejected():
    seen = set()
    for texture in mod.DEGENERATE_TEXTURES:
        grid = mod.generate(5, 6, difficulty="medium", texture=texture)
        assert mod.self_check(grid), texture
        seen.add(tuple(map(tuple, grid)))
    assert len(seen) == len(mod.DEGENERATE_TEXTURES)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(78123)
    state = random.getstate()
    first = mod.generate(77, 31, difficulty="hard")
    pristine = copy.deepcopy(first)
    second = mod.generate(77, 31, difficulty="hard")
    assert state == random.getstate()
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert mod.generate(77, 31, difficulty="hard") == pristine


def test_semantic_witnesses_all_fire_in_each_band():
    for band in ("easy", "medium", "hard"):
        hits = {name: 0 for name in mod.SEMANTIC_WITNESSES}
        for index in range(200):
            grid = mod.generate(100_000 + index, 40_000 + 2 * index, difficulty=band)
            for name, predicate in mod.SEMANTIC_WITNESSES.items():
                hits[name] += bool(predicate(grid))
        assert all(count > 0 for count in hits.values()), (band, hits)
