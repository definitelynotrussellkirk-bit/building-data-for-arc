from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.per_puzzle.e9f9d6781b00 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def test_canonical_pairs_are_accepted_and_mirrored() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_schedule_makes_every_four_demo_window_identifiable() -> None:
    for start in range(12):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(901, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(901, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        assert {gen.observe_overrides(d["input"])["layout"] for d in demos} == set(gen.LAYOUTS)
        assert {gen.observe_overrides(d["input"])["n_dots"] for d in demos} == {2, 3, 4}


def test_exact_overrides_are_observable_at_boundaries() -> None:
    cases = [
        {"grid_h": 3, "grid_w": 3, "n_dots": 2, "layout": "mixed_edges"},
        {"grid_h": 6, "grid_w": 6, "n_dots": 4, "layout": "mixed_edges"},
        {"grid_h": 3, "grid_w": 6, "n_dots": 4, "layout": "interior_mix"},
        {"grid_h": 6, "grid_w": 3, "n_dots": 2, "layout": "interior_mix"},
    ]
    for band in ("easy", "medium", "hard"):
        for seed, overrides in enumerate(cases):
            grid = gen.generate(seed, 7, difficulty=band, **overrides)
            assert gen.self_check(grid, meta={"overrides": overrides}) == []
            assert gen.observe_overrides(grid) == overrides


def test_unknown_and_invalid_overrides_reject_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=3)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(0, 0, grid_h=7)
    with pytest.raises(ValueError, match="not in options"):
        gen.generate(0, 0, layout="top_row")


def test_self_check_rejects_targeted_impostors() -> None:
    for texture in gen.DEGENERATE_TEXTURES:
        grid = gen.generate(0, 0, texture=texture)
        assert gen.self_check(grid), texture

    valid = gen.generate(5, 1)
    same_diagonal_new_color = copy.deepcopy(valid)
    dots = gen._dot_cells(same_diagonal_new_color)
    r, c, _ = dots[0]
    used_colors = {value for _, _, value in dots}
    replacement = next(color for color in range(1, 10) if color not in used_colors)
    for rr in range(len(valid)):
        cc = rr - (r - c)
        if 0 <= cc < len(valid[0]) and same_diagonal_new_color[rr][cc] == 0:
            same_diagonal_new_color[rr][cc] = replacement
            break
    assert any("distinct southeast diagonals" in reason for reason in gen.self_check(same_diagonal_new_color))


def test_determinism_fresh_returns_and_global_rng_state() -> None:
    state = random.getstate()
    first = gen.generate(12345, 9, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(12345, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 99
    assert gen.generate(12345, 9, difficulty="hard") == second


def test_named_rivals_are_refuted_by_scheduled_demos() -> None:
    demos = []
    for sample_index in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(2026, sample_index, difficulty="hard")
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(demo["input"]) != demo["output"] for demo in demos), name
