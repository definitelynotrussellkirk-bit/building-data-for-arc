from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.b25434a1b56e import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "b25434a1b56e"


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_version_are_pinned() -> None:
    assert gen.RULE_HASH == "d994ac093631"
    assert gen.VERSION == "3.0.0"


def test_all_canonical_pairs_are_accepted_and_mirrored() -> None:
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_empty_canonical_quadrant_maps_to_zero() -> None:
    pair = canonical_pairs(TASK_ID)[1]
    signature = gen.semantic_signature(pair["input"])
    assert signature["empty_quadrants"] == 1
    assert pair["output"][1][0] == 0
    assert gen.self_check(pair["input"]) == []


def test_generation_is_deterministic_fresh_and_global_rng_pure() -> None:
    state = random.getstate()
    first = gen.generate(97, 11, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(97, 11, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second


@pytest.mark.parametrize("height", [6, 8, 10, 12])
@pytest.mark.parametrize("width", [6, 8, 10, 12])
def test_exact_dimension_overrides_are_observed(height: int, width: int) -> None:
    grid = gen.generate(
        123,
        4,
        difficulty="easy",
        grid_h=height,
        grid_w=width,
    )
    assert (len(grid), len(grid[0])) == (height, width)
    assert gen.self_check(grid) == []


def test_unknown_and_invalid_overrides_fail_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, mystery_axis=3)
    with pytest.raises(ValueError, match="not in options"):
        gen.generate(1, 0, grid_h=4)


def test_self_check_rejects_four_structural_impostors() -> None:
    valid = gen.generate(44, 7, difficulty="medium")

    ragged = copy.deepcopy(valid)
    ragged[0].pop()
    assert any("rectangular" in reason for reason in gen.self_check(ragged))

    odd_height = copy.deepcopy(valid[:-1])
    assert any("even" in reason for reason in gen.self_check(odd_height))

    invalid_color = copy.deepcopy(valid)
    invalid_color[0][0] = 10
    assert any("0..9" in reason for reason in gen.self_check(invalid_color))

    tied = [[0] * 6 for _ in range(6)]
    tied[0][0] = tied[0][1] = 4
    tied[1][0] = tied[1][1] = 6
    for r0, c0, color in ((0, 3, 2), (3, 0, 3), (3, 3, 8)):
        tied[r0][c0] = tied[r0][c0 + 1] = tied[r0 + 1][c0] = color
    assert any("tied top colors" in reason for reason in gen.self_check(tied))


def test_generated_scenes_refute_public_shortcuts_in_every_band() -> None:
    for band in ("easy", "medium", "hard"):
        for index in range(24):
            grid = gen.generate(7000 + index, index, difficulty=band)
            official = gen.rule_mirror(grid)
            assert gen.SEMANTIC_RIVALS["first_nonzero"](grid) != official
            assert gen.SEMANTIC_RIVALS["highest_nonzero"](grid) != official
            assert gen.SEMANTIC_RIVALS["global_mode_broadcast"](grid) != official


def test_empty_and_nonempty_schedule_covers_every_three_example_window() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(32):
            demos = [_pair(9000 + start, start + offset, band) for offset in range(3)]
            query = _pair(9000 + start, start + 3, band)
            empty_counts = [
                gen.semantic_signature(pair["input"])["empty_quadrants"]
                for pair in demos
            ]
            assert any(count == 0 for count in empty_counts)
            assert any(count == 1 for count in empty_counts)
            assert gen.lesson_identifiable(demos, query) == []


def test_negative_recombination_is_rejected_while_rule_boundary_is_explicit() -> None:
    grid = gen.generate(17, 5, difficulty="medium")
    bad = copy.deepcopy(grid)
    half_h, half_w = len(bad) // 2, len(bad[0]) // 2
    for r in range(half_h):
        for c in range(half_w):
            bad[r][c] = 0
    bad[0][0] = bad[0][1] = 2
    bad[1][0] = bad[1][1] = 9
    errors = gen.self_check(bad)
    assert any("tied top colors" in reason for reason in errors)
    # The selected Racket source defines a high-color tie break.  The teaching
    # grammar rejects such ambiguous lessons, while the exact mirror records
    # the authority boundary for hidden probes.
    assert gen.rule_mirror(bad)[0][0] == 9
