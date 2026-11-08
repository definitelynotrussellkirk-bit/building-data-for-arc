from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from reviewer_support import canonical_path, canonical_pairs, find_root, load_selected_generator

TASK_ID = "0f5fbe0de38e"
ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator(TASK_ID, root=ROOT)


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _canonical_row() -> dict:
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical task row missing")


def test_metadata_and_rule_hash_are_pinned_to_authority():
    row = _canonical_row()
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "4.0.0"
    assert GEN.RULE_HASH == _normalized_hash(row["program_solution"])

    base_name = "base/solutions/training/6aa20dc0__0f5fbe0de38e.json"
    base_path = ROOT / "shared/data" / base_name
    if not base_path.is_file():
        base_path = ROOT / "data" / base_name
    base = json.loads(base_path.read_text())
    assert GEN.RULE_HASH == _normalized_hash(base["racket_target"]["target_code"])
    assert base["racket_target"]["target_code"] == row["program_solution"]


def test_every_canonical_input_is_accepted_and_profiled():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 4
    profiles = set()
    lessons = set()
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        observed = GEN.observe_overrides(source)
        profiles.add(observed["template_profile"])
        lessons.add(observed["lesson_profile"])
    assert profiles == set(GEN.TEMPLATE_PROFILE_NAMES)
    assert lessons == {
        "scaled3_single",
        "mixed_1_2",
        "unit_double",
        "mixed_1_2_3",
    }


def test_six_step_schedule_covers_required_semantic_branches_in_every_band():
    expected_lessons = list(GEN.LESSON_PROFILE_NAMES)
    for band_index, band in enumerate(("easy", "medium", "hard")):
        observed = [
            GEN.observe_overrides(
                GEN.generate(10_000 + band_index * 100 + i, i, difficulty=band)
            )
            for i in range(6)
        ]
        assert [row["lesson_profile"] for row in observed] == expected_lessons
        assert {row["orientation_profile"] for row in observed} == {
            "same",
            "opposite",
            "mixed",
        }
        assert {scale for row in observed for scale in GEN.LESSON_SCALES[row["lesson_profile"]]} == {1, 2, 3}


def test_exact_boundary_overrides_are_observable():
    cases = (
        {
            "grid_h": 19,
            "grid_w": 22,
            "bg_color": 0,
            "fill_color": 9,
            "marker_a_color": 1,
            "marker_b_color": 8,
            "template_profile": "ring6_anti",
            "lesson_profile": "mixed_1_2_3",
            "orientation_profile": "mixed",
        },
        {
            "grid_h": 22,
            "grid_w": 19,
            "bg_color": 9,
            "fill_color": 0,
            "marker_a_color": 8,
            "marker_b_color": 1,
            "template_profile": "cross4_anti",
            "lesson_profile": "scaled3_single",
            "orientation_profile": "opposite",
        },
    )
    for index, overrides in enumerate(cases):
        grid = GEN.generate(20_000 + index, 70 + index, difficulty="easy", **overrides)
        assert GEN.observe_overrides(grid) == overrides
        assert GEN.self_check(grid) == []

    # A mixed orientation is itself a valid exact axis.  When no lesson is
    # forced, generation must select a compatible multi-pair lesson rather
    # than silently ignore or reject the override.
    mixed = GEN.generate(21_000, 0, difficulty="medium", orientation_profile="mixed")
    mixed_obs = GEN.observe_overrides(mixed)
    assert mixed_obs["orientation_profile"] == "mixed"
    assert len(GEN.LESSON_SCALES[mixed_obs["lesson_profile"]]) >= 2

    with pytest.raises(ValueError, match="incompatible"):
        GEN.generate(
            21_001,
            0,
            lesson_profile="unit_single",
            orientation_profile="mixed",
        )


def test_deterministic_fresh_and_global_rng_clean():
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(30_000, 5, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(30_000, 5, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_four_targeted_impostors_are_rejected():
    for texture in GEN.DEGENERATE_TEXTURES:
        grid = GEN.generate(40_000, 3, texture=texture)
        errors = GEN.self_check(grid)
        assert errors, texture


def test_racket_oracle_matches_canonical_and_generated_inputs_without_mutation():
    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == pair["output"]
            assert source == before

        grids = [
            GEN.generate(50_000 + i, i, difficulty=band)
            for band in ("easy", "medium", "hard")
            for i in range(6)
        ]
        for grid in grids:
            before = copy.deepcopy(grid)
            assert _apply_rule(bridge, fn_name, grid) == GEN._predict(grid, "canonical")
            assert grid == before

        a, b = grids[0], grids[-1]
        out_a1 = _apply_rule(bridge, fn_name, a)
        _apply_rule(bridge, fn_name, b)
        out_a2 = _apply_rule(bridge, fn_name, a)
        assert out_a1 == out_a2
    finally:
        bridge.shutdown()
