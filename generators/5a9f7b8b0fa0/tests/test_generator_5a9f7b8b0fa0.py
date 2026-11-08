from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs

TASK_ID = "5a9f7b8b0fa0"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _pairs():
    return canonical_pairs(TASK_ID)


def test_rule_hash_and_all_canonical_pairs_are_synchronized():
    assert GEN.RULE_HASH == "9c7ed54a3ebf"
    pairs = _pairs()
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_every_sliding_four_demo_window_identifies_the_next_query():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            lesson = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(1000 + sample_index, sample_index, difficulty=band)
                lesson.append({"input": grid, "output": GEN.rule_mirror(grid)})
            assert GEN.lesson_identifiable(lesson[:-1], lesson[-1]) == []


def test_schedule_exposes_all_decisive_semantics_in_each_band():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(2000 + index, index, difficulty=band) for index in range(4)]
        signatures = [GEN.semantic_signature(grid) for grid in grids]
        assert {item["relation_pattern"] for item in signatures} == {
            "strict", "mixed_ties"
        }
        assert {item["color_mode"] for item in signatures} == {
            "monochrome", "multicolor"
        }
        assert any(item["strict_canonical_like"] for item in signatures)
        assert any(item["panel_width_rival_disagrees"] for item in signatures)
        assert any(item["color_count_rival_disagrees"] for item in signatures)
        assert any(GEN._has_off_diagonal_equality(grid) for grid in grids)
        assert any(GEN._has_unequal_area_branch(grid) for grid in grids)


def test_exact_override_boundaries_are_observable_across_bands():
    cases = (
        {"grid_h": 5},
        {"grid_h": 8},
        {"panel_count": 3},
        {"panel_count": 4},
        {"panel_width": 4},
        {"panel_width": 6},
        {"relation_pattern": "strict"},
        {"relation_pattern": "mixed_ties"},
        {"relation_pattern": "all_equal"},
        {"color_mode": "monochrome"},
        {"color_mode": "multicolor"},
    )
    for band in ("easy", "medium", "hard"):
        for index, case in enumerate(cases):
            grid = GEN.generate(3000 + index, 9 + index, difficulty=band, **case)
            observed = GEN.observe_overrides(grid)
            for key, value in case.items():
                assert observed[key] == value
            assert GEN.self_check(grid, meta={"overrides": case}) == []


def test_unknown_and_invalid_overrides_reject_loudly():
    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(0, 0, imaginary_axis=4)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, grid_h=4)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, relation_pattern="diagonal_only")


def test_self_check_rejects_four_structural_impostor_classes():
    original = GEN.generate(4000, 1, difficulty="medium")
    assert GEN.self_check(original) == []
    analysis = GEN._analyze(original)
    separator = analysis["panels"][0]["right"]

    broken_separator = copy.deepcopy(original)
    broken_separator[0][separator] = 0
    assert any("outside full-height" in error or "panels" in error
               for error in GEN.self_check(broken_separator))

    adjacent_separator = copy.deepcopy(original)
    for row in range(len(adjacent_separator)):
        adjacent_separator[row][separator + 1] = 8
    assert any("adjacent separator" in error for error in GEN.self_check(adjacent_separator))

    empty_panel = copy.deepcopy(original)
    first = analysis["panels"][0]
    for row in range(len(empty_panel)):
        for col in range(first["left"], first["right"]):
            empty_panel[row][col] = 0
    assert any("no non-{0,8} content" in error for error in GEN.self_check(empty_panel))

    ragged = copy.deepcopy(original)
    ragged[-1].pop()
    assert GEN.self_check(ragged)


def test_negative_recombination_is_distribution_invalid_but_oracle_executable():
    grid = GEN.generate(5000, 0, difficulty="easy")
    analysis = GEN._analyze(grid)
    separators = [panel["right"] for panel in analysis["panels"][:-1]]
    replacement = next(color for color in range(1, 10)
                       if color != 8 and all(color not in row for row in grid))
    mutated = copy.deepcopy(grid)
    for row in range(len(mutated)):
        mutated[row][separators[0]] = replacement
    assert GEN.self_check(mutated)
    output = GEN.rule_mirror(mutated)
    assert len(output) == 2 and all(len(row) == 2 for row in output)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(987654321)
    before = random.getstate()
    first = GEN.generate(77, 19, difficulty="hard")
    middle = GEN.generate(78, 20, difficulty="easy")
    second = GEN.generate(77, 19, difficulty="hard")
    after = random.getstate()
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert middle != first
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert GEN.generate(77, 19, difficulty="hard") == second
