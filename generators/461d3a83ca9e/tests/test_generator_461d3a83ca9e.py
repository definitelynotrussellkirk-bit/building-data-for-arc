from __future__ import annotations

import importlib
import random
import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "461d3a83ca9e"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.461d3a83ca9e.generator"
)


def _canonical_pairs():
    return canonical_pairs(TASK_ID)


def _generated_pair(seed: int, sample_index: int, difficulty: str):
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_accepted_and_mirrored():
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "953a9d167b9c"
    assert len(_canonical_pairs()) == 5
    for pair in _canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_exact_override_boundaries_round_trip_and_bad_inputs_reject():
    for height in (9, 16):
        for width in (9, 18):
            for n_walls in (1, 3):
                grid = gen.generate(
                    2718,
                    height * 100 + width * 10 + n_walls,
                    difficulty="hard",
                    grid_h=height,
                    grid_w=width,
                    n_walls=n_walls,
                )
                assert gen.observe_overrides(grid) == {
                    "grid_h": height,
                    "grid_w": width,
                    "n_walls": n_walls,
                }
                assert gen.self_check(grid) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __typo_axis=3)
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 0, difficulty="extreme")


def test_four_slot_schedule_realizes_every_decisive_branch_without_overlap():
    grids = [gen.generate(12345, index, difficulty="medium") for index in range(4)]
    analyses = [gen._analysis(grid) for grid in grids]

    assert [gen.schedule_profile(12345, index, "medium") for index in range(4)] == list(
        gen.SCHEDULE_PROFILES
    )
    assert gen.strict_canonical_like(grids[0]) == []
    assert analyses[0]["has_wall_block"]
    assert gen.strict_canonical_like(grids[1]) == []
    assert not analyses[1]["has_wall_block"]
    assert analyses[2]["has_emitter_block"]
    assert not analyses[2]["has_wall_block"]
    assert analyses[3]["has_wall_block"]
    assert all(not analysis["has_overlap"] for analysis in analyses)


def test_every_consecutive_four_demo_window_is_identifiable_in_each_band():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(4):
            demos = [
                _generated_pair(8675309, index, difficulty)
                for index in range(start, start + gen.EXAMPLES_NEEDED)
            ]
            query = _generated_pair(8675309, start + gen.EXAMPLES_NEEDED, difficulty)
            assert gen.lesson_identifiable(demos, query) == []


def test_all_named_rivals_are_refuted_by_the_scheduled_witnesses():
    grids = [gen.generate(4242, index, difficulty="hard") for index in range(4)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness_grids = [
            grid for grid in grids if gen.SEMANTIC_WITNESSES[witness_name](grid)
        ]
        assert witness_grids, witness_name
        for grid in witness_grids:
            official = gen.rule_mirror(grid)
            assert any(
                gen.SEMANTIC_RIVALS[rival_name](grid) != official
                for rival_name in rival_names
            )


def test_self_check_rejects_four_structural_impostors():
    base = gen.generate(777, 0, difficulty="medium")
    emitter_cells = [
        (row, col, value)
        for row, values in enumerate(base)
        for col, value in enumerate(values)
        if value not in (0, 5)
    ]

    no_walls = [[0 if value == 5 else value for value in row] for row in base]

    duplicate_colors = [row[:] for row in base]
    first, second = emitter_cells
    duplicate_colors[second[0]][second[1]] = first[2]

    third_emitter = [row[:] for row in base]
    absent = next(color for color in range(1, 10) if color not in {5, first[2], second[2]})
    background = next(
        (row, col)
        for row, values in enumerate(third_emitter)
        for col, value in enumerate(values)
        if value == 0
    )
    third_emitter[background[0]][background[1]] = absent

    split_wall = [row[:] for row in base]
    components = gen._wall_components(
        {
            (row, col)
            for row, values in enumerate(split_wall)
            for col, value in enumerate(values)
            if value == 5
        }
    )
    component = sorted(max(components, key=len))
    removed = component[len(component) // 2]
    split_wall[removed[0]][removed[1]] = 0

    for impostor in (no_walls, duplicate_colors, third_emitter, split_wall):
        assert gen.self_check(impostor)


def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    random.seed(20260815)
    state_before = random.getstate()
    first = gen.generate(314159, 2, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(314159, 2, difficulty="hard")

    assert state_after == state_before
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    original = second[0][0]
    first[0][0] = 9 if original != 9 else 8
    third = gen.generate(314159, 2, difficulty="hard")
    assert third == second
