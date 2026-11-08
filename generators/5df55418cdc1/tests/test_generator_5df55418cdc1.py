from __future__ import annotations

import copy
import importlib
import random

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "5df55418cdc1"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def test_canonical_inputs_are_accepted_and_outputs_match_mirror():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_generated_scene_has_clockwise_demo_and_blank_destination():
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(
            12345,
            7,
            difficulty=band,
            top_palette_size=2,
            query_palette_size=3,
        )
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert all(witness(grid) for witness in gen.SEMANTIC_WITNESSES.values())
        official = gen.rule_mirror(grid)
        assert official != grid
        for rival in gen.SEMANTIC_RIVALS.values():
            assert rival(grid) != official


def test_exact_overrides_are_observable_and_unknown_keys_reject():
    grid = gen.generate(
        91,
        3,
        difficulty="easy",
        top_palette_size=2,
        query_palette_size=3,
        top_cells=3,
        query_cells=10,
    )
    assert gen.observe_overrides(grid) == {
        "top_palette_size": 2,
        "query_palette_size": 3,
        "top_cells": 3,
        "query_cells": 10,
    }
    try:
        gen.generate(1, 0, bogus_axis=1)
    except ValueError as exc:
        assert "unknown override" in str(exc)
    else:
        raise AssertionError("unknown override key was accepted")


def test_self_check_rejects_targeted_structural_impostors():
    base = gen.generate(7, 2, difficulty="medium")
    mutants = []

    broken_row = copy.deepcopy(base)
    broken_row[5][0] = 0
    mutants.append(broken_row)

    broken_col = copy.deepcopy(base)
    broken_col[0][5] = 0
    mutants.append(broken_col)

    wrong_demo = copy.deepcopy(base)
    wrong_demo[0][6] = 0 if wrong_demo[0][6] else 1
    mutants.append(wrong_demo)

    filled_destination = copy.deepcopy(base)
    filled_destination[10][10] = 4
    mutants.append(filled_destination)

    empty_query = copy.deepcopy(base)
    for r in range(6, 11):
        for c in range(5):
            empty_query[r][c] = 0
    mutants.append(empty_query)

    assert all(gen.self_check(mutant) for mutant in mutants)


def test_deterministic_fresh_returns_and_global_rng_purity():
    random.seed(2026)
    before = random.getstate()
    first = gen.generate(314159, 11, difficulty="hard")
    after = random.getstate()
    second = gen.generate(314159, 11, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    first[0][0] = 9
    assert second[0][0] != 9


def test_every_two_consecutive_default_demos_include_multicolor_query():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            palettes = []
            for sample_index in (start, start + 1):
                grid = gen.generate(7000 + start, sample_index, difficulty=band)
                palettes.append(gen.observe_overrides(grid)["query_palette_size"])
            assert 2 in palettes
