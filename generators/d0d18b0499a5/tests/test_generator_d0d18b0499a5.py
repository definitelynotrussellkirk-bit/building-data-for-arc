"""Focused regression tests for d0d18b0499a5."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.d0d18b0499a5 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "data/base/solutions/banks/129d068bbf4e/S18_M4__d0d18b0499a5.json"


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_authorities_are_pinned():
    canonical = next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == gen.TASK_ID
    )
    base = json.loads(AUTHORITY.read_text())
    assert gen.RULE_HASH == _normalized_hash(canonical["program_solution"])
    assert gen.RULE_HASH == _normalized_hash(base["racket_target"]["target_code"])
    assert gen.RULE_HASH == "e70c66638e4c"


def test_all_canonical_pairs_are_accepted_and_mirror_exactly():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    signatures = set()
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert gen.rule_mirror(source) == pair["output"]
        assert source == before
        signatures.add(gen.canonical_profile_signature(source))
    assert signatures == gen._CANONICAL_SIGNATURES


def test_every_three_slot_lesson_refutes_named_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(6):
            episode = [_pair(4000 + start, start + offset, band) for offset in range(4)]
            demos, query = episode[: gen.EXAMPLES_NEEDED], episode[-1]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos), name


def test_schedule_profiles_cover_every_sliding_window():
    expected = set(gen.SCHEDULE_PROFILES)
    for start in range(6):
        observed = {
            gen.schedule_profile(0, start + offset)
            for offset in range(gen.EXAMPLES_NEEDED)
        }
        assert observed == expected


def test_exact_override_axes_round_trip_at_boundaries_in_every_band():
    cases = (
        {"grid_h": 5, "grid_w": 8, "n_active_rows": 3, "n_distinct_colors": 1},
        {"grid_h": 18, "grid_w": 22, "n_active_rows": 5, "n_distinct_colors": 3},
        {"grid_h": 9, "grid_w": 13, "n_active_rows": 4, "n_distinct_colors": 2},
    )
    for band in ("easy", "medium", "hard"):
        for sample_index in range(3):
            for overrides in cases:
                grid = gen.generate(91, sample_index, difficulty=band, **overrides)
                assert gen.observe_overrides(grid) == overrides
                assert gen.self_check(grid, meta={"overrides": overrides}) == []


def test_unknown_override_fails_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)


def test_self_check_rejects_structural_impostors():
    valid = gen.generate(123, 1, difficulty="medium")
    ragged = copy.deepcopy(valid)
    ragged[0].pop()
    boolean = copy.deepcopy(valid)
    boolean[0][0] = True
    all_empty = [[0] * 10 for _ in range(7)]
    pair_only = [[0] * 10 for _ in range(7)]
    pair_only[2][1] = 2
    pair_only[2][5] = 2
    decoy_only = [[0] * 10 for _ in range(7)]
    for column in (1, 4, 7):
        decoy_only[2][column] = 2
    adjacent_pairs = [[0] * 10 for _ in range(7)]
    adjacent_pairs[1][1] = adjacent_pairs[1][2] = 2
    adjacent_pairs[3][4] = adjacent_pairs[3][5] = 3
    adjacent_pairs[5][7] = 4
    solid_2x2 = [[0] * 8 for _ in range(5)]
    solid_2x2[1][1] = solid_2x2[1][2] = 2
    solid_2x2[2][1] = solid_2x2[2][2] = 2
    for fixture in (ragged, boolean, all_empty, pair_only, decoy_only, adjacent_pairs, solid_2x2):
        assert gen.self_check(fixture), fixture


def test_generation_is_deterministic_fresh_and_rng_isolated():
    random.seed(20260727)
    before = random.getstate()
    first = gen.generate(44, 8, difficulty="hard")
    after = random.getstate()
    second = gen.generate(44, 8, difficulty="hard")
    assert after == before
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))


def test_strict_anchor_support_exists_in_every_band():
    for band in ("easy", "medium", "hard"):
        for sample_index in (0, 3, 6):
            grid = gen.generate(808, sample_index, difficulty=band)
            assert gen.strict_canonical_like(grid) == []
