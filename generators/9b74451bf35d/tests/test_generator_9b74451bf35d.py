from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


gen = importlib.import_module("puzzle_generators.per_puzzle.9b74451bf35d.generator")


def _transform_of(grid):
    a = gen._mask(gen._panel(grid, 0))
    b = gen._mask(gen._panel(grid, 1))
    matches = gen._matching_transforms(a, b)
    assert len(matches) == 1
    return matches[0]


def test_canonical_pairs_are_accepted_and_mirrored_exactly():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID)


def test_generated_roles_and_full_d4_uniqueness():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = gen.generate(78123, sample_index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen._teaching_reasons(grid) == []
            a, b, c = (gen._panel(grid, i) for i in range(3))
            assert gen._panel_color(a) == gen._panel_color(c)
            assert gen._panel_color(b) != gen._panel_color(a)
            assert gen._full_d4_orbit(gen._mask(a))
            assert gen._full_d4_orbit(gen._mask(c))


def test_every_sliding_four_demo_window_contains_all_transform_branches():
    expected = set(gen._NORMAL_TRANSFORMS)
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            transforms = {
                _transform_of(gen.generate(9000 + start, index, difficulty=difficulty))
                for index in range(start, start + gen.EXAMPLES_NEEDED)
            }
            assert transforms == expected


def test_lesson_identifiable_for_every_schedule_residue():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(4):
            seed = 4242 + start
            demos = []
            for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=difficulty)
            assert gen.lesson_identifiable(
                demos,
                {"input": query_grid, "output": gen.rule_mirror(query_grid)},
            ) == []


def test_override_axes_round_trip_and_unknown_keys_reject():
    for source_cells in range(3, 7):
        for query_cells in range(3, 7):
            grid = gen.generate(
                12345,
                source_cells * 10 + query_cells,
                difficulty="hard",
                source_cells=source_cells,
                query_cells=query_cells,
            )
            assert gen.observe_overrides(grid) == {
                "source_cells": source_cells,
                "query_cells": query_cells,
            }
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __typo_axis=3)


def test_targeted_impostors_are_rejected():
    base = gen.generate(777, 2, difficulty="medium")

    bad_separator = copy.deepcopy(base)
    bad_separator[0][3] = 9
    assert gen.self_check(bad_separator)

    bad_role_color = copy.deepcopy(base)
    source_color = gen._panel_color(gen._panel(base, 0))
    for r in range(3):
        for c in range(8, 11):
            if bad_role_color[r][c] == source_color:
                bad_role_color[r][c] = 9 if source_color != 9 else 8
    assert any("A and C" in msg for msg in gen.self_check(bad_role_color))

    multi_color_panel = copy.deepcopy(base)
    first = next((r, c) for r in range(3) for c in range(3) if multi_color_panel[r][c])
    multi_color_panel[first[0]][first[1]] = 9 if multi_color_panel[first[0]][first[1]] != 9 else 8
    assert any("monochrome" in msg for msg in gen.self_check(multi_color_panel))

    ambiguous = [[0] * 11 for _ in range(3)]
    ambiguous[1][1] = 2
    ambiguous[1][5] = 5
    ambiguous[1][9] = 2
    assert any("ambiguous" in msg for msg in gen.self_check(ambiguous))

    impossible = copy.deepcopy(base)
    # Toggle one B support cell so no rigid transform can preserve A's cell count.
    for r in range(3):
        for c in range(4, 7):
            if impossible[r][c] == 0:
                impossible[r][c] = gen._panel_color(gen._panel(base, 1))
                break
        else:
            continue
        break
    assert any("no canonical transform" in msg for msg in gen.self_check(impossible))


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(987654321)
    before = random.getstate()
    first = gen.generate(456, 7, difficulty="hard")
    after = random.getstate()
    second = gen.generate(456, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert before == after
