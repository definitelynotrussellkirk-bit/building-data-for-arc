"""Focused regression tests for generator f6875586326b."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
gen = importlib.import_module("puzzle_generators.per_puzzle.f6875586326b.generator")


def _canonical_row():
    with (REPO / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def _base_solution():
    return json.loads(
        (REPO / "data/base/solutions/training/178fcbfb__f6875586326b.json").read_text()
    )


def _find_empty(grid, *, row=None, col=None):
    for r, values in enumerate(grid):
        if row is not None and r != row:
            continue
        for c, value in enumerate(values):
            if col is not None and c != col:
                continue
            if value == 0:
                return r, c
    raise AssertionError("no empty cell matching constraint")


def test_rule_hash_authority_and_all_canonical_pairs():
    row = _canonical_row()
    canonical = row["program_solution"]
    actual_hash = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == actual_hash == "52315007f5e3"

    base = _base_solution()["racket_target"]
    assert base["raw_code"] == canonical
    assert base["target_code"] == canonical
    assert base["rule_hash"] == actual_hash

    pairs = list(row["train"]) + list(row["test"])
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert gen.self_check(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == before


def test_every_declared_exact_axis_boundary_is_observable_in_every_band():
    index = 0
    for band in ("easy", "medium", "hard"):
        for grid_h in (7, 16):
            for grid_w in (7, 18):
                for n_rows in (2, 4):
                    for n_cols in (1, 3):
                        grid = gen.generate(
                            1000 + index,
                            3001,
                            difficulty=band,
                            grid_h=grid_h,
                            grid_w=grid_w,
                            n_rows=n_rows,
                            n_cols=n_cols,
                        )
                        assert gen.self_check(grid) == []
                        assert gen.observe_overrides(grid) == {
                            "grid_h": grid_h,
                            "grid_w": grid_w,
                            "n_rows": n_rows,
                            "n_cols": n_cols,
                        }
                        index += 1


def test_default_canonical_profile_prior_covers_all_official_joint_profiles():
    official = {
        (10, 8, 3, 1, 1, 2),
        (9, 9, 2, 1, 1, 1),
        (10, 11, 3, 2, 1, 2),
        (12, 11, 4, 2, 2, 2),
    }
    seen = set()
    for seed in range(160):
        grid = gen.generate(seed, seed * 4, difficulty="hard")
        obs = gen.observe_overrides(grid)
        n_blue = sum(value == 1 for row in grid for value in row)
        n_green = sum(value == 3 for row in grid for value in row)
        signature = (
            obs["grid_h"], obs["grid_w"], obs["n_rows"], obs["n_cols"],
            n_blue, n_green,
        )
        assert signature in official
        seen.add(signature)
    assert seen == official


def test_determinism_fresh_returns_and_process_global_rng_purity():
    random.seed(687558)
    before = random.getstate()
    first = gen.generate(17, 9, difficulty="medium")
    after = random.getstate()
    second = gen.generate(17, 9, difficulty="medium")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 9
    assert first != second
    assert second != gen.generate(18, 9, difficulty="medium")
    assert second != gen.generate(17, 10, difficulty="medium")


def test_targeted_impostors_are_rejected():
    base = gen.generate(
        901,
        77,
        difficulty="medium",
        grid_h=12,
        grid_w=12,
        n_rows=3,
        n_cols=2,
    )
    mutations = []

    missing_blue = copy.deepcopy(base)
    for r, row in enumerate(missing_blue):
        for c, value in enumerate(row):
            if value == 1:
                missing_blue[r][c] = 3
    mutations.append(missing_blue)

    duplicate_row_marker = copy.deepcopy(base)
    row_with_horizontal = next(r for r, row in enumerate(base) if any(v in (1, 3) for v in row))
    _, empty_col = _find_empty(duplicate_row_marker, row=row_with_horizontal)
    duplicate_row_marker[row_with_horizontal][empty_col] = 1
    mutations.append(duplicate_row_marker)

    mixed_seed_row = copy.deepcopy(base)
    red_col = next(c for r, row in enumerate(base) for c, value in enumerate(row) if value == 2)
    if mixed_seed_row[row_with_horizontal][red_col] != 0:
        _, red_col = _find_empty(mixed_seed_row, row=row_with_horizontal)
    mixed_seed_row[row_with_horizontal][red_col] = 2
    mutations.append(mixed_seed_row)

    duplicate_red_column = copy.deepcopy(base)
    red_r, red_c = next((r, c) for r, row in enumerate(base) for c, value in enumerate(row) if value == 2)
    new_r, _ = _find_empty(duplicate_red_column, col=red_c)
    if new_r == red_r:
        new_r = next(r for r in range(len(base)) if r != red_r and base[r][red_c] == 0)
    duplicate_red_column[new_r][red_c] = 2
    mutations.append(duplicate_red_column)

    adjacent_marker = copy.deepcopy(base)
    marker_r, marker_c = next((r, c) for r, row in enumerate(base) for c, value in enumerate(row) if value in (1, 3))
    for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        rr, cc = marker_r + dr, marker_c + dc
        if 0 <= rr < len(base) and 0 <= cc < len(base[0]) and adjacent_marker[rr][cc] == 0:
            adjacent_marker[rr][cc] = 3
            break
    mutations.append(adjacent_marker)

    for mutation in mutations:
        assert gen.self_check(mutation), mutation


def test_absent_feature_recombination_is_distribution_invalid_but_oracle_defined():
    base = gen.generate(333, 444, difficulty="medium")
    recombined = copy.deepcopy(base)
    r, c = next((r, c) for r, row in enumerate(recombined) for c, value in enumerate(row) if value == 1)
    recombined[r][c] = 4  # color absent from every remaining scene part
    assert gen.self_check(recombined)
    out = gen.rule_mirror(recombined)
    assert len(out) == len(recombined)
    assert len(out[0]) == len(recombined[0])


def test_line_projection_and_row_precedence_are_positive_witnesses():
    grid = gen.generate(808, 12, difficulty="easy", grid_h=10, grid_w=11, n_rows=4, n_cols=2)
    out = gen.rule_mirror(grid)
    row_colors = {
        r: next(value for value in row if value in (1, 3))
        for r, row in enumerate(grid)
        if any(value in (1, 3) for value in row)
    }
    red_cols = {
        c for c in range(len(grid[0])) if any(grid[r][c] == 2 for r in range(len(grid)))
    }
    assert {1, 3} <= set(row_colors.values())
    assert red_cols
    for r, color in row_colors.items():
        assert out[r] == [color] * len(grid[0])
        for c in red_cols:
            assert out[r][c] == color
    for c in red_cols:
        assert all(out[r][c] == (row_colors[r] if r in row_colors else 2) for r in range(len(grid)))


def test_invalid_calls_reject_loudly():
    with pytest.raises(TypeError):
        gen.generate(1, 1, unknown_axis=3)
    with pytest.raises(ValueError):
        gen.generate(1, 1, difficulty="extreme")
    with pytest.raises(ValueError):
        gen.generate(1, 1, grid_h=6)
    with pytest.raises(ValueError):
        gen.generate(1, 1, n_rows=5)
