from __future__ import annotations

import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "52b9b0e6b46a"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def test_canonical_pairs_are_accepted_and_python_audit_mirror_matches():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_every_four_slot_window_separates_independent_controls():
    for start in range(48):
        observations = [
            GEN.observe_overrides(GEN.generate(9000 + start, start + offset, difficulty="medium"))
            for offset in range(5)
        ]
        demos, query = observations[:4], observations[4]
        assert {item["corner_code"] for item in demos} == {0, 1, 2, 3}
        assert {item["rank"] for item in demos} == {1, 2, 3}
        assert {item["frame_side"] for item in demos} == {"left", "right"}
        assert {item["decoy_mode"] for item in demos} == {"none", "orange_object"}
        assert query["corner_code"] == demos[0]["corner_code"]
        assert query["rank"] != demos[0]["rank"]
        assert query["frame_side"] != demos[0]["frame_side"]
        assert query["decoy_mode"] != demos[0]["decoy_mode"]


def test_exact_override_boundaries_are_observable_in_every_band():
    cases = (
        {
            "grid_h": 11,
            "grid_w": 14,
            "frame_h": 5,
            "frame_w": 5,
            "corner_code": 0,
            "rank": 1,
            "frame_side": "left",
            "decoy_mode": "none",
        },
        {
            "grid_h": 16,
            "grid_w": 19,
            "frame_h": 7,
            "frame_w": 8,
            "corner_code": 3,
            "rank": 3,
            "frame_side": "right",
            "decoy_mode": "orange_object",
        },
    )
    for band in ("easy", "medium", "hard"):
        for index, expected in enumerate(cases):
            grid = GEN.generate(1300 + index, index, difficulty=band, **expected)
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            assert {key: observed[key] for key in expected} == expected


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, difficulty="medium", typo_axis=3)


def test_mutation_fixtures_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_deterministic_fresh_and_process_rng_pure():
    state = random.getstate()
    first = GEN.generate(777, 9, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(777, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == GEN.generate(777, 9, difficulty="hard")


def test_declared_schedule_profiles_are_complete_and_unique():
    assert len(GEN.SCHEDULE_PROFILES) == 24
    assert len(set(GEN.SCHEDULE_PROFILES)) == 24
    assert {
        GEN.schedule_profile(0, index, difficulty="medium") for index in range(24)
    } == set(GEN.SCHEDULE_PROFILES)


def test_ordinary_keyed_axes_survive_layout_and_are_observable():
    from puzzle_generators import base

    for band_i, band in enumerate(("easy", "medium", "hard")):
        for j in range(12):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(12000 + band_i * 100 + j, 700 + j * 5, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            keyed = {axis: captured[0].axis_value(axis) for axis in GEN.AXES}
            assert GEN.observe_overrides(grid) == keyed


def test_absent_color_recombination_is_rejected_by_teaching_grammar():
    grid = GEN.generate(950000, 66, difficulty="medium")
    facts = GEN._analyze(grid)
    used = {value for row in grid for value in row}
    fresh = next(color for color in range(1, 7) if color not in used)
    changed = [row[:] for row in grid]
    r, c = facts["candidates"][-1]["cells"][0]
    changed[r][c] = fresh
    assert fresh not in used
    errors = GEN.self_check(changed)
    assert errors
    assert any("areas must be distinct" in error or "bounding box" in error for error in errors)
