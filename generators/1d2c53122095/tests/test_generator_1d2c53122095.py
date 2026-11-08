from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root

GEN = importlib.import_module("puzzle_generators.per_puzzle.1d2c53122095.generator")
TASK_ID = "1d2c53122095"


def _demo(seed: int, sample_index: int, band: str):
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_inputs_are_accepted():
    assert GEN.RULE_HASH == "4e070bae635e"
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 5
    assert all(GEN.self_check(pair["input"]) == [] for pair in pairs)
    assert all(GEN.rule_mirror(pair["input"]) == pair["output"] for pair in pairs)


def test_every_declared_profile_override_is_exactly_observable():
    for profile in GEN.SCENE_PROFILES:
        grid = GEN.generate(1234, 17, difficulty="easy", scene_profile=profile)
        assert GEN.observe_overrides(grid) == {"scene_profile": profile}
        assert GEN.self_check(grid, meta={"overrides": {"scene_profile": profile}}) == []
        assert GEN.teaching_check(grid) == []

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_profile="easy_outer_13_nf2")
    with pytest.raises(ValueError, match="unknown scene_profile"):
        GEN.generate(1, 0, scene_profile="not_a_profile")


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(8675309)
    before = random.getstate()
    first = GEN.generate(77, 3, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(77, 3, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    assert before == after


def test_outer_intermediate_and_innermost_branches_fire_in_every_band():
    for band in ("easy", "medium", "hard"):
        analyses = [GEN._analysis(GEN.generate(91, index, difficulty=band)) for index in range(4)]
        depths = [analysis["k"] for analysis in analyses]
        counts = [len(analysis["frames"]) for analysis in analyses]
        assert any(depth == 1 for depth in depths)
        assert any(1 < depth < count for depth, count in zip(depths, counts))
        assert any(depth == count for depth, count in zip(depths, counts))

        for index in range(4):
            grid = GEN.generate(91, index, difficulty=band)
            output = GEN.rule_mirror(grid)
            assert output != grid


def test_self_check_rejects_structural_impostors():
    source = GEN.generate(2026, 1, difficulty="medium")
    analysis = GEN._analysis(source)

    no_marker = copy.deepcopy(source)
    for col, value in enumerate(no_marker[0]):
        if value == 2:
            no_marker[0][col] = 0
    assert any("marker" in reason for reason in GEN.self_check(no_marker))

    broken_frame = copy.deepcopy(source)
    row, col = next(iter(GEN._outline_cells(analysis["frames"][0])))
    broken_frame[row][col] = 0
    assert GEN.self_check(broken_frame)

    red_inside = copy.deepcopy(source)
    red_inside[1][0] = 2
    assert any("row 0" in reason for reason in GEN.self_check(red_inside))

    foreign_color = copy.deepcopy(source)
    foreign_color[1][0] = 7
    assert any("palette" in reason for reason in GEN.self_check(foreign_color))

    too_many_markers = copy.deepcopy(source)
    needed = len(analysis["frames"]) + 1
    too_many_markers[0] = [0] * len(too_many_markers[0])
    for col in range(needed):
        too_many_markers[0][col] = 2
    assert any("must be in" in reason for reason in GEN.self_check(too_many_markers))


def test_every_sliding_curriculum_window_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(len(GEN._PROFILES_BY_BAND[band])):
            demos = [_demo(404, start + offset, band) for offset in range(GEN.EXAMPLES_NEEDED)]
            query = {"input": GEN.generate(404, start + GEN.EXAMPLES_NEEDED, difficulty=band)}
            assert GEN.lesson_identifiable(demos, query) == []


def test_production_query_profile_is_new_in_every_cyclic_lesson_window():
    """The query must require cue transfer, not exact-profile lookup from a demo."""
    for band in ("easy", "medium", "hard"):
        period = len(GEN._PROFILES_BY_BAND[band])
        assert period > GEN.EXAMPLES_NEEDED
        for start in range(period):
            profiles = [
                GEN.observe_overrides(
                    GEN.generate(505, start + offset, difficulty=band)
                )["scene_profile"]
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            assert profiles[-1] not in profiles[:-1], (band, start, profiles)


def test_lesson_contract_rejects_profile_copy_shortcut():
    """A repeated linked profile leaks its fixed depth even with a fresh layout."""
    for band in ("easy", "medium", "hard"):
        demos = [_demo(606, offset, band) for offset in range(GEN.EXAMPLES_NEEDED)]
        repeated_profile_query = {
            "input": GEN.generate(607, 0, difficulty=band),
        }
        reasons = GEN.lesson_identifiable(demos, repeated_profile_query)
        assert any("profile-copy" in reason for reason in reasons), reasons


def test_named_rivals_are_killed_by_their_claimed_witnesses():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(808, index, difficulty=band) for index in range(4)]
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            firing = [grid for grid in grids if witness(grid)]
            assert firing, (band, witness_name)
            for grid in firing:
                truth = GEN.rule_mirror(grid)
                assert any(
                    GEN.SEMANTIC_RIVALS[rival_name](grid) != truth
                    for rival_name in GEN.WITNESS_RIVALS[witness_name]
                )
