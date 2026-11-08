from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "1ea2cf5a712b"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def test_rule_hash_and_canonical_pairs() -> None:
    assert gen.RULE_HASH == "d20eedb326dc"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", [7, 9])
@pytest.mark.parametrize("board_w", [8, 9])
@pytest.mark.parametrize("match_count", [2, 3])
def test_exact_override_axes_are_observable(
    difficulty: str, grid_h: int, board_w: int, match_count: int
) -> None:
    grid = gen.generate(
        7001,
        13,
        difficulty=difficulty,
        grid_h=grid_h,
        board_w=board_w,
        match_count=match_count,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": grid_h,
        "board_w": board_w,
        "match_count": match_count,
    }


def test_unknown_override_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, bogus_axis=3)


def test_schedule_exercises_both_decoys_and_wildcard_semantics() -> None:
    grids = [gen.generate(8100 + index, index, difficulty="medium") for index in range(4)]
    assert all(gen.SEMANTIC_WITNESSES["template_zero_is_wildcard"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["two_color_mapping_rebuts_shape_only"](grid) for grid in grids)
    assert any(gen.SEMANTIC_WITNESSES["reflection_is_not_a_rotation"](grid) for grid in grids)
    assert all(gen.SEMANTIC_WITNESSES["rotation_branch_changes_answer"](grid) for grid in grids)
    assert all(gen.SEMANTIC_WITNESSES["all_matches_are_marked"](grid) for grid in grids)


def test_structural_mutations_are_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_deterministic_fresh_returns_and_band_variation() -> None:
    first = gen.generate(222, 5, difficulty="medium")
    second = gen.generate(222, 5, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert gen.generate(222, 5, difficulty="medium") == second

    by_band = [gen.generate(222, 5, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({repr(grid) for grid in by_band}) == 3
