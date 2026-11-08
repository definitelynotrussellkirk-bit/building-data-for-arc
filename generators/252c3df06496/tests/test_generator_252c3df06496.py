"""Focused regression tests for generator 252c3df06496."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "252c3df06496"
gen = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs():
    assert gen.RULE_HASH == "ea4fd12284e3"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("profile", tuple(gen._SCENE_PROFILES))
@pytest.mark.parametrize("palette_kind", gen._PALETTE_KINDS)
def test_every_exact_axis_value_is_observable_in_every_band(
    band, profile, palette_kind
):
    grid = gen.generate(
        20260727,
        17,
        difficulty=band,
        scene_profile=profile,
        palette_kind=palette_kind,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "scene_profile": profile,
        "palette_kind": palette_kind,
    }


def test_unknown_and_removed_metadata_only_axes_fail_loudly():
    removed = {
        "grid_h": 6,
        "grid_w": 7,
        "n_rows": 3,
        "palette_size": 3,
        "position_bias": "column0",
        "n_distinct_colors": 3,
        "density": "sparse",
        "texture": "warm",
    }
    for axis, value in removed.items():
        with pytest.raises(ValueError, match="unknown override"):
            gen.generate(3, 4, difficulty="medium", **{axis: value})
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(3, 4, bogus_axis="typo")


def test_deterministic_fresh_returns_and_global_rng_purity():
    random.seed(91027)
    before = random.getstate()
    first = gen.generate(41, 8, difficulty="hard")
    middle = random.getstate()
    second = gen.generate(41, 8, difficulty="hard")
    after = random.getstate()
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert before == middle == after
    first[0][0] = 9 if first[0][0] != 9 else 1
    assert second == gen.generate(41, 8, difficulty="hard")


def test_self_check_rejects_targeted_impostors():
    grid = gen.generate(
        81,
        5,
        scene_profile="canonical_6x7_k3",
        palette_kind="canonical",
    )
    marked = gen._marked_rows(grid)
    assert len(marked) == 3

    no_keys = [[0 for _ in row] for row in grid]
    assert gen.self_check(no_keys)

    body_key = copy.deepcopy(grid)
    row, color = marked[0]
    body_key[row][0] = 0
    body_key[row][2] = color
    assert any("outside column 0" in error for error in gen.self_check(body_key))

    duplicate_color = copy.deepcopy(grid)
    duplicate_color[marked[1][0]][0] = marked[0][1]
    assert any("distinct" in error for error in gen.self_check(duplicate_color))

    all_rows_marked = [[0 for _ in row] for row in grid]
    for row in range(len(all_rows_marked)):
        all_rows_marked[row][0] = row + 1
    assert gen.self_check(all_rows_marked)

    unsupported_shape = copy.deepcopy(grid) + [[0] * len(grid[0])]
    assert any("scene-profile" in error for error in gen.self_check(unsupported_shape))


def test_each_single_demo_refutes_every_named_rival():
    for band in ("easy", "medium", "hard"):
        for seed in range(20):
            grid = gen.generate(1000 + seed, seed * 7 + 1, difficulty=band)
            truth = gen.rule_mirror(grid)
            for name, rival in gen.SEMANTIC_RIVALS.items():
                assert rival(grid) != truth, (band, seed, name)


def test_every_lesson_window_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            pairs = [
                _pair(gen.generate(5000 + start, start + offset, difficulty=band))
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_negative_recombination_is_rejected_but_rule_mirror_executes():
    grid = gen.generate(910, 12, difficulty="medium")
    impostor = copy.deepcopy(grid)
    row, color = gen._marked_rows(impostor)[0]
    impostor[row][0] = 0
    impostor[row][1] = color
    assert gen.self_check(impostor)
    output = gen.rule_mirror(impostor)
    assert len(output) == len(impostor)
    assert all(len(row_out) == len(impostor[0]) for row_out in output)
