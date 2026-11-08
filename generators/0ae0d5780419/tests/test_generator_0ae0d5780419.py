from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "0ae0d5780419"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _episode(seed: int, start: int, band: str):
    pairs = []
    for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(seed, sample_index, difficulty=band)
        pairs.append({"input": grid, "output": GEN._mirror(grid)})
    return pairs[:-1], pairs[-1]


def test_canonical_rule_uses_first_match_priority_and_is_exact():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    priority_cases = 0
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        analysis = GEN._analyse(pair["input"])
        assert not analysis["errors"]
        facts = analysis["facts"]
        if facts["priority_ambiguous"]:
            priority_cases += 1
        assert GEN._mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before
    assert priority_cases == 4


def test_every_sliding_four_demo_window_covers_all_profiles_and_identifies_query():
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            profiles = {
                GEN.schedule_profile(23, sample_index, band)
                for sample_index in range(start, start + GEN.EXAMPLES_NEEDED)
            }
            assert profiles == set(GEN.SCHEDULE_PROFILES)
            demos, query = _episode(23, start, band)
            assert GEN.lesson_identifiable(demos, query) == []


def test_priority_color_and_fallback_witnesses_kill_named_rivals():
    for band in ("easy", "medium", "hard"):
        priority = GEN.generate(0, 0, difficulty=band)
        color = GEN.generate(0, 1, difficulty=band)
        fallback = GEN.generate(0, 2, difficulty=band)
        assert GEN.SEMANTIC_WITNESSES["priority_first_match"](priority)
        assert GEN._rival_last_match(priority) != GEN._mirror(priority)
        assert GEN.SEMANTIC_WITNESSES["color_sensitive_match"](color)
        assert GEN._rival_colorblind(color) != GEN._mirror(color)
        assert GEN.SEMANTIC_WITNESSES["no_match_identity_fallback"](fallback)
        assert GEN._rival_rotate_on_no_match(fallback) != GEN._mirror(fallback)


def test_exact_override_boundaries_are_observed_in_every_band():
    for band in ("easy", "medium", "hard"):
        grid = GEN.generate(
            91,
            7,
            difficulty=band,
            panel_h=3,
            panel_n=8,
            transform=6,
            texture="plain",
        )
        assert GEN.observe_overrides(grid) == {
            "panel_h": 3,
            "panel_n": 8,
            "transform": 6,
            "texture": "plain",
        }
        assert GEN.self_check(
            grid,
            difficulty=band,
            meta={
                "overrides": {
                    "panel_h": 3,
                    "panel_n": 8,
                    "transform": 6,
                    "texture": "plain",
                }
            },
        ) == []

    multicolor_identity = GEN.generate(
        92, 4, difficulty="easy", transform=1, texture="multicolor"
    )
    observed = GEN.observe_overrides(multicolor_identity)
    assert observed["transform"] == 1
    assert observed["texture"] == "multicolor"

    with pytest.raises(ValueError, match="incompatible"):
        GEN.generate(1, 1, difficulty="easy", texture="no_match", transform=2)
    with pytest.raises(ValueError, match="unsupported override"):
        GEN.generate(1, 1, difficulty="easy", misspelled_axis=3)


def test_self_check_rejects_targeted_structural_impostors():
    grid = GEN.generate(5, 3, difficulty="medium")
    assert GEN.self_check(grid) == []
    panel_n = GEN.observe_overrides(grid)["panel_n"]
    second_divider = 2 * panel_n + 1

    missing_divider = copy.deepcopy(grid)
    missing_divider[0][panel_n] = 0
    assert GEN.self_check(missing_divider)

    extra_divider = copy.deepcopy(grid)
    for row in extra_divider:
        row[0] = 5
    assert GEN.self_check(extra_divider)

    empty_c = copy.deepcopy(grid)
    for row in empty_c:
        for col in range(second_divider + 1, len(row)):
            row[col] = 0
    assert any("panel C is empty" in message for message in GEN.self_check(empty_c))

    reserved_color_inside_panel = copy.deepcopy(grid)
    reserved_color_inside_panel[0][1] = 5
    assert GEN.self_check(reserved_color_inside_panel)

    ragged = copy.deepcopy(grid)
    ragged[-1].pop()
    assert GEN.self_check(ragged)


def test_replay_freshness_and_process_global_rng_purity():
    random.seed(20260727)
    state = random.getstate()
    first = GEN.generate(777, 12, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(777, 12, difficulty="hard")
    assert first == second
    assert first is not second
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == GEN.generate(777, 12, difficulty="hard")
