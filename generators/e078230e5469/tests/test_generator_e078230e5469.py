from __future__ import annotations

import copy
import random

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "e078230e5469"
ROOT = find_root(__file__)
gen, GENERATOR_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)

ALL_TRANSFORMS = (
    "id",
    "rot90",
    "rot180",
    "rot270",
    "flip_h",
    "flip_v",
    "transpose",
    "anti",
)
PALETTE_KINDS = ("default", "warm", "cool", "varied")


def _pairs():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _lesson(seed: int, start: int, difficulty: str, n_demos: int):
    grids = [gen.generate(seed, start + i, difficulty=difficulty) for i in range(n_demos)]
    demos = [{"input": grid, "output": gen._apply_rule(grid)} for grid in grids]
    query_grid = gen.generate(seed, start + n_demos, difficulty=difficulty)
    query = {"input": query_grid, "output": gen._apply_rule(query_grid)}
    return grids, demos, query


def test_rule_pin_and_canonical_pairs_remain_exact():
    assert gen.RULE_HASH == "b95936763d1c"
    for pair in _pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._apply_rule(pair["input"]) == pair["output"]


def test_advertised_override_axes_are_exact_observable_and_strict():
    case = 0
    for difficulty in ("easy", "medium", "hard"):
        for square_size in (3, 6):
            for transform in ALL_TRANSFORMS:
                for palette_kind in PALETTE_KINDS:
                    requested = {
                        "square_size": square_size,
                        "transform": transform,
                        "palette_kind": palette_kind,
                    }
                    grid = gen.generate(10_000 + case, case, difficulty=difficulty, **requested)
                    assert gen.observe_overrides(grid) == requested
                    assert gen._teaching_reasons(grid) == []
                    case += 1

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, typo_axis=123)
    with pytest.raises(ValueError):
        gen.generate(1, 2, transform="bogus")
    with pytest.raises(ValueError):
        gen.generate(1, 2, palette_kind="bogus")
    for bad in (2, 7, True, 4.0, "4"):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 2, square_size=bad)


def test_every_eight_draw_window_covers_every_transform_once():
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 1, 17, 991):
            for start in (0, 3, 11):
                grids, _, _ = _lesson(seed, start, difficulty, 8)
                assert {gen.schedule_profile(seed, start + i, difficulty) for i in range(8)} == set(ALL_TRANSFORMS)
                assert {gen._infer_transform(grid) for grid in grids} == set(ALL_TRANSFORMS)


def test_every_twenty_draw_band_has_canonical_profile_support():
    for difficulty in ("easy", "medium", "hard"):
        grids = [gen.generate(29, index, difficulty=difficulty) for index in range(20)]
        exact = [
            grid
            for grid in grids
            if len(grid) == 5
            and {len(row) for row in grid} == {17}
            and len({value for row in grid for value in row}) == 4
        ]
        assert len(exact) >= 1
        assert all(gen.strict_canonical_like(grid) == [] for grid in grids)
        assert all(gen._teaching_reasons(grid) == [] for grid in grids)


def test_generated_motifs_are_connected_unambiguous_and_query_separating():
    for difficulty in ("easy", "medium", "hard"):
        for index in range(64):
            grid = gen.generate(40_000 + index, index * 7 + 3, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            assert gen._teaching_reasons(grid) == []
            a, b, c = gen._panels(grid)
            assert len(gen._matching_transforms(a, b)) == 1
            assert gen._is_connected(gen._support(a))
            assert gen._is_connected(gen._support(c))
            assert len({gen._freeze(gen._transform(c, name)) for name in ALL_TRANSFORMS}) == 8


def test_structural_impostors_are_rejected():
    source = gen.generate(41_001, 5, difficulty="medium")
    cases = {}

    cases["blank"] = [[0 for _ in row] for row in source]

    wrong_divider = copy.deepcopy(source)
    wrong_divider[0][len(source)] = 0
    cases["wrong_divider"] = wrong_divider

    multicolor_a = copy.deepcopy(source)
    for r, row in enumerate(multicolor_a):
        changed = False
        for c in range(len(source)):
            if row[c] != 0:
                row[c] = 9 if row[c] != 9 else 8
                changed = True
                break
        if changed:
            break
    cases["multicolor_a"] = multicolor_a

    empty_query = copy.deepcopy(source)
    n = len(source)
    for r in range(n):
        for c in range(2 * n + 2, 3 * n + 2):
            empty_query[r][c] = 0
    cases["empty_query"] = empty_query

    cases["bad_width"] = [row[:-1] for row in source]
    cases["bad_cell"] = copy.deepcopy(source)
    cases["bad_cell"][0][0] = True

    for name, grid in cases.items():
        assert gen.self_check(grid), name


def test_declared_rivals_fit_or_are_refuted_as_claimed():
    shortcut = gen.CANONICAL_SHORTCUTS["observed_transform_family_only"]
    for pair in _pairs():
        assert shortcut(pair["input"]) == pair["output"]

    examples = [gen.generate(91, index, difficulty="hard") for index in range(24)]
    for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
        firing = [grid for grid in examples if witness(grid)]
        assert firing, witness_name
        for rival_name in gen.WITNESS_RIVALS[witness_name]:
            rival = gen.SEMANTIC_RIVALS[rival_name]
            assert any(rival(grid) != gen._apply_rule(grid) for grid in firing), (witness_name, rival_name)


def test_five_demo_lessons_refute_every_declared_competitor():
    assert gen.EXAMPLES_NEEDED == 5
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 1, 17, 991):
            for start in range(len(ALL_TRANSFORMS)):
                _, demos, query = _lesson(seed, start, difficulty, gen.EXAMPLES_NEEDED)
                assert gen.lesson_identifiable(demos, query) == []
                for rival_name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(rival(demo["input"]) != demo["output"] for demo in demos), rival_name



def test_call_arguments_reject_invalid_scalars():
    for bad_seed in (True, False, 1.0, 1.75, "1"):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(bad_seed, 0, difficulty="easy")
    for bad_index in (True, False, 1.0, 1.75, "1", -1):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(991, bad_index, difficulty="easy")
    for bad_difficulty in (True, False, 0, 1.0, "__invalid_difficulty__"):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(991, 0, difficulty=bad_difficulty)

def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20261019)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second
