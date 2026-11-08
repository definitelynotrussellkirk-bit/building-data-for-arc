from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.ab00df6984f7 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _canonical_program_solution() -> str:
    root = Path(__file__).resolve().parents[3]
    with (root / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return str(row["program_solution"])
    raise AssertionError("canonical task row missing")


def test_rule_hash_and_all_canonical_pairs_are_pinned() -> None:
    normalized = " ".join(_canonical_program_solution().split())
    assert gen.RULE_HASH == hashlib.sha256(normalized.encode()).hexdigest()[:12]
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_override_boundaries_are_observable(band: str) -> None:
    cases = [
        {
            "grid_h": 7,
            "grid_w": 9,
            "bbox_h": 3,
            "bbox_w": 3,
            "palette_size": 2,
            "component_count": 1,
        },
        {
            "grid_h": 14,
            "grid_w": 16,
            "bbox_h": 5,
            "bbox_w": 7,
            "palette_size": 5,
            "component_count": 4,
        },
        {
            "grid_h": 7,
            "grid_w": 16,
            "bbox_h": 5,
            "bbox_w": 7,
            "palette_size": 5,
            "component_count": 3,
        },
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(900 + index, 400 + index, difficulty=band, **overrides)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        for key, value in overrides.items():
            assert observed[key] == value
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, difficulty=band, typo_axis=1)


def test_every_two_demo_window_identifies_the_rule() -> None:
    for start in range(24):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(55, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(55, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        assert gen.lesson_identifiable(demos, {"input": query_grid}) == []


def test_one_component_monochrome_only_is_not_an_identifiable_lesson() -> None:
    grid = gen.generate(77, 5, difficulty="medium")
    assert gen.observe_overrides(grid)["component_count"] == 1
    assert gen.observe_overrides(grid)["palette_size"] == 2
    demo = {"input": grid, "output": gen.rule_mirror(grid)}
    reasons = gen.lesson_identifiable([demo, copy.deepcopy(demo)], {"input": grid})
    assert any("largest_component_only" in reason for reason in reasons)
    assert any("monochrome_crop" in reason for reason in reasons)


def test_semantic_rivals_have_generated_killing_witnesses() -> None:
    grids = [gen.generate(91, index, difficulty="medium") for index in range(16)]
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert any(gen.rule_mirror(grid) != rival(grid) for grid in grids), name


def test_mutation_fixtures_are_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    state = random.getstate()
    first = gen.generate(717, 19, difficulty="hard")
    assert random.getstate() == state
    replay = gen.generate(717, 19, difficulty="hard")
    assert first == replay
    assert first is not replay
    assert all(a is not b for a, b in zip(first, replay))

    expected = copy.deepcopy(replay)
    first[0][0] = 9
    assert gen.generate(717, 19, difficulty="hard") == expected
    assert gen.generate(717, 20, difficulty="hard") != expected
