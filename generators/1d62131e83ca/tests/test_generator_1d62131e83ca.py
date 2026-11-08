from __future__ import annotations

import copy
import importlib

from reviewer_support import canonical_pairs, find_root

gen = importlib.import_module("puzzle_generators.per_puzzle.1d62131e83ca.generator")


ROOT = find_root(__file__)


def _canonical_row():
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT, variant=0, labeled_only=True)
    return {
        split: [
            {"input": pair["input"], "output": pair["output"]}
            for pair in pairs
            if pair["split"] == split
        ]
        for split in ("train", "test")
    }


def _blank(height=10, width=10):
    return [[0 for _ in range(width)] for _ in range(height)]


def _paint_block(grid, row, col, color):
    for drow in (0, 1):
        for dcol in (0, 1):
            grid[row + drow][col + dcol] = color


def test_rule_hash_and_all_canonical_pairs():
    assert gen.RULE_HASH == "7a695100f4e0"
    row = _canonical_row()
    pairs = list(row["train"]) + list(row["test"])
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_defaults_are_deterministic_fresh_and_structural():
    for band in ("easy", "medium", "hard"):
        for seed in range(25):
            grid = gen.generate(seed, seed * 19 + 5, difficulty=band)
            replay = gen.generate(seed, seed * 19 + 5, difficulty=band)
            assert grid == replay
            assert grid is not replay
            assert all(left is not right for left, right in zip(grid, replay))
            assert gen.self_check(grid, difficulty=band) == []
            assert gen.rule_mirror(grid) != grid


def test_exact_semantic_overrides_are_observable():
    witnessed = set()
    for relative in gen.RELATIVE_POSITIONS:
        for balance in gen.TRAIL_BALANCES:
            for seed in range(40):
                try:
                    grid = gen.generate(
                        seed,
                        seed + 100,
                        difficulty="medium",
                        relative_position=relative,
                        trail_balance=balance,
                    )
                except ValueError:
                    continue
                observed = gen.observe_overrides(grid)
                assert observed["relative_position"] == relative
                assert observed["trail_balance"] == balance
                assert gen.self_check(
                    grid,
                    meta={
                        "overrides": {
                            "relative_position": relative,
                            "trail_balance": balance,
                        }
                    },
                ) == []
                witnessed.add((relative, balance))
                break
    assert witnessed == {
        (relative, balance)
        for relative in gen.RELATIVE_POSITIONS
        for balance in gen.TRAIL_BALANCES
    }


def test_self_check_rejects_targeted_impostors():
    valid = gen.generate(901, 17, difficulty="medium")

    missing_blue_cell = copy.deepcopy(valid)
    blue_cells = [
        (r, c)
        for r, row in enumerate(missing_blue_cell)
        for c, value in enumerate(row)
        if value == 1
    ]
    r, c = blue_cells[0]
    missing_blue_cell[r][c] = 0
    assert any("color 1" in message for message in gen.self_check(missing_blue_cell))

    extra_foreground_color = copy.deepcopy(valid)
    for r, row in enumerate(extra_foreground_color):
        for c, value in enumerate(row):
            if value == 0:
                extra_foreground_color[r][c] = 7
                break
        else:
            continue
        break
    assert any("unexpected colors" in message for message in gen.self_check(extra_foreground_color))

    same_row_origins = _blank()
    _paint_block(same_row_origins, 3, 1, 1)
    _paint_block(same_row_origins, 3, 6, 2)
    assert any("differ in both row and column" in message for message in gen.self_check(same_row_origins))

    ray_through_source = _blank(8, 8)
    _paint_block(ray_through_source, 4, 4, 1)
    _paint_block(ray_through_source, 1, 1, 2)
    messages = gen.self_check(ray_through_source)
    assert any("ray would pass through" in message for message in messages)

    empty_blue_ray = _blank()
    _paint_block(empty_blue_ray, 0, 3, 1)
    _paint_block(empty_blue_ray, 5, 1, 2)
    assert any("nonempty up-left ray" in message for message in gen.self_check(empty_blue_ray))


def test_dimension_boundaries_or_loud_incompatibility():
    for band in ("easy", "medium", "hard"):
        for height in (6, 18):
            for width in (6, 18):
                for seed in range(5):
                    grid = gen.generate(
                        seed,
                        seed * 7,
                        difficulty=band,
                        grid_h=height,
                        grid_w=width,
                    )
                    assert (len(grid), len(grid[0])) == (height, width)
                    assert gen.self_check(grid) == []
