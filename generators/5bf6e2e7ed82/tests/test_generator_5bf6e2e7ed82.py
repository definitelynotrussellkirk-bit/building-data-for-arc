from __future__ import annotations

import copy
import importlib
import itertools
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs

TASK_ID = "5bf6e2e7ed82"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.5bf6e2e7ed82.generator"
)


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_pairs_are_accepted_and_mirrored():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_four_sample_schedule_covers_xor_branches_and_identifies_every_window():
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(8000 + i, i, difficulty=band) for i in range(12)]
        for start in range(8):
            window = grids[start : start + 5]
            demos = [_pair(grid) for grid in window[:4]]
            query = _pair(window[4])
            assert gen.lesson_identifiable(demos, query) == []

        facts = [gen._analyze(grid) for grid in grids[:4]]
        assert {
            gen._relation_kind(item["source"], item["target"])
            for item in facts
        } == {"mixed", "target_subset", "source_subset", "disjoint"}
        assert {
            gen._match_position(item["match_index"], len(item["candidates"]))
            for item in facts
        } == {"first", "middle", "last"}
        assert {gen.observe_overrides(grid)["palette_kind"] for grid in grids[:4]} == {
            "canonical",
            "varied",
        }


def test_exact_override_boundaries_are_observable_and_unknown_keys_fail():
    domains = {
        "panel_h": (4, 5),
        "n_panels": (5, 6),
        "source_size": (2, 7),
        "target_size": (1, 7),
        "match_position": ("first", "middle", "last"),
        "palette_kind": ("canonical", "varied"),
    }
    keys = tuple(domains)
    for index, values in enumerate(itertools.product(*(domains[key] for key in keys))):
        overrides = dict(zip(keys, values))
        grid = gen.generate(17000 + index, index, difficulty="hard", **overrides)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)


def test_self_check_rejects_six_targeted_impostors():
    base = gen.generate(23, 1, difficulty="medium")
    facts = gen._analyze(base)
    assert facts["errors"] == []

    no_divider = copy.deepcopy(base)
    for row in no_divider:
        row[4] = 0
    assert gen.self_check(no_divider)

    empty_target = copy.deepcopy(base)
    for row in empty_target:
        for c in range(5, 9):
            row[c] = 0
    assert any("panel 1 is empty" in reason for reason in gen.self_check(empty_target))

    duplicate_match = copy.deepcopy(base)
    true_index = facts["match_index"]
    other_index = 0 if true_index != 0 else 1
    true_cells = facts["candidates"][true_index]
    other_panel = other_index + 2
    c0 = other_panel * 5
    for row in duplicate_match:
        for c in range(c0, c0 + 4):
            row[c] = 0
    color = facts["colors"][other_panel]
    for r, c in true_cells:
        duplicate_match[r][c0 + c] = color
    duplicate_errors = gen.self_check(duplicate_match)
    assert any("candidate occupancies must be distinct" in reason for reason in duplicate_errors)
    assert any("exactly one XOR-matching candidate" in reason for reason in duplicate_errors)

    multicolor_source = copy.deepcopy(base)
    source_cells = sorted(facts["source"])
    r, c = source_cells[0]
    multicolor_source[r][c] = 8 if facts["colors"][0] != 8 else 7
    assert any("panel 0 must be monochrome" in reason for reason in gen.self_check(multicolor_source))

    ragged = copy.deepcopy(base)
    ragged[0].pop()
    assert any("rectangular" in reason for reason in gen.self_check(ragged))

    wide_separator = copy.deepcopy(base)
    for row in wide_separator:
        row[5] = 9
    assert gen.self_check(wide_separator)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    before = random.getstate()
    first = gen.generate(991, 7, difficulty="easy")
    after = random.getstate()
    second = gen.generate(991, 7, difficulty="easy")
    assert before == after == random.getstate()
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_canonical_difference_shortcut_is_refuted_by_mixed_profile():
    for pair in canonical_pairs(TASK_ID):
        assert gen._rival_set_difference(pair["input"]) == pair["output"]

    mixed = gen.generate(44, 0, difficulty="hard")
    assert gen._relation_kind(
        gen._analyze(mixed)["source"], gen._analyze(mixed)["target"]
    ) == "mixed"
    assert gen._rival_set_difference(mixed) != gen.rule_mirror(mixed)
