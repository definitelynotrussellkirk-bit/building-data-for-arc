"""Regression tests for the repaired Deepest Seeded Frame generator."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import importlib.util
from itertools import combinations
import os
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "6c40e60caa4a"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(
        f"reviewed_generator_{TASK_ID}", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
TRAIN = [pair for pair in PAIRS if pair["split"] == "train"]
TEST = [pair for pair in PAIRS if pair["split"] == "test"]


def _lesson(seed: int, start: int, *, band: str = "medium"):
    pairs = []
    for offset in range(gen.EXAMPLES_NEEDED + 1):
        grid = gen.generate(seed, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": gen.expected_output(grid)})
    return pairs


def _materialized_lesson(seed: int, start: int, *, band: str = "medium"):
    """Mirror runner.run_one's pair-level duplicate suppression."""
    pairs = []
    accepted_indices = []
    seen = set()
    sample_index = start
    needed = gen.EXAMPLES_NEEDED + 1
    while len(pairs) < needed and sample_index < start + needed * 5:
        grid = gen.generate(seed, sample_index, difficulty=band)
        pair = {"input": grid, "output": gen.expected_output(grid)}
        blob = json.dumps(
            [pair["input"], pair["output"]],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(blob.encode()).hexdigest()[:12]
        if digest not in seen:
            seen.add(digest)
            pairs.append(pair)
            accepted_indices.append(sample_index)
        sample_index += 1
    assert len(pairs) == needed
    return pairs, accepted_indices


def test_rule_hash_and_version_pin_the_repair():
    assert gen.RULE_HASH == "e82c2d54609b"
    assert gen.VERSION == "2.0.0"


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_accepted_and_solved_exactly(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.expected_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("scene_kind", ["single", "nested", "mixed"])
def test_exact_overrides_are_honored_and_observable(band, scene_kind):
    grid = gen.generate(
        913,
        37,
        difficulty=band,
        grid_h=15,
        grid_w=14,
        scene_kind=scene_kind,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": 15,
        "grid_w": 14,
        "scene_kind": scene_kind,
    }


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("grid_h", 10),
        ("grid_h", 16),
        ("grid_w", 10),
        ("grid_w", 16),
        ("scene_kind", "other"),
        ("grid_h", True),
        ("grid_w", 11.0),
        ("scene_kind", 1),
        ("typo", 1),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = gen.generate(12345, 67, difficulty="hard")
    assert random.getstate() == state
    untouched = deepcopy(first)
    first[0][0] = 9
    second = gen.generate(12345, 67, difficulty="hard")
    assert random.getstate() == state
    assert second == untouched
    assert second is not first
    assert all(a is not b for a, b in zip(second, first))


def test_difficulty_bands_change_layout_without_changing_the_rule_profile():
    grids = [
        gen.generate(24680, 8, difficulty=band)
        for band in ("easy", "medium", "hard")
    ]
    assert len({repr(grid) for grid in grids}) == 3
    observations = [gen.observe_overrides(grid) for grid in grids]
    assert observations[0] == observations[1] == observations[2]


def test_schedule_keeps_two_mixed_witnesses_after_any_two_rejections():
    needed = gen.EXAMPLES_NEEDED + 1
    for start in range(gen.LESSON_SCHEDULE_PERIOD):
        raw = [
            gen.schedule_profile(0, start + offset, "medium")
            for offset in range(needed + 2)
        ]
        for rejected in combinations(range(len(raw)), 2):
            accepted = [
                profile
                for index, profile in enumerate(raw)
                if index not in rejected
            ][:needed]
            assert len(accepted) == needed
            assert accepted.count("mixed") >= 2


def test_default_schedule_hits_the_three_canonical_profiles():
    observed = []
    for index in range(4):
        grid = gen.generate(71, index, difficulty="medium")
        assert gen.self_check(grid) == []
        observed.append(gen.observe_overrides(grid))
    assert observed == [
        {"grid_h": 11, "grid_w": 11, "scene_kind": "single"},
        {"grid_h": 13, "grid_w": 13, "scene_kind": "mixed"},
        {"grid_h": 12, "grid_w": 12, "scene_kind": "nested"},
        {"grid_h": 13, "grid_w": 13, "scene_kind": "mixed"},
    ]


def test_self_check_rejects_blank_malformed_and_off_grammar_grids():
    blank = [[0] * 13 for _ in range(13)]
    assert gen.self_check(blank)

    malformed = gen.generate(5, 1, scene_kind="nested")
    one_cell = next(
        (r, c)
        for r, row in enumerate(malformed)
        for c, value in enumerate(row)
        if value == 1
    )
    malformed[one_cell[0]][one_cell[1]] = 0
    assert gen.self_check(malformed)

    wrong_color = gen.generate(5, 0, scene_kind="single")
    wrong_color[0][0] = 8
    assert gen.self_check(wrong_color)

    unseeded = gen.generate(5, 0, scene_kind="single")
    for row in unseeded:
        for col, value in enumerate(row):
            if value == 2:
                row[col] = 0
    assert gen.self_check(unseeded)


def test_declared_witnesses_really_refute_their_named_rivals():
    nested = gen.generate(101, 7, scene_kind="nested")
    mixed = gen.generate(101, 8, scene_kind="mixed")

    intended_nested = gen.expected_output(nested)
    intended_mixed = gen.expected_output(mixed)
    assert gen.SEMANTIC_WITNESSES["nested_depth"](nested)
    assert (
        gen.SEMANTIC_RIVALS["fill_all_seeded_frames"](nested)
        != intended_nested
    )
    assert gen.SEMANTIC_WITNESSES["multiple_seeded_chains"](mixed)
    assert (
        gen.SEMANTIC_RIVALS["global_smallest_seeded_frame"](mixed)
        != intended_mixed
    )


def test_visible_training_pairs_leave_the_global_shortcut_alive_but_mixed_refutes_it():
    shortcut = gen.CANONICAL_SHORTCUTS["global_smallest_seeded_frame"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in TRAIN)
    assert any(shortcut(pair["input"]) != pair["output"] for pair in TEST)
    mixed = gen.generate(404, 2, scene_kind="mixed")
    assert shortcut(mixed) != gen.expected_output(mixed)


@pytest.mark.parametrize("start", range(6))
def test_every_query_rotation_of_a_scheduled_lesson_remains_identifiable(start):
    pairs = _lesson(7701, start)
    for query_index in range(len(pairs)):
        query = pairs[query_index]
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []


def test_census_regression_seed_remains_rotation_identifiable_after_materialization():
    # Regression for lesson-census medium lesson 48 (seed 1144200380):
    # the original schedule rejected sample 53 as a duplicate mixed pair, then
    # rotating sample 50 into the query left no mixed demonstration.
    pairs, accepted_indices = _materialized_lesson(1144200380, 48)
    assert len(accepted_indices) == gen.EXAMPLES_NEEDED + 1
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert gen.lesson_identifiable(demos, query) == []
