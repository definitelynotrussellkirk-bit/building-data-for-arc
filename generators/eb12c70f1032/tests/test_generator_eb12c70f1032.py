from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.eb12c70f1032 import generator as gen


ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row["task_id"] == gen.TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def _canonical_pairs():
    row = _canonical_row()
    return row["train"] + row["test"]


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            todo = [(row, col)]
            seen.add((row, col))
            cells = []
            while todo:
                cr, cc = todo.pop()
                cells.append((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)):
                    if (
                        0 <= nr < height and 0 <= nc < width
                        and (nr, nc) not in seen and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            result.append((min(c for _, c in cells), min(r for r, _ in cells), color, len(cells)))
    return sorted(result)


def _independent_oracle(grid):
    objects = _components(grid)
    height = max(size for _, _, _, size in objects)
    output = [[0] * (2 * len(objects) - 1) for _ in range(height)]
    for index, (_, _, color, size) in enumerate(objects):
        for row in range(height - size, height):
            output[row][2 * index] = color
    return output


def _code(profile):
    return gen.PROFILE_TO_CODE[profile]


def test_identity_version_and_rule_hash_pin():
    assert gen.GENERATOR_ID == gen.TASK_ID == "eb12c70f1032"
    assert gen.VERSION == "3.0.0"
    rule = " ".join(_canonical_row()["program_solution"].split())
    assert hashlib.sha256(rule.encode()).hexdigest()[:12] == gen.RULE_HASH


def test_canonical_inventory_and_profiles():
    row = _canonical_row()
    assert row["source"] == "bank:cedcb02251c0"
    assert len(row["train"]) == 3
    assert len(row["test"]) == 1
    assert len(_canonical_pairs()) == 4
    profiles = {
        gen.canonical_profile_signature(pair["input"])
        for pair in _canonical_pairs()
    }
    assert profiles == set(gen.PUBLIC_PROFILES)


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_every_canonical_pair_matches_independent_oracle(pair):
    original = copy.deepcopy(pair["input"])
    assert _independent_oracle(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original
    assert gen.self_check(pair["input"]) == []


@pytest.mark.parametrize("profile", gen.SCENE_PROFILES)
def test_every_scene_code_is_exact_and_observable(profile):
    code = _code(profile)
    grid = gen.generate(1000 + code, code, scene_code=code)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"scene_code": code}
    assert gen.rule_mirror(grid) == _independent_oracle(grid)
    if profile in gen.PUBLIC_PROFILES:
        assert gen.canonical_profile_signature(grid) == profile
    else:
        assert gen.canonical_profile_signature(grid) is None


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_balanced_schedule_covers_every_profile(difficulty):
    seen = set()
    for index in range(len(gen.SCENE_PROFILES)):
        grid = gen.generate(2000, index, difficulty=difficulty)
        seen.add(gen._analysis(grid)["scene_profile"])
    assert seen == set(gen.SCENE_PROFILES)


def test_public_schedule_variants_remain_complete_official_scenes():
    for index in range(240):
        grid = gen.generate(3000, index)
        profile = gen._analysis(grid)["scene_profile"]
        if profile in gen.PUBLIC_PROFILES:
            assert gen.canonical_family_signature(grid) == profile
            assert len(_components(grid)) == 3


def test_each_public_profile_has_250_unique_scheduled_variants():
    buckets = {profile: set() for profile in gen.PUBLIC_PROFILES}
    for index in range(5000):
        grid = gen.generate(index, index, difficulty="medium")
        profile = gen._analysis(grid)["scene_profile"]
        if profile in buckets:
            buckets[profile].add(tuple(map(tuple, grid)))
    assert {profile: len(values) for profile, values in buckets.items()} == {
        profile: 250 for profile in gen.PUBLIC_PROFILES
    }


def test_general_area_orders_counts_and_comparator_modes_are_covered():
    seen_counts = set()
    seen_modes = set()
    seen_orders = set()
    for profile in gen.GENERAL_PROFILES:
        grid = gen.generate(4000, _code(profile), scene_code=_code(profile))
        facts = gen._analysis(grid)["facts"]
        seen_counts.add(facts["object_count"])
        seen_modes.add(facts["order_mode"])
        seen_orders.add(facts["areas"])
    assert seen_counts == {2, 3, 4, 5}
    assert seen_modes == {"unique", "left_tie", "origin_tie"}
    assert len(seen_orders) == len(gen.GENERAL_PROFILES)


def test_tied_area_profile_is_intentional_and_not_collapsed():
    grid = gen.generate(5000, 0, scene_code=_code("tied_areas"))
    facts = gen._analysis(grid)["facts"]
    assert facts["areas"] == (4, 4, 7)
    assert len(set(facts["colors"])) == 3
    assert len({tuple(row) for row in gen.rule_mirror(grid)}) > 1


def test_left_edge_tie_is_resolved_by_top_edge():
    grid = gen.generate(5001, 0, scene_code=_code("left_edge_tie"))
    objects = gen._analysis(grid)["facts"]["components"]
    assert objects[0]["c1"] == objects[1]["c1"]
    assert objects[0]["r1"] < objects[1]["r1"]
    assert tuple(obj["size"] for obj in objects) == (3, 6, 8)


def test_origin_tie_is_resolved_by_color():
    grid = gen.generate(5002, 0, scene_code=_code("origin_tie"))
    objects = gen._analysis(grid)["facts"]["components"]
    assert (objects[0]["c1"], objects[0]["r1"]) == (objects[1]["c1"], objects[1]["r1"])
    assert objects[0]["color"] < objects[1]["color"]
    assert tuple(obj["size"] for obj in objects) == (3, 5, 8)


def test_bar_geometry_for_every_profile():
    for profile in gen.SCENE_PROFILES:
        grid = gen.generate(6000 + _code(profile), 0, scene_code=_code(profile))
        objects = _components(grid)
        output = gen.rule_mirror(grid)
        assert len(output) == max(size for _, _, _, size in objects)
        assert len(output[0]) == 2 * len(objects) - 1
        assert all(output[row][col] == 0 for row in range(len(output)) for col in range(1, len(output[0]), 2))


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(77123)
    state = random.getstate()
    first = gen.generate(7000, 11, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(7000, 11, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(7000, 11, difficulty="hard") == second


@pytest.mark.parametrize("bad", [
    [],
    [[]],
    [[0], [0, 0]],
    [[False] * 7 for _ in range(7)],
    [[10] * 7 for _ in range(7)],
    [[0] * 6 for _ in range(7)],
    [[0] * 27 for _ in range(7)],
])
def test_structurally_invalid_grids_fail_closed(bad):
    assert gen.self_check(bad)


def test_blank_single_object_and_too_many_objects_fail_closed():
    blank = [[0] * 8 for _ in range(8)]
    single = copy.deepcopy(blank)
    single[1][1] = single[1][2] = 2
    many = [[0] * 20 for _ in range(8)]
    for index in range(6):
        many[1][3 * index] = 1 + index
        many[2][3 * index] = 1 + index
    assert gen.self_check(blank)
    assert gen.self_check(single)
    assert gen.self_check(many)


def test_unknown_area_recombination_fails_closed():
    grid = gen.generate(8000, 0, scene_code=_code("trio_rise"))
    color = gen._analysis(grid)["facts"]["components"][0]["color"]
    row, col = gen._analysis(grid)["facts"]["components"][0]["cells"][0]
    mutated = copy.deepcopy(grid)
    # Removing one endpoint changes the declared (2,5,8) area relation.
    mutated[row][col] = 0
    assert gen.self_check(mutated)


def test_public_count_fragment_without_complete_core_is_not_canonical_like():
    grid = gen.generate(8001, 0, scene_code=_code("trio_peak"))
    assert len(_components(grid)) == 3
    assert gen.canonical_family_signature(grid) is None


@pytest.mark.parametrize("overrides", [
    {"scene_code": -1},
    {"scene_code": len(gen.SCENE_PROFILES)},
    {"unknown": 1},
])
def test_invalid_controls_raise(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(9000, 0, **overrides)


def test_unknown_difficulty_raises():
    with pytest.raises(ValueError):
        gen.generate(9001, 0, difficulty="extreme")


def test_rule_mirror_rejects_empty_foreground_and_preserves_input():
    grid = [[0] * 7 for _ in range(7)]
    with pytest.raises(ValueError):
        gen.rule_mirror(grid)
    sample = gen.generate(9002, 0, scene_code=_code("four_mixed"))
    original = copy.deepcopy(sample)
    gen.rule_mirror(sample)
    assert sample == original
