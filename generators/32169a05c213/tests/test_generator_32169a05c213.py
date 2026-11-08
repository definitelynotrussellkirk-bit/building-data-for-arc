from __future__ import annotations

import copy
import importlib
import random

import pytest


from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash

gen = importlib.import_module("puzzle_generators.per_puzzle.32169a05c213.generator")


def _pair(grid, output=None) -> dict:
    return {"input": copy.deepcopy(grid), "output": copy.deepcopy(output if output is not None else gen.rule_mirror(grid))}


def test_rule_hash_and_all_canonical_pairs_are_exact_and_accepted() -> None:
    assert gen.RULE_HASH == canonical_rule_hash(gen.TASK_ID)
    assert gen.VERSION == "3.0.0"

    for pair in canonical_pairs(gen.TASK_ID):
        before = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before, "rule mirror/self-check mutated canonical input"


def test_exact_axis_boundaries_profiles_and_override_rejections() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for profile_index, profile in enumerate(gen.SCHEDULE_PROFILES):
            for h, w in ((9, 11), (12, 15)):
                grid = gen.generate(
                    10_000 + 100 * band_index + 10 * profile_index + h,
                    profile_index,
                    difficulty=band,
                    grid_h=h,
                    grid_w=w,
                    scene_profile=profile,
                )
                assert gen.self_check(grid) == []
                assert gen.observe_overrides(grid) == {
                    "grid_h": h,
                    "grid_w": w,
                    "scene_profile": profile,
                }

    with pytest.raises(TypeError, match="unknown override axis"):
        gen.generate(1, 0, imaginary_axis=True)
    with pytest.raises(TypeError, match="must be an integer"):
        gen.generate(1, 0, grid_h=True)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(1, 0, grid_h=8)
    with pytest.raises(ValueError, match="outside"):
        gen.generate(1, 0, grid_w=16)
    with pytest.raises(ValueError, match="scene_profile"):
        gen.generate(1, 0, scene_profile="not_a_profile")
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 0, difficulty="expert")


def test_determinism_fresh_returns_and_global_random_state() -> None:
    state_before = random.getstate()
    first = gen.generate(42_424, 7, difficulty="hard")
    state_after = random.getstate()
    assert state_before == state_after

    second = gen.generate(42_424, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert first[0] is not second[0]

    first[0][0] = 9 if first[0][0] != 9 else 8
    third = gen.generate(42_424, 7, difficulty="hard")
    assert third == second


def test_schedule_is_complete_in_every_four_sample_window() -> None:
    expected = set(gen.SCHEDULE_PROFILES)
    for start in range(16):
        got = {
            gen.schedule_profile(seed=12345, sample_index=index, difficulty="hard")
            for index in range(start, start + 4)
        }
        assert got == expected


def test_each_named_rival_has_generated_killing_witnesses() -> None:
    killed = {name: False for name in gen.SEMANTIC_RIVALS}
    branch_seen = {name: False for name in gen.SCHEDULE_PROFILES}

    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(24):
            grid = gen.generate(70_000 + 10_000 * band_index + index, index, difficulty=band)
            facts = gen.semantic_observables(grid)
            branch_seen[facts["scene_profile"]] = True
            expected = gen.rule_mirror(grid)
            for name, rival in gen.SEMANTIC_RIVALS.items():
                if rival(grid) != expected:
                    killed[name] = True

    assert all(branch_seen.values()), branch_seen
    assert all(killed.values()), killed


def test_bbox_area_counterexample_orders_by_occupied_cells() -> None:
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(81_000, 2, difficulty=band, scene_profile="bbox_area_conflict")
        facts = gen.semantic_observables(grid)
        by_authority = [facts["components"][i] for i in facts["authority_order"]]
        assert [c["size"] for c in by_authority] == [3, 5, 6]
        assert sorted(c["bbox_area"] for c in by_authority) != [c["bbox_area"] for c in by_authority]
        assert gen.SEMANTIC_RIVALS["bbox_area_ascending"](grid) != gen.rule_mirror(grid)


def test_targeted_structural_impostors_are_rejected() -> None:
    base = gen.generate(91_000, 0, difficulty="medium", scene_profile="canonical_tie_344")
    facts = gen.semantic_observables(base)

    assert gen.self_check([[0] * 11 for _ in range(9)])

    dropped = copy.deepcopy(base)
    for r, c in facts["components"][0]["cells"]:
        dropped[r][c] = 0
    assert gen.self_check(dropped)

    duplicate_color = copy.deepcopy(base)
    source = facts["components"][0]
    target = facts["components"][1]
    for r, c in target["cells"]:
        duplicate_color[r][c] = source["color"]
    errors = gen.self_check(duplicate_color)
    assert any("pairwise distinct" in error for error in errors), errors

    # Recombine a canonical teaching scene with a 5-cell replacement feature.
    # No remaining scene component has size 5; the Racket/Python rule grammar can
    # still execute it, but the distribution grammar must reject the unsupported
    # (4,4,5) size profile.
    recombined = copy.deepcopy(base)
    source_comp = min(facts["components"], key=lambda c: c["size"])
    for r, c in source_comp["cells"]:
        recombined[r][c] = 0
    r0, c0, _, _ = source_comp["bbox"]
    replacement = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2))
    for dr, dc in replacement:
        recombined[r0 + dr][c0 + dc] = source_comp["color"]
    replacement_facts = gen.semantic_observables(recombined)
    assert 5 not in [c["size"] for c in replacement_facts["components"] if c["color"] != source_comp["color"]]
    errors = gen.self_check(recombined)
    assert any("unsupported component-size profile" in error for error in errors), errors
    assert gen.rule_mirror(recombined), "authority grammar should remain executable"

    four_components = copy.deepcopy(base)
    # Add an isolated singleton in the one unused corner.
    candidates = [(1, 1), (1, len(base[0]) - 2), (len(base) - 2, 1), (len(base) - 2, len(base[0]) - 2)]
    for r, c in candidates:
        if all(four_components[rr][cc] == 0 for rr in range(max(0, r - 1), min(len(base), r + 2)) for cc in range(max(0, c - 1), min(len(base[0]), c + 2))):
            four_components[r][c] = 9
            break
    assert any("exactly three components" in error for error in gen.self_check(four_components))


def test_every_four_demo_window_identifies_the_next_query() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(12):
            lesson_seed = 120_000 + 10_000 * band_index + start
            demos = []
            for index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(lesson_seed, index, difficulty=band)
                demos.append(_pair(grid))
            query_index = start + gen.EXAMPLES_NEEDED
            query_grid = gen.generate(lesson_seed, query_index, difficulty=band)
            assert gen.lesson_identifiable(demos, _pair(query_grid)) == []


def test_three_demos_are_minimal_for_schedule_level_identifiability() -> None:
    # Three consecutive profiles are enough to kill all query-changing named
    # competitors for this curriculum; two are not universally sufficient.
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(8):
            lesson_seed = 150_000 + 10_000 * band_index + start
            demos = [
                _pair(gen.generate(lesson_seed, i, difficulty=band))
                for i in range(start, start + 3)
            ]
            query = _pair(gen.generate(lesson_seed, start + 3, difficulty=band))
            assert gen.lesson_identifiable(demos, query) == []

    found_two_demo_failure = False
    for start in range(8):
        lesson_seed = 170_000 + start
        demos = [_pair(gen.generate(lesson_seed, i, difficulty="hard")) for i in range(start, start + 2)]
        query = _pair(gen.generate(lesson_seed, start + 2, difficulty="hard"))
        if gen.lesson_identifiable(demos, query):
            found_two_demo_failure = True
            break
    assert found_two_demo_failure
