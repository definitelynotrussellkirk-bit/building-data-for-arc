"""Focused regression tests for the c24bb478ceb4 generator repair."""
from __future__ import annotations

import random

import pytest

from puzzle_generators.per_puzzle.c24bb478ceb4 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _grid(height: int = 8, width: int = 9):
    return [[0 for _ in range(width)] for _ in range(height)]


def test_canonical_pairs_are_accepted_and_python_mirror_matches() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_all_declared_override_boundaries_round_trip() -> None:
    for height in (7, 10):
        for width in (8, 12):
            for count in (2, 3):
                for palette_kind in gen.PALETTE_KINDS:
                    for missing_pattern in gen.MISSING_PATTERNS:
                        grid = gen.generate(
                            1701,
                            23,
                            difficulty="hard",
                            grid_h=height,
                            grid_w=width,
                            n_rects=count,
                            palette_kind=palette_kind,
                            missing_pattern=missing_pattern,
                        )
                        assert gen.observe_overrides(grid) == {
                            "grid_h": height,
                            "grid_w": width,
                            "n_rects": count,
                            "palette_kind": palette_kind,
                            "missing_pattern": missing_pattern,
                        }
                        assert gen.self_check(grid, difficulty="hard") == []


def test_unknown_and_invalid_overrides_fail_closed() -> None:
    with pytest.raises(TypeError, match="unknown override axis"):
        gen.generate(0, 0, typo_axis=3)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(0, 0, grid_h=6)
    with pytest.raises(ValueError, match="not in"):
        gen.generate(0, 0, missing_pattern="upper")


def test_self_check_rejects_targeted_impostors() -> None:
    blank = _grid()
    assert gen.self_check(blank)

    full_four = _grid()
    for r, c in ((1, 1), (1, 5), (5, 1), (5, 5)):
        full_four[r][c] = 2
    for r, c in ((2, 7), (4, 7), (4, 8)):
        full_four[r][c] = 7
    assert any("appears 4 times" in reason for reason in gen.self_check(full_four))

    two_corners = _grid()
    for r, c in ((1, 1), (5, 5)):
        two_corners[r][c] = 2
    for r, c in ((2, 7), (4, 7), (4, 8)):
        two_corners[r][c] = 7
    assert any("appears 2 times" in reason for reason in gen.self_check(two_corners))

    collinear = _grid()
    for r, c in ((1, 1), (1, 3), (1, 5)):
        collinear[r][c] = 2
    for r, c in ((2, 7), (4, 7), (4, 8)):
        collinear[r][c] = 7
    assert any("two rows and two columns" in reason for reason in gen.self_check(collinear))

    shared_corner = _grid()
    for r, c in ((1, 1), (1, 4), (4, 1)):
        shared_corner[r][c] = 2
    for r, c in ((4, 4), (4, 7), (6, 4)):
        shared_corner[r][c] = 7
    errors = gen.self_check(shared_corner)
    assert any("not blank" in reason for reason in errors)
    assert any("shares implied rectangle" in reason for reason in errors)


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(123456)
    state = random.getstate()
    first = gen.generate(918, 27, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(918, 27, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))


def test_every_sliding_three_demo_window_refutes_named_competitors() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(18):
            pairs = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED + 1):
                inp = gen.generate(3400 + start, sample_index, difficulty=band)
                pairs.append({"input": inp, "output": gen.rule_mirror(inp)})
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_semantic_witnesses_fire_in_every_band() -> None:
    for band in ("easy", "medium", "hard"):
        hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        for index in range(60):
            grid = gen.generate(7000 + index, index, difficulty=band)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                hits[name] += int(witness(grid))
        assert all(count > 0 for count in hits.values()), (band, hits)
