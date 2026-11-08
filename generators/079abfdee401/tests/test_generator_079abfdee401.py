from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.079abfdee401.generator")
ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "079abfdee401"


def _canonical_task() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def test_rule_hash_and_all_canonical_pairs_are_owned_exactly():
    task = _canonical_task()
    assert gen.RULE_HASH == "a6a896998c77"
    pairs = task["train"] + task["test"]
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_ordinary_curriculum_is_canonical_scaled_and_semantically_decisive():
    witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    strict_hits = 0
    total = 0
    for band in ("easy", "medium", "hard"):
        for index in range(40):
            grid = gen.generate(7000 + index, index * 17 + 3, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            analysis = gen._analyze(grid)
            assert 7 <= analysis["height"] <= 24
            assert 7 <= analysis["width"] <= 24
            assert analysis["palette"] == {0, 1, 5}
            assert len(analysis["targets"]) in {2, 3}
            assert gen.rule_mirror(grid) != grid
            strict_hits += not gen.strict_canonical_like(grid)
            total += 1
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                witness_hits[name] += bool(witness(grid))
    assert strict_hits / total >= gen.MIN_STRICT_FRAC
    assert all(count > 0 for count in witness_hits.values())


def test_single_axis_override_boundaries_are_exact_and_observable():
    cases = [
        {"grid_h": 7},
        {"grid_h": 24},
        {"grid_w": 7},
        {"grid_w": 24},
        {"n_rectangles": 1},
        {"n_rectangles": 6},
    ]
    for band in ("easy", "medium", "hard"):
        for index, case in enumerate(cases):
            grid = gen.generate(8800 + index, 100 + index, difficulty=band, **case)
            assert gen.self_check(grid, difficulty=band, meta={"overrides": case}) == []
            observed = gen.observe_overrides(grid)
            for name, value in case.items():
                assert observed[name] == value


def test_every_declared_texture_materializes_a_distinct_valid_rival_rebuttal():
    signatures = set()
    for index, texture in enumerate(gen.HELPFUL_TEXTURES):
        grid = gen.generate(
            9900 + index,
            index,
            difficulty="medium",
            texture=texture,
        )
        assert gen.self_check(grid) == []
        analysis = gen._analyze(grid)
        signature = (
            any(gen._has_bar_decoy(grid) for _ in [0]),
            gen._has_non_solid_six_decoy(grid),
            gen._has_wrong_size_solid_decoy(grid),
            gen._has_gray_exact_target_shape(grid),
            len(analysis["blue_decoys"]),
        )
        signatures.add(signature)
    assert len(signatures) == len(gen.HELPFUL_TEXTURES)


def test_dense_impossible_combinations_reject_loudly_without_axis_drift():
    with pytest.raises(ValueError, match="requested combination cannot fit"):
        gen.generate(
            123,
            456,
            difficulty="hard",
            grid_h=7,
            grid_w=7,
            n_rectangles=6,
            texture="six_decoys",
        )


def test_mutation_fixtures_are_all_rejected_by_structural_self_check():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_four_demonstrations_identify_the_rule_and_replay_is_pure():
    demos = []
    for index in range(gen.EXAMPLES_NEEDED):
        source = gen.generate(17000, index, difficulty="medium")
        demos.append({"input": source, "output": gen.rule_mirror(source)})
    query_source = gen.generate(17000, gen.EXAMPLES_NEEDED, difficulty="medium")
    assert gen.lesson_identifiable(demos, {"input": query_source}) == []

    random.seed(20260725)
    state = random.getstate()
    first = gen.generate(31337, 2718, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(31337, 2718, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
