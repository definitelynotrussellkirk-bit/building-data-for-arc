from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.2db1f7f0392d.generator")


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs() -> None:
    assert gen.RULE_HASH == "d90c04209e45"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_self_check_rejects_targeted_impostors() -> None:
    valid = gen.generate(20260729, 6, difficulty="medium")
    assert gen.self_check(valid) == []

    broken_border = copy.deepcopy(valid)
    broken_border[0][1] = 0

    no_interior_walls = copy.deepcopy(valid)
    for row in range(1, len(valid) - 1):
        for col in range(1, len(valid[0]) - 1):
            if no_interior_walls[row][col] == 9:
                no_interior_walls[row][col] = 0

    duplicate_seed = copy.deepcopy(valid)
    seed_color = gen._seed_cells(valid)[0][2]
    empty = next(
        (row, col)
        for row in range(1, len(valid) - 1)
        for col in range(1, len(valid[0]) - 1)
        if duplicate_seed[row][col] == 0
    )
    duplicate_seed[empty[0]][empty[1]] = seed_color

    same_color_seeds = copy.deepcopy(valid)
    first, second = gen._seed_cells(same_color_seeds)
    same_color_seeds[second[0]][second[1]] = first[2]

    invalid_color = copy.deepcopy(valid)
    invalid_color[1][1] = 12

    for name, impostor in {
        "broken_border": broken_border,
        "no_interior_walls": no_interior_walls,
        "duplicate_seed": duplicate_seed,
        "same_color_seeds": same_color_seeds,
        "invalid_color": invalid_color,
    }.items():
        assert gen.self_check(impostor), name


def test_negative_recombination_is_rejected_but_oracle_domain_remains_executable() -> None:
    valid = gen.generate(991, 7, difficulty="hard")
    used = {value for row in valid for value in row}
    replacement = next(color for color in range(1, 9) if color not in used)
    mutant = copy.deepcopy(valid)
    interior_wall = next(
        (row, col)
        for row in range(1, len(valid) - 1)
        for col in range(1, len(valid[0]) - 1)
        if mutant[row][col] == 9
    )
    mutant[interior_wall[0]][interior_wall[1]] = replacement

    assert gen.self_check(mutant)
    output = gen.rule_mirror(mutant)
    assert len(output) == len(mutant)
    assert all(len(row) == len(mutant[0]) for row in output)


def test_all_exact_override_combinations_are_observable() -> None:
    for band in ("easy", "medium", "hard"):
        for height in (8, 12):
            for width in (10, 15):
                for layout in gen.DIVIDER_LAYOUTS:
                    for palette_kind in gen.PALETTE_KINDS:
                        grid = gen.generate(
                            112358,
                            7,
                            difficulty=band,
                            grid_h=height,
                            grid_w=width,
                            divider_layout=layout,
                            palette_kind=palette_kind,
                        )
                        assert gen.observe_overrides(grid) == {
                            "grid_h": height,
                            "grid_w": width,
                            "divider_layout": layout,
                            "palette_kind": palette_kind,
                        }
                        assert gen.self_check(grid) == []


def test_unknown_and_invalid_overrides_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="cross")
    with pytest.raises(ValueError, match="outside"):
        gen.generate(1, 0, grid_h=7)
    with pytest.raises(ValueError, match="not in options"):
        gen.generate(1, 0, divider_layout="diagonal")


def test_generation_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(8675309)
    before = random.getstate()
    first = gen.generate(42, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(42, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))


def test_every_generated_draw_kills_named_rivals_and_fires_all_witnesses() -> None:
    for band in ("easy", "medium", "hard"):
        for index in range(40):
            grid = gen.generate(50000 + index, index, difficulty=band)
            truth = gen.rule_mirror(grid)
            assert gen.self_check(grid) == []
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                assert witness(grid), (band, index, name)
            for name, rival in gen.SEMANTIC_RIVALS.items():
                assert rival(grid) != truth, (band, index, name)


def test_every_sliding_lesson_window_is_identifiable() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = [
                _pair(gen.generate(7000 + start, start + offset, difficulty=band))
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []
