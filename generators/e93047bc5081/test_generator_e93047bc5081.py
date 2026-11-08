from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.e93047bc5081 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _canonical_rule_hash() -> str:
    root = Path(__file__).resolve().parents[3]
    for line in (root / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row["task_id"] == gen.TASK_ID:
            normalized = " ".join(row["program_solution"].split())
            return hashlib.sha256(normalized.encode()).hexdigest()[:12]
    raise AssertionError("canonical task row missing")


def test_rule_hash_and_all_canonical_inputs_are_pinned():
    assert gen.RULE_HASH == _canonical_rule_hash()
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen._python_apply(pair["input"]) == pair["output"]
        assert gen.strict_canonical_like(pair["input"]) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_override_boundaries_and_unknown_key_rejection(band):
    cases = [
        {"grid_h": 5, "grid_w": 5, "n_objs": 3, "marker_side": "top"},
        {"grid_h": 14, "grid_w": 14, "n_objs": 1, "marker_side": "bottom"},
        {"grid_h": 5, "grid_w": 14, "n_objs": 3, "marker_side": "left"},
        {"grid_h": 14, "grid_w": 5, "n_objs": 3, "marker_side": "right"},
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(1000 + index, index, difficulty=band, **overrides)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        for key, value in overrides.items():
            assert observed[key] == value
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, difficulty=band, typo_axis=1)


def test_every_four_consecutive_samples_identify_the_rule():
    for start in range(16):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(55, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": gen._python_apply(grid)})
        query_grid = gen.generate(55, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        query = {"input": query_grid, "output": gen._python_apply(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []


def test_semantic_rivals_have_generated_killing_witnesses():
    grids = [gen.generate(91, index, difficulty="medium") for index in range(20)]
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert any(gen._python_apply(grid) != rival(grid) for grid in grids), name


def test_declared_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name
