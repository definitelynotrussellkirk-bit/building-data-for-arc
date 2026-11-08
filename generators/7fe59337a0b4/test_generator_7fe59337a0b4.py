from __future__ import annotations

import copy
import importlib

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.7fe59337a0b4.generator")


def test_all_canonical_pairs_are_accepted_and_match_rule_mirror():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(original) == []
        assert gen.strict_canonical_like(original) == []
        assert gen.rule_mirror(original) == pair["output"]
        assert original == pair["input"]


def test_every_exact_axis_is_observable_at_boundaries():
    for canvas_size in (9, 15):
        for motif_color in (1, 8):
            for index, profile in enumerate(gen.SCENE_PROFILES):
                grid = gen.generate(
                    9000 + index,
                    index,
                    difficulty="hard",
                    canvas_size=canvas_size,
                    motif_color=motif_color,
                    scene_profile=profile,
                )
                assert gen.self_check(grid) == []
                assert gen.observe_overrides(grid) == {
                    "canvas_size": canvas_size,
                    "motif_color": motif_color,
                    "scene_profile": profile,
                }
                assert gen.rule_mirror(grid) != grid


def test_unknown_overrides_and_difficulty_are_rejected():
    with pytest.raises(KeyError, match="unknown override"):
        gen.generate(1, 0, typo_axis=4)
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 0, difficulty="impossible")
    with pytest.raises(ValueError, match="not in options"):
        gen.generate(1, 0, scene_profile="impossible")


@pytest.mark.parametrize(
    "mutator, message",
    [
        (lambda g: g[0].append(0), "rectangular"),
        (lambda g: g.__setitem__(0, [9] + g[0][1:]), "exactly one"),
        (lambda g: _recolor_one_motif_cell(g, 8), "exactly one non-9 color"),
        (lambda g: _disconnect_one_motif_cell(g), "4-connected"),
        (lambda g: _move_marker_to_corner(g), "clipped"),
    ],
)
def test_structural_mutations_are_rejected(mutator, message):
    grid = gen.generate(77, 2, difficulty="medium", motif_color=3)
    mutator(grid)
    assert any(message in error for error in gen.self_check(grid))


def _motif_positions(grid):
    return [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]


def _recolor_one_motif_cell(grid, color):
    row, col = _motif_positions(grid)[0]
    grid[row][col] = color


def _disconnect_one_motif_cell(grid):
    positions = _motif_positions(grid)
    row, col = positions[-1]
    grid[row][col] = 0
    grid[0][-1] = grid[positions[0][0]][positions[0][1]]


def _move_marker_to_corner(grid):
    for row in grid:
        for col, value in enumerate(row):
            if value == 9:
                row[col] = 0
    grid[0][0] = 9


def test_every_four_demo_window_identifies_the_rule():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(73, index, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(73, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []
            assert {
                gen._analyze(pair["input"])["scene_profile"] for pair in demos
            } == set(gen.SCENE_PROFILES)
            for rival in gen.LESSON_COMPETITORS.values():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_generate_is_deterministic_fresh_and_rng_isolated():
    import random

    random.seed(12345)
    before = random.getstate()
    first = gen.generate(221, 7, difficulty="hard")
    after = random.getstate()
    second = gen.generate(221, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
