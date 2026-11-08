"""Regressions for scalar validation and finite demonstration-only teaching."""
from __future__ import annotations

import copy
import pytest
from reviewer_support import find_root, load_selected_generator

gen, SOURCE, SOURCE_SHA256 = load_selected_generator("48fee61713bb", root=find_root(__file__))


def pair(edge):
    grid = gen._public_grid(edge)
    return {"input": grid, "output": gen.rule_mirror(grid)}


@pytest.mark.parametrize("name", ["seed", "sample_index"])
@pytest.mark.parametrize("value", [True, False, 1.5, "1"])
def test_rejects_nonliteral_integer_coordinates(name, value):
    kwargs = {"seed": 2, "sample_index": 3, name: value}
    with pytest.raises(TypeError, match=name):
        gen.generate(**kwargs)


def test_rejects_negative_sample_index():
    with pytest.raises(ValueError, match="sample_index"):
        gen.generate(seed=2, sample_index=-1)


def test_signed_integer_seed_remains_supported():
    assert gen.generate(-1, 0) == gen.generate(-1, 0)


def test_strict_contract_accepts_canonical_and_rejects_broken_ring():
    for edge in range(4):
        grid = gen._public_grid(edge)
        assert gen.strict_canonical_like(grid) == []
    broken = gen._public_grid(0)
    row, col = next((r, c) for r, row in enumerate(broken) for c, v in enumerate(row) if v == 8)
    broken[row][col] = 0
    assert gen.strict_canonical_like(broken)


def test_declared_witnesses_are_nonvacuous_and_refute_named_rivals():
    seen = set()
    grids = [gen._public_grid(edge) for edge in range(4)]
    grids += [gen.generate(19, i, difficulty=band) for band in ("easy", "medium", "hard") for i in range(8)]
    for grid in grids:
        expected = gen.rule_mirror(grid)
        before = copy.deepcopy(grid)
        for name, predicate in gen.SEMANTIC_WITNESSES.items():
            fired = predicate(grid)
            assert type(fired) is bool
            if fired:
                seen.add(name)
                if name not in gen.BRANCH_WITNESSES:
                    rivals = gen.WITNESS_RIVALS[name]
                    assert any(gen.SEMANTIC_RIVALS[rival](grid) != expected for rival in rivals), name
        assert grid == before
    assert seen == set(gen.SEMANTIC_WITNESSES)


def test_fitting_fixed_side_rival_flags_underspecified_demonstrations():
    # Both demonstrations put the main on the high side; the query needs low.
    demos = [pair(0), pair(1)]
    query = pair(2)
    assert gen.LESSON_COMPETITORS["fixed_main_at_end"](query["input"]) != query["output"]
    reasons = gen.lesson_identifiable(demos, query)
    assert any("fixed_main_at_end" in reason for reason in reasons)


def test_rich_demonstrations_identify_each_query_without_reading_its_answer():
    demos = [pair(0), pair(1), pair(2)]
    original = copy.deepcopy(demos)
    for edge in range(4):
        query = pair(edge)
        assert gen.lesson_identifiable(demos, query) == []
        assert gen.lesson_identifiable(demos, {"input": query["input"]}) == []
        assert gen.lesson_identifiable(demos, {"input": query["input"], "output": [[9]]}) == []
    assert demos == original
    assert gen.lesson_identifiable([], pair(0))


def test_every_holdout_of_four_linked_orientations_is_identifiable():
    pairs = [pair(edge) for edge in range(4)]
    for held_out in range(4):
        demos = [p for i, p in enumerate(pairs) if i != held_out]
        assert gen.lesson_identifiable(demos, pairs[held_out]) == []
