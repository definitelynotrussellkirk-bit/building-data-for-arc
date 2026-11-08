from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest


MODULE = importlib.import_module(
    "puzzle_generators.per_puzzle.60d5b73ff222.generator"
)
ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = (
    ROOT
    / "data/base/solutions/banks/38166e88069b/E27__60d5b73ff222.json"
)


def _canonical_inputs() -> list[list[list[int]]]:
    record = json.loads(AUTHORITY.read_text())
    samples = json.loads(record["visible_context"]["samples_text"])
    return [
        pair["input"]
        for split in (samples["train"], samples["test"])
        for pair in split
    ]


def _blank(h: int = 9, w: int = 9) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def _add_target(
    grid: list[list[int]], r: int, c: int, orientation: str
) -> None:
    for rr, cc in MODULE._pair_cells(r, c, orientation):
        grid[rr][cc] = 3


def test_canonical_inputs_are_in_distribution_and_cover_both_branches() -> None:
    for grid in _canonical_inputs():
        analysis = MODULE._analysis(grid)
        assert analysis["errors"] == []
        assert analysis["main_count"] > 0
        assert analysis["anti_count"] > 0
        assert MODULE.self_check(grid) == []


def test_boundary_overrides_are_exact_across_all_difficulty_bands() -> None:
    for band in ("easy", "medium", "hard"):
        for h, w, n_pairs in ((7, 7, 3), (7, 7, 6), (14, 14, 3), (14, 14, 6)):
            for seed in range(8):
                grid = MODULE.generate(
                    1000 + seed,
                    seed * 31 + 7,
                    difficulty=band,
                    grid_h=h,
                    grid_w=w,
                    n_pairs=n_pairs,
                )
                assert (len(grid), len(grid[0])) == (h, w)
                assert MODULE.observe_overrides(grid) == {"n_pairs": n_pairs}
                assert MODULE.self_check(grid) == []


def test_default_bands_realize_their_declared_pair_ranges() -> None:
    expected = {
        "easy": range(3, 5),
        "medium": range(4, 6),
        "hard": range(5, 7),
    }
    for band, allowed in expected.items():
        observed = set()
        for seed in range(40):
            grid = MODULE.generate(seed, seed * 17 + 3, difficulty=band)
            n_pairs = MODULE.observe_overrides(grid)["n_pairs"]
            assert n_pairs in allowed
            observed.add(n_pairs)
        assert observed == set(allowed)


def test_replay_is_fresh_and_does_not_touch_process_global_rng() -> None:
    state = random.getstate()
    first = MODULE.generate(73, 19, difficulty="hard", n_pairs=6)
    assert random.getstate() == state
    second = MODULE.generate(73, 19, difficulty="hard", n_pairs=6)
    assert random.getstate() == state

    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    first[0][0] = 9
    replay = MODULE.generate(73, 19, difficulty="hard", n_pairs=6)
    assert replay == second


def test_invalid_or_unknown_overrides_reject_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 1, mystery_axis=4)
    with pytest.raises(ValueError, match="outside"):
        MODULE.generate(1, 1, grid_h=6)
    with pytest.raises(ValueError, match="outside"):
        MODULE.generate(1, 1, n_pairs=7)
    with pytest.raises(ValueError, match="difficulty"):
        MODULE.generate(1, 1, difficulty="expert")


def test_four_targeted_impostors_are_rejected() -> None:
    valid = MODULE.generate(809, 23, difficulty="medium", n_pairs=5)

    all_background = _blank(len(valid), len(valid[0]))

    no_distractor = [row[:] for row in valid]
    for r, c in MODULE._analysis(valid)["distractor_cells"]:
        no_distractor[r][c] = 0

    one_orientation = _blank()
    for r, c in ((0, 0), (3, 3), (7, 7)):
        _add_target(one_orientation, r, c, "main")
    one_orientation[0][5] = 3

    no_border_target = _blank()
    _add_target(no_border_target, 1, 1, "main")
    _add_target(no_border_target, 1, 5, "anti")
    _add_target(no_border_target, 4, 3, "main")
    no_border_target[7][7] = 3

    impostors = {
        "all_background": all_background,
        "no_distractor": no_distractor,
        "one_orientation": one_orientation,
        "no_border_target": no_border_target,
    }
    for name, grid in impostors.items():
        assert MODULE.self_check(grid), name


def test_color_recombination_is_outside_the_teaching_distribution() -> None:
    grid = MODULE.generate(901, 29, difficulty="easy")
    recombined = [row[:] for row in grid]
    distractor = MODULE._analysis(grid)["distractor_cells"][0]
    recombined[distractor[0]][distractor[1]] = 8
    errors = MODULE.self_check(recombined)
    assert any("colors 0 and 3" in error for error in errors)


def _official_mirror(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            a, b = grid[r][c], grid[r][c + 1]
            d, e = grid[r + 1][c], grid[r + 1][c + 1]
            if (a, b, d, e) == (3, 0, 0, 3):
                out[r][c + 1] = out[r + 1][c] = 3
            elif (a, b, d, e) == (0, 3, 3, 0):
                out[r][c] = out[r + 1][c + 1] = 3
    return out


def _relaxed_diagonal_mirror(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            if grid[r][c] == grid[r + 1][c + 1] == 3:
                out[r][c + 1] = out[r + 1][c] = 3
            if grid[r][c + 1] == grid[r + 1][c] == 3:
                out[r][c] = out[r + 1][c + 1] = 3
    return out


def test_normal_draws_include_a_blocked_diagonal_else_branch_witness() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            grid = MODULE.generate(2000 + seed, seed * 47 + 5, difficulty=band)
            analysis = MODULE._analysis(grid)
            assert analysis["blocked_count"] >= 1
            assert _official_mirror(grid) != _relaxed_diagonal_mirror(grid)
