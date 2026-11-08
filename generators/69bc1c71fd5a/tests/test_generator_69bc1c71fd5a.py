from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


gen = importlib.import_module("puzzle_generators.per_puzzle.69bc1c71fd5a.generator")


def _pair(grid):
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_all_canonical_pairs_are_accepted_and_solved():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(original) == []
        assert gen.strict_canonical_like(original) == []
        assert gen.rule_mirror(original) == pair["output"]
        assert original == pair["input"]


def test_every_scene_profile_is_exactly_observable_in_every_band():
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(gen.SCENE_PROFILES):
            grid = gen.generate(
                1000 + index,
                index,
                difficulty=band,
                scene_profile=profile,
            )
            assert gen.self_check(
                grid, meta={"overrides": {"scene_profile": profile}}
            ) == []
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            assert (gen.strict_canonical_like(grid) == []) == profile.startswith("canon_")


def test_unknown_overrides_and_bad_profiles_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="canon_7x7_l3")
    with pytest.raises(ValueError, match="unknown scene_profile"):
        gen.generate(1, 0, scene_profile="not-a-profile")
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 0, difficulty="impossible")


def test_self_check_rejects_targeted_structural_impostors():
    base = gen.generate(17, 1, difficulty="medium", scene_profile="multi_9x10_l3_t4")

    two_anchors = copy.deepcopy(base)
    two_anchors[0][0] = 9
    assert any("exactly one" in error for error in gen.self_check(two_anchors))

    unsupported_shape = copy.deepcopy(base)
    # Extend one colored motif by one isolated cell: either disconnected or an
    # unsupported morphology, both of which are outside the teaching grammar.
    color = next(v for row in unsupported_shape for v in row if v not in (0, 9))
    unsupported_shape[0][0] = color
    assert any(
        token in error
        for error in gen.self_check(unsupported_shape)
        for token in ("one 4-connected motif", "unsupported motif morphology")
    )

    out_of_bounds_rotation = [[0] * 6 for _ in range(7)]
    out_of_bounds_rotation[0][0] = 9
    out_of_bounds_rotation[5][3] = 2
    out_of_bounds_rotation[6][3] = 2
    out_of_bounds_rotation[6][4] = 2
    assert any("leaves the grid" in error for error in gen.self_check(out_of_bounds_rotation))

    rotationally_hidden = [[0] * 7 for _ in range(7)]
    rotationally_hidden[3][3] = 9
    # Four L3-shaped colored components are not a declared profile and make the
    # before/after occupancy rotationally symmetric.
    for r, c in ((1, 1), (2, 1), (2, 2)):
        rotationally_hidden[r][c] = 1
    for r, c in ((1, 5), (1, 4), (2, 4)):
        rotationally_hidden[r][c] = 2
    for r, c in ((5, 5), (4, 5), (4, 4)):
        rotationally_hidden[r][c] = 3
    for r, c in ((5, 1), (5, 2), (4, 2)):
        rotationally_hidden[r][c] = 4
    assert gen.self_check(rotationally_hidden)


def test_generation_is_replayable_fresh_and_global_rng_neutral():
    random.seed(987654321)
    state = random.getstate()
    first = gen.generate(88, 5, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(88, 5, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(88, 5, difficulty="hard")


def test_every_three_demo_window_falsifies_named_rivals():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = [
                _pair(gen.generate(410, start + offset, difficulty=band))
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            query = _pair(gen.generate(410, start + gen.EXAMPLES_NEEDED, difficulty=band))
            assert gen.lesson_identifiable(demos, query) == []
            for competitor in gen.LESSON_COMPETITORS.values():
                assert any(
                    competitor(pair["input"]) != pair["output"]
                    for pair in demos
                )


def test_negative_recombination_is_rejected_while_rule_still_has_a_defined_output():
    grid = gen.generate(77, 0, scene_profile="canon_7x7_l3")
    anchor = next(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 9
    )
    color = next(value for row in grid for value in row if value not in (0, 9))
    impostor = [[0] * 7 for _ in range(7)]
    impostor[anchor[0]][anchor[1]] = 9
    # A straight triomino is absent from all declared profiles. It remains a
    # mathematically valid input to the rotation rule but is rejected by the
    # teaching distribution.
    candidates = [((1, 1), (1, 2), (1, 3)), ((5, 1), (5, 2), (5, 3))]
    cells = next(
        cells
        for cells in candidates
        if all(0 <= gen._rotate_point(r, c, anchor)[0] < 7 and 0 <= gen._rotate_point(r, c, anchor)[1] < 7 for r, c in cells)
    )
    for r, c in cells:
        impostor[r][c] = color
    assert gen.self_check(impostor)
    output = gen.rule_mirror(impostor)
    assert len(output) == 7 and all(len(row) == 7 for row in output)
