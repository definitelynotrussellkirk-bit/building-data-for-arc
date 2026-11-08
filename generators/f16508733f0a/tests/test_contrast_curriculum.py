"""Regression tests for colour agreement and simultaneous-update teaching."""
from __future__ import annotations

import copy
import importlib

from scripts.canonical_profile_gate import canonical_pairs

gen = importlib.import_module("puzzle_generators.per_puzzle.f16508733f0a.generator")


def majority_rival(grid):
    out = copy.deepcopy(grid)
    for r in range(len(grid) - 1):
        for c in range(len(grid[0]) - 1):
            cells = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
            values = [grid[y][x] for y, x in cells]
            nonzero = [v for v in values if v]
            if len(nonzero) == 3:
                colour = min(set(nonzero), key=lambda v: (-nonzero.count(v), v))
                y, x = cells[values.index(0)]
                out[y][x] = colour
    return out


def decoy_grid():
    # The rightmost lower zero is beside a mixed-colour L and must NOT fill.
    # It becomes fillable on a second pass, so this also tests simultaneity.
    return [
        [1, 1, 1, 1, 1, 0, 0, 0],
        [0, 1, 0, 0, 2, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
        [2, 2, 0, 0, 0, 0, 0, 0],
        [2, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ]


def test_mixed_colour_decoy_is_lawful_when_real_targets_are_present():
    grid = decoy_grid()
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    out = gen.rule_mirror(grid)
    assert out[1][:5] == [1, 1, 1, 0, 2]
    assert majority_rival(grid) != out
    assert gen.rule_mirror(out) != out


def test_connected_multicolour_axis_combination_supplies_both_controls():
    for seed in range(12):
        for band in ("easy", "medium", "hard"):
            grid = gen.generate(seed, 0, difficulty=band, layout_mode="connected", color_count=2)
            output = gen.rule_mirror(grid)
            assert majority_rival(grid) != output, (seed, band)
            assert gen.rule_mirror(output) != output, (seed, band)


def test_colour_and_simultaneity_rivals_are_declared_and_fit_canonical():
    expected = {"ignore_colour_agreement", "repeat_until_stable"}
    assert expected <= set(gen.CANONICAL_SHORTCUTS)
    pairs = canonical_pairs(gen.TASK_ID)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(p["input"]) == p["output"] for p in pairs), name


def test_every_cyclic_three_demo_start_has_both_contrastive_witnesses():
    for seed in range(8):
        for band in ("easy", "medium", "hard"):
            examples = [gen.generate(seed, i, difficulty=band) for i in range(9)]
            for start in range(6):
                demos = examples[start:start + 3]
                assert any(majority_rival(g) != gen.rule_mirror(g) for g in demos), (seed, band, start)
                assert any(gen.rule_mirror(gen.rule_mirror(g)) != gen.rule_mirror(g) for g in demos)


def test_ambiguous_canonical_only_lesson_is_not_silently_admitted():
    demos = canonical_pairs(gen.TASK_ID)[:3]
    query = {"input": decoy_grid(), "output": gen.rule_mirror(decoy_grid())}
    reasons = gen.lesson_identifiable(demos, query)
    assert any("ignore_colour_agreement" in reason for reason in reasons)
    assert any("repeat_until_stable" in reason for reason in reasons)


def test_all_exact_axis_combinations_remain_realizable():
    # All 54 categorical/count combinations at the smallest grid, at four
    # seeds each (216 draws), not just endpoint draws. In particular, 6 targets / 3 colours stresses packing.
    for targets in (4, 5, 6):
        for colours in (1, 2, 3):
            for mode in ("isolated", "connected"):
                for corners in (2, 3, 4):
                    overrides = dict(grid_h=6, grid_w=8, target_count=targets,
                                     color_count=colours, layout_mode=mode,
                                     corner_diversity=corners)
                    for seed in (0, 17, 1009, 104729):
                        grid = gen.generate(seed, 200 + seed, difficulty="hard", **overrides)
                        assert gen.observe_overrides(grid) == overrides
                        assert gen.self_check(grid, meta={"overrides": overrides}) == []


def test_mirror_preserves_every_preexisting_cell_and_is_pure():
    for index in range(18):
        grid = gen.generate(73, index, difficulty="medium")
        before = copy.deepcopy(grid)
        out = gen.rule_mirror(grid)
        assert grid == before
        assert all(v == out[r][c] for r, row in enumerate(grid) for c, v in enumerate(row) if v)
