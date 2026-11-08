from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.875ce5d835db.generator"
)


def test_rule_hash_and_all_canonical_pairs() -> None:
    assert gen.RULE_HASH == "d02a970277c5"
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._truth(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_self_check_rejects_targeted_impostors() -> None:
    valid = gen.generate(7001, 2, difficulty="medium")
    h, w = len(valid), len(valid[0])

    all_background = [[0 for _ in range(w)] for _ in range(h)]
    full_one_color = [[1 for _ in range(w)] for _ in range(h)]

    short_contiguous_line = [[0 for _ in range(w)] for _ in range(h)]
    for col, color in zip((1, 2, 3), (4, 5, 6)):
        short_contiguous_line[2][col] = color

    multi_marker_column = copy.deepcopy(valid)
    facts = gen._analyze(valid)
    col = facts["columns"][0]
    occupied = facts["rows"][0]
    other_row = next(row for row in range(h) if row != occupied)
    multi_marker_column[other_row][col] = 9

    invalid_color = copy.deepcopy(valid)
    invalid_color[0][0] = 12

    for name, impostor in {
        "all_background": all_background,
        "full_one_color": full_one_color,
        "short_contiguous_line": short_contiguous_line,
        "multi_marker_column": multi_marker_column,
        "invalid_color": invalid_color,
    }.items():
        assert gen.self_check(impostor), name


def test_negative_recombination_is_rejected_and_uses_new_feature() -> None:
    original = gen.generate(94117, 1, difficulty="medium")
    impostor = gen.negative_recombination_fixture()
    original_colors = {value for row in original for value in row if value}
    impostor_colors = {value for row in impostor for value in row if value}
    assert len(impostor_colors - original_colors) == 1
    assert any("contains 2 markers" in reason for reason in gen.self_check(impostor))


def test_exact_override_boundaries_are_observable() -> None:
    for band in ("easy", "medium", "hard"):
        for height in (5, 10):
            for width in (8, 14):
                for marker_count in (3, 6):
                    for color_mode in ("distinct", "repeat"):
                        grid = gen.generate(
                            20260729,
                            17,
                            difficulty=band,
                            grid_h=height,
                            grid_w=width,
                            marker_count=marker_count,
                            color_mode=color_mode,
                        )
                        assert gen.observe_overrides(grid) == {
                            "grid_h": height,
                            "grid_w": width,
                            "marker_count": marker_count,
                            "color_mode": color_mode,
                        }


def test_unknown_override_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, difficulty="easy", typo_axis="ignored")


def test_generation_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(42, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(42, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))


def test_canonical_anchor_schedule_and_every_sliding_window() -> None:
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in canonical_pairs(gen.TASK_ID)
    }
    for band in ("easy", "medium", "hard"):
        for anchor_index in (0, 4, 8, 12, 16):
            grid = gen.generate(55, anchor_index, difficulty=band)
            profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
            assert profile in canonical_profiles

        for start in range(len(gen.SCHEDULE_PROFILES)):
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(1000 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": gen._truth(grid)})
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_each_named_witness_kills_its_claimed_rival() -> None:
    grids = [gen.generate(8080, index, difficulty="medium") for index in range(4)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness = gen.SEMANTIC_WITNESSES[witness_name]
        firing = next(grid for grid in grids if witness(grid))
        truth = gen._truth(firing)
        assert any(gen.SEMANTIC_RIVALS[name](firing) != truth for name in rival_names)
