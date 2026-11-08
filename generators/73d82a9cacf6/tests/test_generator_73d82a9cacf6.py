from __future__ import annotations

import copy
import importlib
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "73d82a9cacf6"
ROOT = find_root(__file__)
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _blank(height: int = 10, width: int = 16):
    return [[0 for _ in range(width)] for _ in range(height)]


def test_canonical_pairs_are_owned_and_solved_by_mirror():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(copy.deepcopy(pair["input"])) == []
        assert GEN.strict_canonical_like(copy.deepcopy(pair["input"])) == []
        assert GEN.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_canonical_shortcut_declaration_matches_named_competitor_census():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    candidates = dict(GEN.LESSON_COMPETITORS)
    candidates.update(GEN.CANONICAL_SHORTCUTS)
    fit = {
        name: [shortcut(copy.deepcopy(pair["input"])) == pair["output"] for pair in pairs]
        for name, shortcut in candidates.items()
    }
    expected = {name for name, matches in fit.items() if all(matches)}
    assert set(GEN.CANONICAL_SHORTCUTS) == expected, fit


def test_noncanonical_shortcuts_remain_available_as_lesson_rivals():
    expected = {"hole_count_only", "reading_order"}
    assert expected <= set(GEN.SEMANTIC_RIVALS)
    assert expected <= set(GEN.LESSON_COMPETITORS)


def test_every_two_example_window_contains_both_semantic_profiles():
    for start in range(20):
        profiles = {
            GEN.schedule_profile(123, start + offset, difficulty="hard")
            for offset in range(GEN.EXAMPLES_NEEDED)
        }
        assert profiles == set(GEN.SCENE_PROFILES)


def test_area_tie_profile_kills_hole_only_and_area_ascending_rivals():
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            grid = GEN.generate(
                seed,
                1,
                difficulty=band,
                scene_profile="area_tie",
            )
            assert GEN.observe_overrides(grid)["scene_profile"] == "area_tie"
            expected = GEN.rule_mirror(grid)
            assert GEN._rival_hole_only(grid) != expected
            assert GEN._rival_area_ascending(grid) != expected


def test_exact_overrides_are_observable_and_unknown_keys_reject():
    for band in ("easy", "medium", "hard"):
        for scene_profile in GEN.SCENE_PROFILES:
            for canvas_profile in GEN.CANVAS_PROFILES:
                grid = GEN.generate(
                    91,
                    7,
                    difficulty=band,
                    scene_profile=scene_profile,
                    canvas_profile=canvas_profile,
                )
                assert GEN.observe_overrides(grid) == {
                    "scene_profile": scene_profile,
                    "canvas_profile": canvas_profile,
                }
                assert GEN.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, nonsense_axis="typo")


def test_self_check_rejects_targeted_structural_impostors():
    no_components = _blank()

    single_component = _blank()
    for row in range(2):
        for col in range(2):
            single_component[row][col] = 4

    all_same_holes = _blank()
    for left, color in ((0, 2), (6, 4), (12, 7)):
        for row in range(2):
            for col in range(2):
                all_same_holes[row][left + col] = color

    broken_ring = GEN.generate(
        8, 0, scene_profile="distinct_holes", canvas_profile="10x16"
    )
    ring = next(
        obj for obj in GEN._analyze(broken_ring)["facts"]["objects"]
        if obj["holes"] == 1
    )
    row, col = ring["cells"][0]
    broken_ring[row][col] = 0

    touching = GEN.generate(
        11, 0, scene_profile="distinct_holes", canvas_profile="10x16"
    )
    facts = GEN._analyze(touching)["facts"]
    first = facts["objects"][0]
    second_color = facts["objects"][1]["color"]
    neighbor = next(
        (row + dr, col + dc)
        for row, col in first["cells"]
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        if 0 <= row + dr < len(touching)
        and 0 <= col + dc < len(touching[0])
        and touching[row + dr][col + dc] == 0
    )
    touching[neighbor[0]][neighbor[1]] = second_color

    for impostor in (
        no_components,
        single_component,
        all_same_holes,
        broken_ring,
        touching,
    ):
        assert GEN.self_check(impostor), impostor


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(20260728)
    state = random.getstate()
    first = GEN.generate(314159, 9, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(314159, 9, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
