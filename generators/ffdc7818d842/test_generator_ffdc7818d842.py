from __future__ import annotations

import copy
import importlib

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.ffdc7818d842.generator")


def test_all_canonical_pairs_are_accepted_and_match_the_rule():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 10
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(original) == []
        assert gen.strict_canonical_like(original) == []
        assert gen.rule_mirror(original) == pair["output"]
        assert original == pair["input"]


def test_every_profile_is_exactly_observable_and_non_degenerate():
    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(1000 + index, index, scene_profile=profile)
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert gen.self_check(grid, meta={"overrides": {"scene_profile": profile}}) == []
        assert gen.strict_canonical_like(grid) == []
        output = gen.rule_mirror(grid)
        assert output != grid
        assert any(value == 9 for row in output for value in row)


def test_unknown_overrides_profiles_and_difficulty_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="left")
    with pytest.raises(ValueError, match="unknown scene_profile"):
        gen.generate(1, 0, scene_profile="not-a-profile")
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 0, difficulty="impossible")


@pytest.mark.parametrize(
    "mutator, message",
    [
        (lambda g: g[0].append(0), "rectangular"),
        (lambda g: g.__setitem__(0, [8] + g[0][1:]), "exactly one"),
        (lambda g: g.__setitem__(1, [7] + g[1][1:]), "unexpected input colors"),
        (lambda g: [row.__setitem__(c, 0) for row in g for c, v in enumerate(row) if v == 8], "exactly one"),
        (lambda g: [row.__setitem__(c, 0) for row in g for c, v in enumerate(row) if v == 1], "at least one"),
    ],
)
def test_structural_mutations_are_rejected(mutator, message):
    grid = gen.generate(19, 2, difficulty="medium")
    mutator(grid)
    assert any(message in error for error in gen.self_check(grid))


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
                gen._analysis(pair["input"])["direction"] for pair in demos
            } == {"left", "up", "right", "down"}
            for rival in gen.LESSON_COMPETITORS.values():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_generate_is_deterministic_and_returns_fresh_grids():
    a = gen.generate(221, 7, difficulty="hard")
    b = gen.generate(221, 7, difficulty="hard")
    assert a == b
    assert a is not b
    assert all(row_a is not row_b for row_a, row_b in zip(a, b))
