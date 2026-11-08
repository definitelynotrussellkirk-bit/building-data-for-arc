"""Focused semantic and contract regressions for d47a6fca9d15."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.d47a6fca9d15 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs

ROOT = Path(__file__).resolve().parents[1]
BANDS = ("easy", "medium", "hard")


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError(f"canonical task {gen.TASK_ID} not found")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_rule_hash_and_every_canonical_pair_are_exact() -> None:
    row = _canonical_row()
    assert gen.RULE_HASH == "4f2a3760d35b"
    assert gen.RULE_HASH == _normalized_hash(row["program_solution"])

    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        snapshot = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == snapshot

    # These are not hypothetical: both shortcuts fit all four canonical pairs.
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


def test_exact_override_boundaries_round_trip_in_every_band() -> None:
    cases = (
        {
            "grid_h": 8,
            "grid_w": 11,
            "size_profile": "canonical_235",
            "rank_order": "ascending",
        },
        {
            "grid_h": 10,
            "grid_w": 13,
            "size_profile": "bbox_conflict_145",
            "rank_order": "descending",
        },
        {
            "grid_h": 9,
            "grid_w": 12,
            "size_profile": "shifted_357",
            "rank_order": "mixed",
        },
    )
    for band in BANDS:
        for index, overrides in enumerate(cases):
            grid = gen.generate(4701, index, difficulty=band, **overrides)
            assert gen.self_check(grid, meta={"overrides": overrides}) == []
            assert gen.observe_overrides(grid) == overrides


@pytest.mark.parametrize(
    "overrides",
    (
        {"grid_h": 7},
        {"grid_w": 14},
        {"size_profile": "invented"},
        {"rank_order": "leftmost"},
    ),
)
def test_invalid_override_values_are_rejected(overrides: dict) -> None:
    with pytest.raises(ValueError):
        gen.generate(1, 0, **overrides)


def test_unknown_override_and_difficulty_are_rejected() -> None:
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 0, misspelled_axis="ignored-before-repair")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="expert")


def test_every_sliding_three_demo_window_is_identifiable() -> None:
    for seed in (0, 1, 17, 31337):
        for band in BANDS:
            for start in range(12):
                demos = []
                for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
                    grid = gen.generate(seed, sample_index, difficulty=band)
                    demos.append({"input": grid, "output": gen.rule_mirror(grid)})
                query_grid = gen.generate(
                    seed, start + gen.EXAMPLES_NEEDED, difficulty=band
                )
                query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
                assert gen.lesson_identifiable(demos, query) == []
                assert {
                    gen.observe_overrides(demo["input"])["size_profile"]
                    for demo in demos
                } == set(gen.SIZE_PROFILES)
                assert {
                    gen.observe_overrides(demo["input"])["rank_order"]
                    for demo in demos
                } == set(gen.RANK_ORDERS)


def test_generated_schedule_refutes_every_named_rival_and_covers_witnesses() -> None:
    grids = [
        gen.generate(808, index, difficulty="medium")
        for index in range(gen.EXAMPLES_NEEDED)
    ]
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(grid) != gen.rule_mirror(grid) for grid in grids), name
    for name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), name


def test_bbox_and_absolute_shortcuts_are_deliberately_broken() -> None:
    bbox_grid = gen.generate(
        19,
        0,
        size_profile="bbox_conflict_145",
        rank_order="mixed",
    )
    shifted_grid = gen.generate(
        19,
        0,
        size_profile="shifted_357",
        rank_order="mixed",
    )
    assert gen._rival_bbox_area(bbox_grid) != gen.rule_mirror(bbox_grid)
    assert gen._rival_absolute_buckets(shifted_grid) != gen.rule_mirror(shifted_grid)


def test_self_check_rejects_all_targeted_mutation_fixtures() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 8
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_default_distribution_is_strict_and_observable() -> None:
    seen_profiles = set()
    seen_orders = set()
    seen_dimensions = set()
    for band in BANDS:
        for seed in range(8):
            for sample_index in range(12):
                grid = gen.generate(seed, sample_index, difficulty=band)
                assert gen.self_check(grid) == []
                assert gen.strict_canonical_like(grid) == []
                observed = gen.observe_overrides(grid)
                seen_profiles.add(observed["size_profile"])
                seen_orders.add(observed["rank_order"])
                seen_dimensions.add((observed["grid_h"], observed["grid_w"]))
    assert seen_profiles == set(gen.SIZE_PROFILES)
    assert seen_orders == set(gen.RANK_ORDERS)
    assert seen_dimensions == {
        (h, w) for h in range(8, 11) for w in range(11, 14)
    }


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(112358)
    state_before = random.getstate()
    first = gen.generate(12345, 77, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(12345, 77, difficulty="hard")
    assert state_before == state_after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == gen.generate(12345, 77, difficulty="hard")
