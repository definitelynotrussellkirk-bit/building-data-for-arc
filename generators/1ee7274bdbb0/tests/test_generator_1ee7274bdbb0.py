from __future__ import annotations

import importlib.util
import random

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "1ee7274bdbb0"
ROOT = find_root(__file__)
_source = ROOT / "generators" / TASK_ID / "generator.py"
if not _source.is_file():
    _source = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
_spec = importlib.util.spec_from_file_location("test_marked_tiles_subject", _source)
generator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generator)


def _canonical_pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT)


def _independent_rule(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    divider_rows = [r for r in range(height) if all(v == 9 for v in grid[r])]
    divider_cols = [
        c for c in range(width) if all(grid[r][c] == 9 for r in range(height))
    ]

    def bounds(length: int, dividers: list[int]) -> list[tuple[int, int]]:
        out: list[tuple[int, int]] = []
        previous = -1
        for divider in [*dividers, length]:
            out.append((previous + 1, divider))
            previous = divider
        return out

    rows = bounds(height, divider_rows)
    cols = bounds(width, divider_cols)
    output = [[0 for _ in range(width)] for _ in range(height)]
    for r in divider_rows:
        output[r] = [9] * width
    for c in divider_cols:
        for r in range(height):
            output[r][c] = 9

    tile_size = rows[0][1] - rows[0][0]
    for r0, r1 in rows:
        for c0, c1 in cols:
            motif = {
                (r - r0, c - c0)
                for r in range(r0, r1)
                for c in range(c0, c1)
                if grid[r][c] == 2
            }
            marked = any(
                grid[r][c] == 3
                for r in range(r0, r1)
                for c in range(c0, c1)
            )
            if marked:
                motif = {(c, tile_size - 1 - r) for r, c in motif}
            for r, c in motif:
                output[r0 + r][c0 + c] = 8
    return output


def test_rule_hash_and_all_canonical_pairs():
    assert generator.RULE_HASH == "a23915e769b9"
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        before = [row[:] for row in pair["input"]]
        assert generator.self_check(pair["input"]) == []
        assert generator.strict_canonical_like(pair["input"]) == []
        assert _independent_rule(pair["input"]) == pair["output"]
        assert generator.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {
            "tile_size": 3,
            "n_tile_rows": 1,
            "n_tile_cols": 2,
            "shape_size": 1,
            "rotate_flag": False,
            "n_flag_cells": 1,
        },
        {
            "tile_size": 5,
            "n_tile_rows": 3,
            "n_tile_cols": 4,
            "shape_size": 6,
            "rotate_flag": True,
            "n_flag_cells": 3,
        },
    ],
)
def test_exact_override_boundaries_are_observable(difficulty, overrides):
    grid = generator.generate(127, 9, difficulty=difficulty, **overrides)
    assert generator.self_check(grid, meta={"overrides": overrides}) == []
    assert generator.observe_overrides(grid) == overrides
    assert generator.rule_mirror(grid) == _independent_rule(grid)


def test_semantic_witnesses_and_lesson_identifiability():
    pairs = _canonical_pairs()
    for band in ("easy", "medium", "hard"):
        grid = generator.generate(991, 4, difficulty=band)
        assert generator.self_check(grid) == []
        for name in ("marked_rotation_visible", "unmarked_copy_control", "mixed_marker_control",
                     "motif_size_distractor", "marker_not_answer"):
            assert generator.SEMANTIC_WITNESSES[name](grid)
    assert generator.lesson_identifiable(pairs[:2], pairs[2]) == []


def test_self_check_rejects_all_negative_fixtures_and_mutations():
    for texture in generator.DEGENERATE_TEXTURES:
        grid = generator.generate(4, 0, texture=texture)
        assert generator.self_check(grid), texture

    valid = generator.generate(81, 2, difficulty="medium")
    no_lattice = [[0 if value == 9 else value for value in row] for row in valid]
    no_markers = [[0 if value == 3 else value for value in row] for row in valid]
    missing_motif = [row[:] for row in valid]
    analysis = generator._analyze(missing_motif)
    first = analysis["tiles"][0]
    for r, c in first["twos"]:
        missing_motif[first["r0"] + r][first["c0"] + c] = 0
    for mutation in (no_lattice, no_markers, missing_motif):
        assert generator.self_check(mutation)


def test_deterministic_fresh_returns_and_global_random_state():
    random.seed(4917)
    before = random.getstate()
    first = generator.generate(222, 6, difficulty="hard")
    after = random.getstate()
    second = generator.generate(222, 6, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert first != second
