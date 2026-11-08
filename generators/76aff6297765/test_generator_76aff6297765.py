"""Focused regression checks for generator 76aff6297765."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.76aff6297765.generator")


def _canonical_inputs():
    return [pair["input"] for pair in canonical_pairs(gen.TASK_ID)]


def test_canonical_inputs_are_accepted_and_strict():
    inputs = _canonical_inputs()
    assert len(inputs) == 5
    for grid in inputs:
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid)


def test_every_generated_draw_exposes_all_four_relations():
    for band in ("easy", "medium", "hard"):
        strict = 0
        same_colour = 0
        for sample_index in range(80):
            grid = gen.generate(1000 + sample_index, sample_index, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            info = gen._analysis(grid)
            assert all(count > 0 for count in info["joint_counts"].values())
            strict += gen.strict_canonical_like(grid) == []
            same_colour += info["top_color"] == info["bot_color"]
        assert strict >= 20
        assert same_colour >= 30


def test_same_colour_examples_refute_equal_cell_shortcut():
    grid = gen.generate(17, 1, difficulty="medium")
    info = gen._analysis(grid)
    assert info["top_color"] == info["bot_color"]
    assert gen._rival_equal_cells(grid) != gen.rule_mirror(grid)


def test_exact_override_boundaries_and_unknown_key_rejection():
    for panel_h, panel_w, top_color, bot_color in (
        (3, 3, 1, 1),
        (8, 8, 9, 9),
        (6, 4, 2, 6),
    ):
        grid = gen.generate(
            31,
            7,
            difficulty="easy",
            panel_h=panel_h,
            panel_w=panel_w,
            top_color=top_color,
            bot_color=bot_color,
        )
        assert gen.observe_overrides(grid) == {
            "panel_h": panel_h,
            "panel_w": panel_w,
            "top_color": top_color,
            "bot_color": bot_color,
        }
    with pytest.raises(ValueError, match="unknown override axis"):
        gen.generate(0, 0, typo_axis=3)


def test_determinism_fresh_returns_and_global_rng_purity():
    state = random.getstate()
    first = gen.generate(23, 7, difficulty="medium")
    second = gen.generate(23, 7, difficulty="medium")
    assert first == second
    assert first is not second
    first[0][0] = 9 if first[0][0] != 9 else 6
    assert gen.generate(23, 7, difficulty="medium") == second
    assert random.getstate() == state


def test_self_check_rejects_decisive_mutations():
    base = gen.generate(41, 3, difficulty="medium")
    info = gen._analysis(base)

    missing_separator = copy.deepcopy(base)
    missing_separator[info["separator"]][0] = 0
    assert gen.self_check(missing_separator)

    extra_separator = copy.deepcopy(base)
    extra_separator[0] = [7] * len(extra_separator[0])
    assert gen.self_check(extra_separator)

    unequal_panels = copy.deepcopy(base[:-1])
    assert gen.self_check(unequal_panels)

    leaked_output_colour = copy.deepcopy(base)
    leaked_output_colour[0][0] = 8
    assert gen.self_check(leaked_output_colour)

    two_top_foregrounds = copy.deepcopy(base)
    replacement = 9 if info["top_color"] != 9 else 6
    for row in range(info["panel_h"]):
        for col in range(info["panel_w"]):
            if two_top_foregrounds[row][col] == info["top_color"]:
                two_top_foregrounds[row][col] = replacement
                assert gen.self_check(two_top_foregrounds)
                return
    raise AssertionError("generated panel unexpectedly had no foreground cell")


def test_consecutive_lessons_are_identifiable():
    for start in range(20):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(91, sample_index, difficulty="hard")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(91, start + gen.EXAMPLES_NEEDED, difficulty="hard")
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
