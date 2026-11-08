from __future__ import annotations

import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

TASK_ID = "66fcab92de52"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_owned_exactly():
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "e36095ccf386"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 10
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_all_declared_overrides_round_trip_and_unknowns_reject():
    for h in (5, 7, 10):
        for w in (5, 8, 10):
            for corner in gen.CORNERS:
                grid = gen.generate(
                    20260815,
                    17,
                    difficulty="hard",
                    grid_h=h,
                    grid_w=w,
                    corner=corner,
                )
                assert gen.observe_overrides(grid) == {
                    "grid_h": h,
                    "grid_w": w,
                    "corner": corner,
                }
                assert gen.self_check(grid) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __typo_axis__=1)
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_h=4)
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_w=11)
    with pytest.raises(ValueError):
        gen.generate(1, 0, corner="center")


def test_four_demo_schedule_covers_all_corners_and_is_identifiable():
    for difficulty in ("easy", "medium", "hard"):
        pairs = []
        for sample_index in range(20):
            grid = gen.generate(7301, sample_index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid)["corner"] == gen.schedule_profile(
                7301, sample_index, difficulty
            )
            pairs.append(_pair(grid))

        for start in range(0, 15):
            demos = pairs[start : start + gen.EXAMPLES_NEEDED]
            query = pairs[start + gen.EXAMPLES_NEEDED]
            assert {
                gen.observe_overrides(pair["input"])["corner"] for pair in demos
            } == set(gen.CORNERS)
            assert gen.lesson_identifiable(demos, query) == []


def test_public_only_top_right_shortcut_is_real_and_generated_witness_kills_it():
    pairs = canonical_pairs(TASK_ID)
    assert all(gen.observe_overrides(pair["input"])["corner"] != "top_right" for pair in pairs)
    shortcut = gen.CANONICAL_SHORTCUTS["skip_top_right"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs)

    witness = gen.generate(987, 0, difficulty="easy", corner="top_right")
    assert gen.SEMANTIC_WITNESSES["corner_top_right"](witness)
    assert shortcut(witness) != gen.rule_mirror(witness)


def test_all_declared_semantic_rivals_are_killed_by_claimed_witnesses():
    witness_for = {
        "corner_top_left": "top_left",
        "corner_top_right": "top_right",
        "corner_bottom_left": "bottom_left",
        "corner_bottom_right": "bottom_right",
    }
    for witness_name, corner in witness_for.items():
        grid = gen.generate(555, 3, corner=corner)
        assert gen.SEMANTIC_WITNESSES[witness_name](grid)
        truth = gen.rule_mirror(grid)
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            assert gen.SEMANTIC_RIVALS[rival_name](grid) != truth


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(1234567)
    state = random.getstate()
    first = gen.generate(44, 3, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(44, 3, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert gen.generate(44, 3, difficulty="medium") == second


def test_self_check_rejects_structure_destroying_impostors():
    valid = gen.generate(808, 0, difficulty="easy", corner="top_left")
    analysis = gen._analyze(valid)
    bg = analysis["bg_color"]
    border = analysis["border_color"]

    impostors = {
        "singleton": [[border]],
        "solid_2x2": [[border, border], [border, border]],
        "short_line": [[border] * 5 for _ in range(5)],
    }

    missing_l_cell = [row[:] for row in valid]
    missing_l_cell[0][2] = bg
    impostors["missing_l_cell"] = missing_l_cell

    extra_interior_border = [row[:] for row in valid]
    extra_interior_border[2][2] = border
    impostors["extra_interior_border"] = extra_interior_border

    cyan_input = [row[:] for row in valid]
    cyan_input[2][2] = 8
    impostors["cyan_input"] = cyan_input

    third_color = [row[:] for row in valid]
    third = next(c for c in range(10) if c not in {bg, border, 8})
    third_color[2][2] = third
    impostors["third_color"] = third_color

    ragged = [row[:] for row in valid]
    ragged[-1] = ragged[-1][:-1]
    impostors["ragged"] = ragged

    for name, grid in impostors.items():
        assert gen.self_check(grid), f"impostor was accepted: {name}"


def test_every_named_difficulty_retains_an_exact_canonical_profile_anchor():
    profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({c for row in pair["input"] for c in row}))
        for pair in canonical_pairs(TASK_ID)
    }
    from scripts.canonical_profile_gate import _pinned_seed

    for difficulty in ("easy", "medium", "hard"):
        hits = 0
        for index in range(20):
            seed = _pinned_seed(TASK_ID, difficulty, index)
            sample_index = seed % 7919 + index
            grid = gen.generate(seed, sample_index, difficulty=difficulty)
            profile = (len(grid), len(grid[0]), len({c for row in grid for c in row}))
            hits += profile in profiles
        assert hits >= 1, f"{difficulty} lost all exact canonical-profile support"
