from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "b883fcd81438"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.b883fcd81438.generator"
)


def test_rule_hash_and_all_canonical_pairs_match_python_mirror() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID)
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        source = pair["input"]
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]


def test_declared_profiles_are_exact_observable_and_semantically_live() -> None:
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            requested = {"scene_profile": profile}
            source = gen.generate(
                31_415 + index,
                index,
                difficulty=band,
                **requested,
            )
            assert gen.observe_overrides(source) == requested
            assert gen.self_check(source, meta={"overrides": requested}) == []
            assert gen.strict_canonical_like(source) == []
            expected = gen.rule_mirror(source)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                assert witness(source), (band, profile, name)
            for name, rival in gen.SEMANTIC_RIVALS.items():
                assert rival(copy.deepcopy(source)) != expected, (band, profile, name)


def test_unknown_override_and_invalid_difficulty_fail_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="compact_five")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="impossible")


def test_canonical_sparsity_and_bbox_shortcuts_are_real_then_generated_away() -> None:
    # These are not hypothetical strawmen: both reproduce every public pair.
    for pair in canonical_pairs(TASK_ID):
        source, expected = pair["input"], pair["output"]
        assert gen._rival_grow_sparsest(source) == expected
        assert gen._rival_grow_smallest_bbox(source) == expected

    # Every generated profile supplies the missing counterexample: an earlier
    # distractor is smaller/sparser, but the rule still grows panel three.
    for index, profile in enumerate(gen.SCENE_PROFILES):
        source = gen.generate(2718, index, scene_profile=profile)
        expected = gen.rule_mirror(source)
        assert gen._witness_query_not_sparsest(source)
        assert gen._witness_query_not_smallest_bbox(source)
        assert gen._rival_grow_sparsest(source) != expected
        assert gen._rival_grow_smallest_bbox(source) != expected


def test_two_demo_lessons_refute_every_named_competitor() -> None:
    for band in ("easy", "medium", "hard"):
        demos = []
        for sample_index in range(gen.EXAMPLES_NEEDED):
            source = gen.generate(73, sample_index, difficulty=band)
            demos.append({"input": source, "output": gen.rule_mirror(source)})
        query_source = gen.generate(73, gen.EXAMPLES_NEEDED, difficulty=band)
        query = {"input": query_source, "output": gen.rule_mirror(query_source)}
        assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_targeted_structural_impostors() -> None:
    source = gen.generate(99, 0, scene_profile="compact_five")

    partial_divider = copy.deepcopy(source)
    first_divider = gen._divider_columns(partial_divider)[0]
    partial_divider[0][first_divider] = 0
    assert any("exactly two" in error for error in gen.self_check(partial_divider))

    wrong_palette = copy.deepcopy(source)
    panels = gen._split_panels(wrong_palette)
    row, column = next(iter(gen._cells(panels[0])))
    # Translate panel-local column back into the first panel (same index).
    wrong_palette[row][column] = 2
    assert any("colors 0, 1, and divider color 9" in error for error in gen.self_check(wrong_palette))

    disconnected_query = copy.deepcopy(source)
    panels = gen._split_panels(disconnected_query)
    query_cells = gen._cells(panels[2])
    query_box = gen._bbox(query_cells)
    assert query_box is not None
    # Add an isolated query-colored pixel at a guaranteed border location; this
    # simultaneously tests disconnectedness and the required visible margin.
    query_start = gen._divider_columns(disconnected_query)[1] + 1
    disconnected_query[0][query_start] = 1
    errors = gen.self_check(disconnected_query)
    assert any("4-connected" in error for error in errors)
    assert any("border margin" in error for error in errors)

    empty_query = copy.deepcopy(source)
    right_divider = gen._divider_columns(empty_query)[1]
    for row in range(len(empty_query)):
        for column in range(right_divider + 1, len(empty_query[0])):
            empty_query[row][column] = 0
    assert any("panel 3 must contain" in error for error in gen.self_check(empty_query))


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(987654321)
    before = random.getstate()
    first = gen.generate(44, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(44, 9, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 8
    assert first != second
