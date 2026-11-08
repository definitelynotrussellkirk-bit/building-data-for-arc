from __future__ import annotations

import importlib
import random
from collections import Counter

from reviewer_support import canonical_pairs, find_root


TASK_ID = "90640e0e6314"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = find_root(__file__)


def _oracle(grid):
    n = len(grid)
    out = [[0 for _ in range(2 * n)] for _ in range(2 * n)]
    for r in range(2 * n):
        for c in range(2 * n):
            qr, qc = r // n, c // n
            lr, lc = r % n, c % n
            if qr == 0 and qc == 0:
                out[r][c] = grid[n - 1 - lr][n - 1 - lc]
            elif qr == 0:
                out[r][c] = grid[n - 1 - lr][lc]
            elif qc == 0:
                out[r][c] = grid[lr][n - 1 - lc]
            else:
                out[r][c] = grid[lr][lc]
    return out


def _strict_profile(grid):
    n = len(grid)
    counts = Counter(value for row in grid for value in row)
    modal_fraction = max(counts.values()) / (n * n)
    variants = {
        tuple(tuple(row) for row in variant)
        for variant in (
            grid,
            [row[:] for row in reversed(grid)],
            [list(reversed(row)) for row in grid],
            [list(reversed(row)) for row in reversed(grid)],
        )
    }
    return (
        n in {3, 4, 8}
        and len(counts) == 4
        and 1 / 3 <= modal_fraction <= 9 / 16
        and len({tuple(row) for row in grid}) >= n - 1
        and len({tuple(grid[r][c] for r in range(n)) for c in range(n)}) >= n - 1
        and len(variants) == 4
    )


def test_rule_hash_and_task_identity_are_pinned():
    assert MODULE.TASK_ID == TASK_ID
    assert MODULE.GENERATOR_ID == TASK_ID
    assert MODULE.RULE_HASH == "370706e398d4"


def test_all_canonical_inputs_pass_and_python_oracle_matches_outputs():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        assert MODULE.self_check(pair["input"]) == []
        assert _oracle(pair["input"]) == pair["output"]


def test_boundary_overrides_are_exact_in_every_band():
    for band in ("easy", "medium", "hard"):
        for n in (3, 8):
            for palette_size in (3, 7):
                grid = MODULE.generate(
                    41,
                    19,
                    difficulty=band,
                    grid_n=n,
                    palette_size=palette_size,
                    texture="noise",
                    bg_density=0.0,
                    noise_overlay=0.0,
                )
                assert len(grid) == n
                assert all(len(row) == n for row in grid)
                assert len({value for row in grid for value in row}) == palette_size
                assert MODULE.self_check(
                    grid,
                    difficulty=band,
                    meta={"grid_n": n, "palette_size": palette_size},
                ) == []


def test_replay_is_deterministic_fresh_and_does_not_touch_global_rng():
    before = random.getstate()
    first = MODULE.generate(1234, 57, difficulty="hard")
    after = random.getstate()
    second = MODULE.generate(1234, 57, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_self_check_rejects_four_targeted_impostor_classes():
    monochrome = [[0] * 4 for _ in range(4)]
    too_sparse = [[0] * 4 for _ in range(4)]
    too_sparse[0][0] = 1
    too_sparse[3][1] = 2
    solid_block = [[0] * 4 for _ in range(4)]
    solid_block[0][0] = solid_block[0][1] = 1
    solid_block[1][0] = solid_block[1][1] = 2
    horizontal_alias = [
        [0, 1, 2, 0],
        [2, 1, 0, 2],
        [2, 1, 0, 2],
        [0, 1, 2, 0],
    ]
    vertical_alias = [
        [0, 1, 1, 0],
        [2, 0, 0, 2],
        [1, 2, 2, 1],
        [0, 2, 2, 0],
    ]
    for grid in (
        monochrome,
        too_sparse,
        solid_block,
        horizontal_alias,
        vertical_alias,
    ):
        assert MODULE.self_check(grid), grid


def test_default_schedule_keeps_each_band_above_twenty_percent_strict_profile():
    for band in ("easy", "medium", "hard"):
        draws = [
            MODULE.generate(20_000 + i, i, difficulty=band)
            for i in range(80)
        ]
        matches = sum(_strict_profile(grid) for grid in draws)
        assert matches >= 16, (band, matches)


def test_transform_assignment_is_unique_for_every_generated_input():
    # With all four variants distinct, no alternative quadrant permutation can
    # match the official 2x2 output. This rules out transform-answer ambiguity.
    import itertools

    for band in ("easy", "medium", "hard"):
        for i in range(12):
            grid = MODULE.generate(70_000 + i, i, difficulty=band)
            variants = [
                [list(reversed(row)) for row in reversed(grid)],
                [row[:] for row in reversed(grid)],
                [list(reversed(row)) for row in grid],
                [row[:] for row in grid],
            ]
            official = _oracle(grid)
            n = len(grid)
            matches = 0
            for order in itertools.permutations(range(4)):
                candidate = [[0] * (2 * n) for _ in range(2 * n)]
                for quadrant, variant_index in enumerate(order):
                    qr, qc = divmod(quadrant, 2)
                    variant = variants[variant_index]
                    for r in range(n):
                        for c in range(n):
                            candidate[qr * n + r][qc * n + c] = variant[r][c]
                matches += candidate == official
            assert matches == 1
