"""Focused regression tests for generator 577d2db13443."""
from __future__ import annotations

import copy
import importlib
import random
from itertools import product

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.577d2db13443.generator"
)


def test_canonical_pairs_are_accepted_and_match_python_oracle() -> None:
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._oracle(pair["input"]) == pair["output"]


def test_every_exact_override_combination_is_observable() -> None:
    values = (
        range(7, 10),
        range(1, 3),
        range(1, 4),
        range(3, 7),
        ("zero_gaps", "color_boundary"),
        ("interior", "has_border"),
    )
    names = tuple(gen.AXES)
    for sample_index, combination in enumerate(product(*values)):
        overrides = dict(zip(names, combination))
        grid = gen.generate(
            918273,
            sample_index,
            difficulty=("easy", "medium", "hard")[sample_index % 3],
            **overrides,
        )
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, meta={"overrides": overrides}) == []


def test_unknown_override_and_invalid_values_are_rejected() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, misspelled_axis=3)
    with pytest.raises(ValueError, match="run_count"):
        gen.generate(1, 0, run_count=6)
    with pytest.raises(ValueError, match="separator_style"):
        gen.generate(1, 0, separator_style="decorative")


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(1107)
    state_before = random.getstate()
    first = gen.generate(12345, 77, difficulty="medium")
    state_after = random.getstate()
    second = gen.generate(12345, 77, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert state_before == state_after


def test_self_check_rejects_targeted_impostors() -> None:
    base = gen.generate(4401, 2, difficulty="hard")

    wrong_shape = base[:-1]

    color_one_input = copy.deepcopy(base)
    for row in color_one_input:
        for column, value in enumerate(row):
            if value != 0:
                row[column] = 1
                break
        else:
            continue
        break

    collapsed_palette = [
        [2 if value != 0 else 0 for value in row]
        for row in base
    ]

    vertical_same_color_merge = copy.deepcopy(base)
    inserted = False
    for row, start, end, color in gen._row_runs(base):
        for neighbor_row in (row - 1, row + 1):
            if 0 <= neighbor_row < len(base):
                for column in range(start, end + 1):
                    if vertical_same_color_merge[neighbor_row][column] == 0:
                        vertical_same_color_merge[neighbor_row][column] = color
                        inserted = True
                        break
            if inserted:
                break
        if inserted:
            break
    assert inserted

    no_singletons = copy.deepcopy(base)
    for row, start, end, _color in list(gen._row_runs(no_singletons)):
        if start == end:
            no_singletons[row][start] = 0

    cases = {
        "wrong shape": wrong_shape,
        "input color 1": color_one_input,
        "collapsed palette": collapsed_palette,
        "vertical same-color merge": vertical_same_color_merge,
        "removed singleton branch": no_singletons,
    }
    for name, grid in cases.items():
        assert gen.self_check(grid), name


def test_every_three_demo_sliding_window_identifies_the_rule() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(76001, sample_index, difficulty=band)
                demos.append({"input": grid, "output": gen._oracle(grid)})
            query_grid = gen.generate(
                76001, start + gen.EXAMPLES_NEEDED, difficulty=band
            )
            assert gen.lesson_identifiable(
                demos, {"input": query_grid, "output": gen._oracle(query_grid)}
            ) == []


def test_declared_witnesses_have_real_rival_disagreements() -> None:
    grids = [gen.generate(991, index, difficulty="easy") for index in range(8)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        firings = [grid for grid in grids if witness(grid)]
        assert firings, witness_name
        for grid in firings:
            official = gen._oracle(grid)
            assert any(
                gen.SEMANTIC_RIVALS[rival_name](grid) != official
                for rival_name in gen.WITNESS_RIVALS[witness_name]
            ), witness_name
