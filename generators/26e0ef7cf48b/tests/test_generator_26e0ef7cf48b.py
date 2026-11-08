from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

TASK = "26e0ef7cf48b"
MODULE = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/base/solutions/banks/40f7bd2c7916/S15_H6__26e0ef7cf48b.json"


def canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        return next(
            row
            for row in map(json.loads, handle)
            if row.get("task_id") == TASK
        )


def canonical_pairs():
    row = canonical_row()
    test = row["test"]
    return list(row["train"]) + ([test] if isinstance(test, dict) else list(test))


def test_canonical_pairs_rule_hash_and_selected_authority():
    row = canonical_row()
    source = row["program_solution"]
    normalized = " ".join(source.split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH
    base = json.loads(BASE.read_text())
    assert base["racket_target"]["target_code"] == source

    for pair in canonical_pairs():
        before = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_sequential_lesson_schedule_exposes_all_decisive_branches():
    for band in ("easy", "medium", "hard"):
        for seed in range(40):
            signatures = [
                MODULE.semantic_signature(
                    MODULE.generate(seed, sample_index, difficulty=band)
                )
                for sample_index in range(4)
            ]
            assert signatures[0]["blocked"]
            assert signatures[1]["clipped"]
            assert signatures[2]["overlap"]
            assert not signatures[3]["blocked"]
            assert not signatures[3]["clipped"]
            assert all(signature["valid"] for signature in signatures)
            assert all(signature["unique_3"] > 0 for signature in signatures)
            assert all(signature["unique_4"] > 0 for signature in signatures)


def test_every_exact_axis_boundary_is_observable_in_every_band():
    for band in ("easy", "medium", "hard"):
        for grid_h in (8, 24):
            for grid_w in (8, 24):
                for template_size in (3, 7):
                    for n_markers_3 in (1, 5):
                        for n_markers_4 in (1, 5):
                            expected = {
                                "grid_h": grid_h,
                                "grid_w": grid_w,
                                "template_size": template_size,
                                "n_markers_3": n_markers_3,
                                "n_markers_4": n_markers_4,
                            }
                            grid = MODULE.generate(
                                991,
                                2,
                                difficulty=band,
                                **expected,
                            )
                            assert MODULE.self_check(
                                grid, meta={"overrides": expected}
                            ) == []
                            assert MODULE.observe_overrides(grid) == expected


def test_self_check_rejects_targeted_semantic_impostors():
    grid = MODULE.generate(17, 0, difficulty="medium")

    no_template = copy.deepcopy(grid)
    for row in range(len(no_template)):
        for col in range(len(no_template[0])):
            if no_template[row][col] == 2:
                no_template[row][col] = 0
    assert any("template" in error for error in MODULE.self_check(no_template))

    no_color_4 = copy.deepcopy(grid)
    for row in range(len(no_color_4)):
        for col in range(len(no_color_4[0])):
            if no_color_4[row][col] == 4:
                no_color_4[row][col] = 0
    assert any("color-4" in error for error in MODULE.self_check(no_color_4))

    disconnected_template = copy.deepcopy(grid)
    template = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 2
    ]
    row, col = template[-1]
    disconnected_template[row][col] = 0
    target = next(
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if disconnected_template[r][c] == 0
        and all(abs(r - tr) + abs(c - tc) > 1 for tr, tc in template[:-1])
    )
    disconnected_template[target[0]][target[1]] = 2
    assert any("exactly one" in error for error in MODULE.self_check(disconnected_template))

    illegal_palette = copy.deepcopy(grid)
    zero = next(
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if illegal_palette[row][col] == 0
    )
    illegal_palette[zero[0]][zero[1]] = 6
    assert any("illegal input colors" in error for error in MODULE.self_check(illegal_palette))


def test_determinism_fresh_returns_global_rng_and_unknown_overrides():
    state = random.getstate()
    first = MODULE.generate(1234, 2, difficulty="hard")
    second = MODULE.generate(1234, 2, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 7
    assert second[0][0] != 7
    assert random.getstate() == state
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, texture="blocked")
    with pytest.raises(ValueError):
        MODULE.generate(1, 0, difficulty="expert")
