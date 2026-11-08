"""Focused authority, override, distribution, and lesson regressions for b19deac47327."""
from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "b19deac47327"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _pair(seed: int, sample_index: int, difficulty: str):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_pin_mirror_and_canonical_acceptance() -> None:
    assert GEN.VERSION == "2.1.0"
    assert GEN.RULE_HASH == "2b2e46dd36cc"
    assert "border" in GEN.SUMMARY.lower() and "marker" in GEN.SUMMARY.lower()

    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_every_four_episode_window_is_rotation_identifiable() -> None:
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "cross_horizontal",
        "tie_vertical",
        "cross_vertical",
        "tie_horizontal",
    )

    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            episodes = [
                _pair(7100 + start, sample_index, difficulty)
                for sample_index in range(start, start + 4)
            ]
            for query_index, query in enumerate(episodes):
                demos = [pair for index, pair in enumerate(episodes) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                observed = [GEN.observe_overrides(pair["input"]) for pair in demos]
                assert {item["orientation"] for item in observed} == {
                    "horizontal",
                    "vertical",
                }
                assert any(item["midline_marker"] for item in observed)
                assert any(item["edge_marker_mode"] == "unseen" for item in observed)


def test_exact_override_boundaries_are_observable_in_every_band() -> None:
    cases = (
        {
            "grid_h": 9,
            "grid_w": 9,
            "orientation": "horizontal",
            "marker_count": 4,
            "edge_pair": "2_4",
            "side_balance": "first_heavy",
            "edge_marker_mode": "none",
            "midline_marker": False,
        },
        {
            "grid_h": 18,
            "grid_w": 18,
            "orientation": "vertical",
            "marker_count": 12,
            "edge_pair": "8_3",
            "side_balance": "second_heavy",
            "edge_marker_mode": "unseen",
            "midline_marker": True,
        },
        {
            "grid_h": 13,
            "grid_w": 10,
            "orientation": "horizontal",
            "marker_count": 7,
            "edge_pair": "5_9",
            "side_balance": "balanced",
            "edge_marker_mode": "seen",
            "midline_marker": True,
        },
    )
    for difficulty in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = GEN.generate(8000 + index, 20 + index, difficulty=difficulty, **requested)
            assert GEN.observe_overrides(grid) == requested
            assert GEN.self_check(
                grid,
                difficulty=difficulty,
                meta={"overrides": requested},
            ) == []

    with pytest.raises(TypeError, match="unknown override"):
        GEN.generate(0, 0, misspelled_axis=1)
    with pytest.raises(TypeError, match="grid_h"):
        GEN.generate(0, 0, grid_h=True)
    with pytest.raises(ValueError, match="grid_h"):
        GEN.generate(0, 0, grid_h=8)
    with pytest.raises(ValueError, match="orientation"):
        GEN.generate(0, 0, orientation="diagonal")
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")


def test_default_distribution_has_canonical_support_and_all_witnesses() -> None:
    canonical_profiles = {(14, 10, 4), (12, 13, 4), (12, 10, 4), (16, 18, 4)}
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(9001, index, difficulty=difficulty) for index in range(20)]
        profiles = [
            (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            for grid in grids
        ]
        assert sum(profile in canonical_profiles for profile in profiles) >= 8
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)
        assert {GEN.observe_overrides(grid)["orientation"] for grid in grids} == {
            "horizontal",
            "vertical",
        }
        assert {GEN.observe_overrides(grid)["edge_marker_mode"] for grid in grids} >= {
            "none",
            "seen",
            "unseen",
        }
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            assert any(witness(grid) for grid in grids), name


def test_canonical_shortcuts_need_generated_counterexamples() -> None:
    pairs = canonical_pairs(TASK_ID, root=find_root(__file__))
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name

    generated = [GEN.generate(10001, index, difficulty="medium") for index in range(4)]
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert any(shortcut(grid) != GEN.rule_mirror(grid) for grid in generated), name


def test_self_check_rejects_targeted_impostors() -> None:
    valid = GEN.generate(11001, 1, difficulty="medium")
    assert GEN.self_check(valid) == []
    facts = GEN._facts_or_raise(valid)

    broken_border = copy.deepcopy(valid)
    if facts["orientation"] == "horizontal":
        broken_border[0][0] = 0
    else:
        broken_border[0][0] = 0

    one_sided = copy.deepcopy(valid)
    for marker_row, marker_col in facts["markers"]:
        oriented = marker_row if facts["orientation"] == "horizontal" else marker_col
        extent = len(valid) if facts["orientation"] == "horizontal" else len(valid[0])
        if 2 * oriented >= extent:
            one_sided[marker_row][marker_col] = 0

    blocked_projection = copy.deepcopy(valid)
    destination_row, destination_col = facts["destinations"][0]
    blocked_projection[destination_row][destination_col] = 1

    illegal_palette = copy.deepcopy(valid)
    illegal_palette[len(valid) // 2][len(valid[0]) // 2] = 6

    for name, grid in {
        "broken border": broken_border,
        "one-sided markers": one_sided,
        "blocked projection": blocked_projection,
        "illegal palette": illegal_palette,
    }.items():
        assert GEN.self_check(grid), name


def test_difficulty_keys_layout_without_changing_declared_axes() -> None:
    for sample_index in range(GEN.LESSON_SCHEDULE_PERIOD):
        grids = {
            difficulty: GEN.generate(12500, sample_index, difficulty=difficulty)
            for difficulty in ("easy", "medium", "hard")
        }
        assert len({
            tuple(tuple(row) for row in grid)
            for grid in grids.values()
        }) == 3
        assert len({
            tuple(sorted(GEN.observe_overrides(grid).items()))
            for grid in grids.values()
        }) == 1



def test_determinism_fresh_returns_diversity_and_global_rng_purity() -> None:
    random.seed(20261007)
    before = random.getstate()
    first = GEN.generate(123456, 17, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(123456, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(123456, 17, difficulty="hard") == second

    unique = {
        tuple(tuple(row) for row in GEN.generate(12000 + index, index, difficulty="hard"))
        for index in range(120)
    }
    assert len(unique) >= 110


def test_retained_counterexamples_cover_declared_canonical_shortcuts() -> None:
    path = find_root(__file__) / "generators" / TASK_ID / "counterexamples" / "canonical_shortcuts.json"
    payload = json.loads(path.read_text())
    assert payload["task_id"] == TASK_ID
    assert payload["generator_version"] == GEN.VERSION
    assert payload["rule_hash"] == GEN.RULE_HASH
    cases = {case["rival"]: case for case in payload["cases"]}
    assert set(cases) == set(GEN.CANONICAL_SHORTCUTS)
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        case = cases[name]
        grid = case["input"]
        assert GEN.self_check(grid) == []
        assert GEN.rule_mirror(grid) == case["canonical_output"]
        assert rival(grid) == case["rival_output"]
        assert case["canonical_output"] != case["rival_output"]


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1"])
def test_public_call_rejects_nonliteral_seed_scalars(bad_seed) -> None:
    with pytest.raises(TypeError, match="seed must be an integer"):
        GEN.generate(bad_seed, 0, difficulty="easy")
    with pytest.raises(TypeError, match="seed must be an integer"):
        GEN.schedule_profile(bad_seed, 0, "easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1"])
def test_public_call_rejects_nonliteral_sample_indices(bad_index) -> None:
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        GEN.generate(991, bad_index, difficulty="easy")
    with pytest.raises(TypeError, match="sample_index must be an integer"):
        GEN.schedule_profile(991, bad_index, "easy")


def test_public_call_rejects_negative_sample_index() -> None:
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        GEN.generate(991, -1, difficulty="easy")
    with pytest.raises(ValueError, match="sample_index must be nonnegative"):
        GEN.schedule_profile(991, -1, "easy")


def test_default_height_distribution_exercises_full_strict_envelope() -> None:
    heights = {
        len(GEN.generate(13000 + seed, sample_index, difficulty=difficulty))
        for difficulty in ("easy", "medium", "hard")
        for seed in range(32)
        for sample_index in range(GEN.LESSON_SCHEDULE_PERIOD)
    }
    assert heights == {12, 13, 14, 15, 16}
