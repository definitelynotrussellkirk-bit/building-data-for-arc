from __future__ import annotations

import copy
import importlib
import random

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.38300735cc4d.generator")
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


TASK_ID = "38300735cc4d"


def test_rule_pin_and_all_canonical_pairs() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "e1f30dfc7d44"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_every_five_step_window_identifies_the_rule() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(len(gen.SCENE_PROFILES)):
            grids = [
                gen.generate(8100 + band_index, start + offset, difficulty=band)
                for offset in range(6)
            ]
            demos = [
                {"input": grid, "output": gen.rule_mirror(grid)}
                for grid in grids[:5]
            ]
            query = {"input": grids[5], "output": gen.rule_mirror(grids[5])}
            assert gen.lesson_identifiable(demos, query) == [], (band, start)

            for witness_name, rival_names in gen.WITNESS_RIVALS.items():
                witness_grid = next(
                    grid
                    for grid in grids[:5]
                    if gen.SEMANTIC_WITNESSES[witness_name](grid)
                )
                answer = gen.rule_mirror(witness_grid)
                for rival_name in rival_names:
                    assert gen.SEMANTIC_RIVALS[rival_name](witness_grid) != answer


def test_override_boundaries_are_exact_observable_and_band_safe() -> None:
    case_index = 0
    for band in ("easy", "medium", "hard"):
        for grid_h in (6, 12):
            for grid_w in (6, 12):
                for scene_profile in gen.SCENE_PROFILES:
                    requested = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "scene_profile": scene_profile,
                    }
                    grid = gen.generate(
                        30_000 + case_index,
                        case_index * 7 + 3,
                        difficulty=band,
                        **requested,
                    )
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == requested
                    assert gen.rule_mirror(grid) != grid
                    case_index += 1

    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)


@pytest.mark.parametrize(
    "axis,value",
    [
        ("grid_h", 5),
        ("grid_h", 13),
        ("grid_w", 5),
        ("grid_w", 13),
        ("scene_profile", "all_blocked"),
    ],
)
def test_invalid_override_values_reject(axis: str, value: object) -> None:
    with pytest.raises(ValueError):
        gen.generate(7, 9, difficulty="hard", **{axis: value})


def test_replay_freshness_and_global_rng_purity() -> None:
    random.seed(20260817)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_targeted_mutation_impostors_are_rejected() -> None:
    grid = gen.generate(17, 5, difficulty="medium")
    assert gen.self_check(grid) == []
    impostors = gen.mutation_impostors(grid)
    assert len(impostors) >= 4
    for name, impostor in impostors:
        assert gen.self_check(impostor), name


def test_default_census_keeps_profiles_and_witnesses_live_in_every_band() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        profiles = set()
        witness_counts = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        strict = 0
        for sample_index in range(72):
            grid = gen.generate(700_000 + band_index, sample_index, difficulty=band)
            assert gen.self_check(grid) == []
            facts = gen.semantic_observables(grid)
            profiles.add(facts["scene_profile"])
            strict += int(gen.strict_canonical_like(grid) == [])
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                witness_counts[name] += int(witness(grid))
        assert profiles == set(gen.SCENE_PROFILES)
        assert strict > 0
        assert all(count > 0 for count in witness_counts.values())


def test_negative_branch_rivals_are_branch_isolated() -> None:
    cases = {
        "blocked": "ignore_blockers",
        "count_decoy": "fill_extrema_any_count",
        "alignment_decoy": "fill_bbox_for_two",
    }
    branch_rivals = set(cases.values())
    for offset, (profile, expected_rival) in enumerate(cases.items()):
        grid = gen.generate(
            880_000 + offset,
            offset,
            difficulty="hard",
            scene_profile=profile,
            grid_h=10,
            grid_w=10,
        )
        truth = gen.rule_mirror(grid)
        for rival_name in branch_rivals:
            rival_output = gen.SEMANTIC_RIVALS[rival_name](grid)
            assert (rival_output != truth) is (rival_name == expected_rival), (
                profile,
                rival_name,
            )


@pytest.mark.parametrize("scene_profile", ("blocked", "mixed"))
def test_blocker_profiles_refute_blocker_count_shortcuts(scene_profile: str) -> None:
    grid = gen.generate(
        990_001,
        7,
        difficulty="hard",
        scene_profile=scene_profile,
        grid_h=8,
        grid_w=8,
    )
    facts = gen.semantic_observables(grid)
    blocker_color_counts = []
    for pair in facts["blocked_pairs"]:
        assert len(pair["blocker_cells"]) == 1
        row, col = pair["blocker_cells"][0]
        blocker_color_counts.append(len(facts["positions"][grid[row][col]]))

    assert sorted(blocker_color_counts) == [1, 3]
    assert len(facts["scattered_blockers"]) == 1

    truth = gen.rule_mirror(grid)
    assert gen.SEMANTIC_RIVALS["block_only_singletons"](grid) != truth
    assert gen.SEMANTIC_RIVALS["block_only_repeated"](grid) != truth
