from __future__ import annotations

import importlib
import random

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "36275402c6b2"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _valid_grid(seed=11, sample_index=7, **overrides):
    return GEN.generate(seed, sample_index, difficulty="medium", **overrides)


def test_canonical_pairs_are_accepted_and_mirrored():
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_exact_override_boundaries_round_trip():
    cases = [
        {
            "grid_h": 11,
            "grid_w": 11,
            "rect_h": 7,
            "rect_w": 7,
            "frame_color": 1,
            "pair_count": 3,
        },
        {
            "grid_h": 15,
            "grid_w": 15,
            "rect_h": 4,
            "rect_w": 4,
            "frame_color": 9,
            "pair_count": 2,
        },
    ]
    for overrides in cases:
        grid = _valid_grid(**overrides)
        assert GEN.observe_overrides(grid) == overrides
        assert GEN.self_check(grid, meta={"overrides": overrides}) == []


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override axis"):
        GEN.generate(1, 2, difficulty="easy", misspelled_axis=3)


def test_determinism_fresh_returns_and_global_rng_purity():
    before = random.getstate()
    first = GEN.generate(444, 8, difficulty="hard")
    assert random.getstate() == before
    second = GEN.generate(444, 8, difficulty="hard")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]


def test_self_check_rejects_four_targeted_impostors():
    grid = _valid_grid(pair_count=3)
    analysis = GEN._analysis_or_raise(grid)

    missing_legend_cell = [row[:] for row in grid]
    _, _, pair_row, pair_col = analysis["pairs"][0]
    missing_legend_cell[pair_row][pair_col + 1] = 0
    assert GEN.self_check(missing_legend_cell)

    three_cell_legend = [row[:] for row in grid]
    extension = pair_col + 2
    if extension >= len(grid[0]) or three_cell_legend[pair_row][extension] != 0:
        extension = pair_col - 1
    assert 0 <= extension < len(grid[0])
    three_cell_legend[pair_row][extension] = analysis["frame"]
    assert GEN.self_check(three_cell_legend)

    target_inside_crop = [row[:] for row in grid]
    r1, c1, r2, c2 = analysis["bbox"]
    target_inside_crop[r1 + 1][c1 + 1] = analysis["targets"][0]
    assert GEN.self_check(target_inside_crop)

    missing_source = [row[:] for row in grid]
    source = analysis["sources"][0]
    for row in range(r1, r2 + 1):
        for col in range(c1, c2 + 1):
            if missing_source[row][col] == source:
                missing_source[row][col] = analysis["frame"]
    assert GEN.self_check(missing_source)


def test_negative_recombination_is_rejected():
    grid_a = _valid_grid(seed=101, sample_index=1, frame_color=1, pair_count=2)
    grid_b = _valid_grid(seed=202, sample_index=2, frame_color=9, pair_count=2)
    a = GEN._analysis_or_raise(grid_a)
    b = GEN._analysis_or_raise(grid_b)
    recombined = [row[:] for row in grid_a]
    for (_, _, row_a, col_a), (target_b, source_b, _, _) in zip(a["pairs"], b["pairs"]):
        recombined[row_a][col_a] = target_b
        recombined[row_a][col_a + 1] = source_b
    errors = GEN.self_check(recombined)
    assert errors
    assert any("absent from the crop" in error or "unkeyed colour" in error for error in errors)


def test_core_rivals_always_disagree_and_branch_rivals_have_witnesses():
    witnessed = {name: False for name in GEN.SEMANTIC_RIVALS}
    for seed in range(12):
        grid = GEN.generate(seed + 900, seed, difficulty="hard")
        official = GEN.rule_mirror(grid)
        for name, rival in GEN.SEMANTIC_RIVALS.items():
            differs = rival(grid) != official
            witnessed[name] |= differs
            if name not in {"preserve_border_sources", "ignore_side_legends"}:
                assert differs, name
    assert all(witnessed.values()), witnessed
