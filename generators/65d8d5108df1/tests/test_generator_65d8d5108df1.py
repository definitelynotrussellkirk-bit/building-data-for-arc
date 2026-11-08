from __future__ import annotations

import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK_ID = "65d8d5108df1"
ROOT = find_root(__file__)
gen, _SOURCE, _SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _controlled_grid(code: int) -> list[list[int]]:
    grid = [[0] * 10 for _ in range(9)]
    # Asymmetric template 1: [[1,0,0], [1,1,1]].
    grid[0][0] = 1
    grid[1][0] = 1
    grid[1][1] = 1
    grid[1][2] = 1
    # A second, unused library template keeps the public 2-template manifold.
    grid[4][8] = 3
    grid[-3][0] = 1
    grid[-2][0] = code
    grid[-1][0] = 7
    return grid


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_every_canonical_pair_are_owned_exactly():
    assert gen.RULE_HASH == "d178b58b9106"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_audited_exact_controls_are_consumed_on_every_seed():
    request = {
        "grid_h": 16,
        "grid_w": 20,
        "n_templates": 5,
        "n_commands": 5,
    }
    for seed in range(8):
        grid = gen.generate(seed, 0, difficulty="easy", **request)
        assert gen.observe_overrides(grid) == request
        assert gen.self_check(grid) == []

    one_command = gen.generate(
        8,
        3,
        grid_h=9,
        grid_w=10,
        n_templates=2,
        n_commands=1,
    )
    assert gen.observe_overrides(one_command) == {
        "grid_h": 9,
        "grid_w": 10,
        "n_templates": 2,
        "n_commands": 1,
    }

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __typo_axis__=1)
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, grid_h=True)
    with pytest.raises(ValueError):
        gen.generate(1, 0, n_templates=6)
    with pytest.raises(ValueError):
        gen.generate(1, 0, n_commands=0)


def test_transform_codes_4_5_6_match_canonical_table():
    assert gen.rule_mirror(_controlled_grid(4)) == [
        [0, 0, 7],
        [7, 7, 7],
    ]
    assert gen.rule_mirror(_controlled_grid(5)) == [
        [7, 7, 7],
        [7, 0, 0],
    ]
    assert gen.rule_mirror(_controlled_grid(6)) == [
        [0, 7],
        [0, 7],
        [7, 7],
    ]


def test_three_slot_schedule_exercises_4_5_6_and_kills_declared_rivals():
    for sample_index, expected_code in enumerate((4, 5, 6)):
        grid = gen.generate(
            919,
            sample_index,
            grid_h=9,
            grid_w=10,
            n_templates=2,
            n_commands=1,
        )
        assert gen.schedule_profile(919, sample_index) == expected_code
        active = [i for i, value in enumerate(grid[-3]) if value != 0]
        assert len(active) == 1
        assert grid[-2][active[0]] == expected_code
        truth = gen.rule_mirror(grid)
        for witness_name in ("transform_required", "canonical_code_table", "recolor_required"):
            assert gen.SEMANTIC_WITNESSES[witness_name](grid) is True
            for rival_name in gen.WITNESS_RIVALS[witness_name]:
                assert gen.SEMANTIC_RIVALS[rival_name](grid) != truth


def test_three_demo_schedule_is_identifiable_for_every_rotation_start():
    pairs = [_pair(gen.generate(7301, i, difficulty="medium")) for i in range(12)]
    for start in range(8):
        demos = pairs[start : start + gen.EXAMPLES_NEEDED]
        query = pairs[start + gen.EXAMPLES_NEEDED]
        assert {
            gen.schedule_profile(7301, start + offset, "medium")
            for offset in range(gen.EXAMPLES_NEEDED)
        } == set(gen.SCHEDULE_PROFILES)
        assert gen.lesson_identifiable(demos, query) == []


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(1234567)
    state = random.getstate()
    first = gen.generate(44, 3, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(44, 3, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert gen.generate(44, 3, difficulty="hard") == second


def test_self_check_rejects_broken_library_or_command_contracts():
    valid = gen.generate(808, 0, grid_h=9, grid_w=10, n_templates=2, n_commands=1)
    active = next(i for i, value in enumerate(valid[-3]) if value != 0)

    ragged = [row[:] for row in valid]
    ragged[-1] = ragged[-1][:-1]

    missing_id = [row[:] for row in valid]
    missing_id[-3][active] = 9
    while any(9 in row for row in missing_id[:-3]):
        for row in missing_id[:-3]:
            for c, value in enumerate(row):
                if value == 9:
                    row[c] = 8

    bad_transform = [row[:] for row in valid]
    bad_transform[-2][active] = 7

    inactive_payload = [row[:] for row in valid]
    inactive = next(i for i, value in enumerate(inactive_payload[-3]) if value == 0)
    inactive_payload[-2][inactive] = 2

    duplicate_library_color = [row[:] for row in valid]
    color = valid[-3][active]
    duplicate_library_color[5][9] = color

    for name, grid in {
        "ragged": ragged,
        "missing_id": missing_id,
        "bad_transform": bad_transform,
        "inactive_payload": inactive_payload,
        "duplicate_library_color": duplicate_library_color,
    }.items():
        assert gen.self_check(grid), f"broken contract accepted: {name}"


@pytest.mark.parametrize(
    ("seed", "sample_index"),
    [
        (True, 0),
        (1.0, 0),
        ("1", 0),
        (-1, 0),
        (1, True),
        (1, 1.0),
        (1, "1"),
        (1, -1),
    ],
)
def test_generate_rejects_non_integer_or_negative_call_indices(seed, sample_index):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, grid_h=9, grid_w=10, n_templates=2, n_commands=1)
