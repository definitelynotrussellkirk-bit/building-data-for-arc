"""Focused regression tests for the 8eeb98656c43 generator repair."""

from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest


HERE = Path(__file__).resolve()
for ancestor in HERE.parents:
    runtime = ancestor / "shared" / "runtime"
    if runtime.is_dir():
        sys.path.insert(0, str(runtime))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    path = Path(
        os.environ.get(
            "GENERATOR_UNDER_TEST",
            HERE.parents[1] / "generator.py",
        )
    )
    spec = importlib.util.spec_from_file_location(
        "generator_8eeb98656c43_under_test", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _pairs():
    return canonical_pairs(gen.TASK_ID, root=find_root(HERE))


def _components(grid, predicate):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if predicate(value)
    }
    result = []
    while remaining:
        first = min(remaining)
        color = grid[first[0]][first[1]]
        todo = [first]
        cells = {first}
        remaining.remove(first)
        while todo:
            r, c = todo.pop()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in remaining and grid[nxt[0]][nxt[1]] == color:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    todo.append(nxt)
        result.append((color, cells))
    return result


def _mixed_witness():
    grid = [[0] * 11 for _ in range(8)]
    grid[1][0] = grid[1][1] = 2
    grid[4][3] = 2
    grid[6][0] = grid[7][0] = 4
    return grid


def test_rule_pin_and_all_canonical_pairs_are_accepted_and_solved():
    assert gen.RULE_HASH == "87bf6fd393d9"
    pairs = _pairs()
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_nonred_left_object_is_ignored_and_refutes_color_blind_mirroring():
    grid = _mixed_witness()
    assert gen.self_check(grid) == []
    expected = gen.rule_mirror(grid)
    rival = gen.SEMANTIC_RIVALS["mirror_every_nonzero"]

    assert expected[6][10] == 0
    assert expected[7][10] == 0
    assert rival(grid)[6][10] == 7
    assert rival(grid)[7][10] == 7
    assert rival(grid) != expected
    assert gen.SEMANTIC_WITNESSES["ignore_nonred_left_objects"](grid)


def test_every_three_default_samples_contain_a_decisive_mixed_color_witness():
    assert not hasattr(gen, "LESSON_SCHEDULE_PERIOD")
    period = len(gen.SCHEDULE_PROFILES)
    assert period == 3
    for band in (None, "easy", "medium", "hard"):
        for start in range(period * 3):
            grids = [gen.generate(4109, index, difficulty=band) for index in range(start, start + 3)]
            assert all(gen.self_check(grid) == [] for grid in grids)
            assert any(
                gen.SEMANTIC_WITNESSES["ignore_nonred_left_objects"](grid)
                for grid in grids
            )


def test_exact_axes_are_observable_and_scalar_inputs_are_strict():
    for band in (None, "easy", "medium", "hard"):
        grid = gen.generate(
            997,
            7,
            difficulty=band,
            grid_h=8,
            half_w=4,
            n_targets=2,
            n_distractors=2,
        )
        assert len(grid) == 8
        assert len(grid[0]) == 9
        assert len(_components(grid, lambda value: value == 2)) == 2
        assert len(_components(grid, lambda value: value not in (0, 2))) == 2
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {
            "grid_h": 8,
            "half_w": 4,
            "n_targets": 2,
            "n_distractors": 2,
        }

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")
    with pytest.raises((TypeError, ValueError), match="sample_index"):
        gen.generate(1, True)
    with pytest.raises((TypeError, ValueError), match="integer|bool"):
        gen.generate(1, 0, grid_h=8.0)


def test_generation_is_deterministic_fresh_and_does_not_touch_global_random():
    random.seed(712358)
    state = random.getstate()
    first = gen.generate(222, 5, difficulty="hard")
    second = gen.generate(222, 5, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert random.getstate() == state


def test_self_check_rejects_malformed_or_rule_ambiguous_inputs():
    blank = [[0] * 11 for _ in range(8)]
    assert gen.self_check(blank)

    center = _mixed_witness()
    center[2][5] = 2
    assert any("center" in reason or "axis" in reason for reason in gen.self_check(center))

    right = _mixed_witness()
    right[2][8] = 2
    assert any("right" in reason for reason in gen.self_check(right))

    output_color = _mixed_witness()
    output_color[2][2] = 7
    assert any("color 7" in reason for reason in gen.self_check(output_color))

    solid = [[0] * 11 for _ in range(8)]
    for r in range(2):
        for c in range(2):
            solid[r][c] = 2
    assert gen.self_check(solid)

    ragged = _mixed_witness()
    ragged[0].pop()
    assert any("rectangular" in reason or "ragged" in reason for reason in gen.self_check(ragged))


def test_declared_rival_fits_public_pairs_but_generated_lessons_refute_it():
    rival = gen.CANONICAL_SHORTCUTS["mirror_every_nonzero"]
    for pair in _pairs():
        assert rival(pair["input"]) == pair["output"]

    for band in (None, "easy", "medium", "hard"):
        pairs = []
        for index in range(4):
            grid = gen.generate(331, index, difficulty=band)
            pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
        for query_index in range(4):
            query = pairs[query_index]
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []
