"""Focused regressions for generator 10599ac9904a."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from puzzle_generators.base import set_ctx_observer
from scripts.canonical_profile_gate import canonical_pairs


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "10599ac9904a"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.10599ac9904a.generator"
)
BANDS = ("easy", "medium", "hard")
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/64addfdad75c/M151__10599ac9904a.json"
)


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN._python_apply(grid)}


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_rule_hash_and_selected_authority_are_synchronized():
    base = json.loads(BASE_PATH.read_text())
    racket = base["racket_target"]
    assert racket["target_code"] == racket["raw_code"]
    assert _normalized_hash(racket["target_code"]) == GEN.RULE_HASH == "6bbf0525c028"


def test_all_canonical_inputs_are_accepted_and_python_mirror_is_exact_and_pure():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN._python_apply(grid) == pair["output"]
        assert grid == snapshot


def test_five_demo_sliding_windows_identify_every_named_rival():
    assert GEN.EXAMPLES_NEEDED == 5
    assert len(GEN.SCENE_PROFILES) == 5
    for band in BANDS:
        for start in range(40):
            pairs = [
                _pair(GEN.generate(410_000 + start, start + offset, difficulty=band))
                for offset in range(6)
            ]
            demos, query = pairs[:5], pairs[5]
            assert {GEN._scene_profile(pair["input"]) for pair in demos} == set(
                GEN.SCENE_PROFILES
            )
            assert GEN.lesson_identifiable(demos, query) == []


def test_repeated_multi_payload_profile_kills_three_shortcuts_at_once():
    grid = GEN.generate(
        777,
        2,
        difficulty="hard",
        scene_profile="repeated_multi_payload",
        vector="up_left_3_4",
    )
    info, errors = GEN._analyse(grid)
    assert errors == []
    assert len(info["twos"]) > 1 or len(info["threes"]) > 1
    assert len(info["payload_colors"]) == 2
    assert len(GEN._payload_components(grid)) >= 2
    official = GEN._python_apply(grid)
    assert official != GEN._rival_first_markers(grid)
    assert official != GEN._rival_largest_component_only(grid)
    assert official != GEN._rival_one_payload_color_only(grid)


def test_linked_semantic_and_disjoint_stability_censuses_200_per_band():
    expected_profile_count = {name: 40 for name in GEN.SCENE_PROFILES}
    for cohort in range(2):
        for band_index, band in enumerate(BANDS):
            profile_counts = Counter()
            witness_counts = Counter()
            unique = set()
            for index in range(200):
                seed = 1_000_000 * (cohort + 1) + 10_000 * band_index + index
                sample_index = 50_000 * cohort + index
                grid = GEN.generate(seed, sample_index, difficulty=band)
                assert GEN.self_check(grid) == []
                assert GEN.strict_canonical_like(grid) == []
                profile_counts[GEN._scene_profile(grid)] += 1
                unique.add(_frozen(grid))
                for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                    witness_counts[name] += bool(predicate(grid))
            assert dict(profile_counts) == expected_profile_count
            assert len(unique) >= 195
            assert all(witness_counts[name] > 0 for name in GEN.SEMANTIC_WITNESSES)


def test_override_provenance_unknown_keys_and_fresh_returns():
    captured = []
    set_ctx_observer(captured.append)
    try:
        grid = GEN.generate(
            808,
            19,
            difficulty="medium",
            grid_h=12,
            grid_w=10,
            scene_profile="partial_clip",
            vector="down_left_4_2",
        )
    finally:
        set_ctx_observer(None)
    assert len(captured) == 1
    observed = GEN.observe_overrides(grid)
    assert observed == {
        "grid_h": 12,
        "grid_w": 10,
        "scene_profile": "partial_clip",
        "vector": "down_left_4_2",
    }
    assert all(captured[0].axis_value(axis) == value for axis, value in observed.items())
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 1, made_up_axis="nope")

    random.seed(9173)
    state = random.getstate()
    first = GEN.generate(808, 19, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(808, 19, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(808, 19, difficulty="medium") == second


def test_negative_recombination_rejected_and_oracle_precondition_is_explicit():
    grid = GEN.generate(909, 7, difficulty="hard")
    recombined = copy.deepcopy(grid)
    replacement = next(
        color
        for color in range(1, 10)
        if color not in {value for row in recombined for value in row}
    )
    for row in recombined:
        for column, value in enumerate(row):
            if value == 2:
                row[column] = replacement
    assert not any(value == 2 for row in recombined for value in row)
    assert GEN.self_check(recombined)
    with pytest.raises(ValueError, match="color-2"):
        GEN._python_apply(recombined)


def test_mutation_fixtures_are_rejected_without_mutation():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == snapshot
