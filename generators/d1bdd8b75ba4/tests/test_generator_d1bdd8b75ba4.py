from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.d1bdd8b75ba4 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


def _count_map(grid):
    out = {}
    for row in grid:
        for value in row:
            if value:
                out[value] = out.get(value, 0) + 1
    return out


def test_rule_hash_and_canonical_inputs_are_owned():
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID)
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_every_declared_scene_profile_round_trips_exactly():
    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(7000 + index, index, scene_profile=profile)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {"scene_profile": profile}


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="ignored-before-repair")


def test_every_four_demo_window_has_all_decisive_profile_kinds():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            profiles = [gen.schedule_profile(123, start + offset, band) for offset in range(4)]
            kinds = {profile.split("_", 1)[1] for profile in profiles}
            assert kinds == set(gen._PROFILE_KINDS)


def test_compact_runner_refutes_connected_component_shortcut():
    for band in ("easy", "medium", "hard"):
        profile = f"{gen._BAND_PREFIX[band]}_mid_gap1_compact_runner"
        grid = gen.generate(4242, 3, difficulty=band, scene_profile=profile)
        assert gen._compact_runner(grid)
        assert gen._rival_largest_component(grid) != gen.rule_mirror(grid)


def test_connected_profiles_keep_canonical_three_object_morphology():
    for band in ("easy", "medium", "hard"):
        profile = f"{gen._BAND_PREFIX[band]}_mid_gap2_connected"
        grid = gen.generate(31337, 1, difficulty=band, scene_profile=profile)
        counts = _count_map(grid)
        assert len(counts) == 3
        assert all(len(gen._components_for_color(grid, color)) == 1 for color in counts)


def test_self_check_rejects_targeted_impostors():
    base = gen.generate(9001, 0, difficulty="easy", scene_profile="e_low_gap1_connected")

    # 1. Remove one entire color: no longer the three-color task grammar.
    one_missing = copy.deepcopy(base)
    smallest = min(_count_map(one_missing), key=_count_map(one_missing).get)
    for row in one_missing:
        for c, value in enumerate(row):
            if value == smallest:
                row[c] = 0
    assert gen.self_check(one_missing)

    # 2. Force a tie between the winner and runner-up.
    tied = copy.deepcopy(base)
    counts = _count_map(tied)
    ranked = sorted(counts, key=lambda color: (-counts[color], color))
    winner, runner = ranked[:2]
    for r, row in enumerate(tied):
        for c, value in enumerate(row):
            if value == winner:
                row[c] = 0
                assert gen.self_check(tied)
                break
        else:
            continue
        break

    # 3. Use a non-ARC cell value.
    invalid_cell = copy.deepcopy(base)
    invalid_cell[0][0] = 12
    assert gen.self_check(invalid_cell)

    # 4. Eliminate literal background entirely.
    no_background = [[1 for _ in row] for row in base]
    assert gen.self_check(no_background)


def test_determinism_fresh_return_and_global_rng_purity():
    state = random.getstate()
    a = gen.generate(123456, 17, difficulty="hard")
    after = random.getstate()
    b = gen.generate(123456, 17, difficulty="hard")
    assert state == after == random.getstate()
    assert a == b
    assert a is not b
    assert all(row_a is not row_b for row_a, row_b in zip(a, b))
    a[0][0] = 9 if a[0][0] != 9 else 8
    assert a != b


def test_four_generated_demos_identify_named_rivals():
    for band in ("easy", "medium", "hard"):
        demos = []
        for sample_index in range(4):
            grid = gen.generate(2026, sample_index, difficulty=band)
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(2026, 4, difficulty=band)
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
