from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.c94f3e28d713 import generator as gen
from scripts.canonical_profile_gate import canonical_pairs


def _canonical_rule_hash() -> str:
    root = Path(__file__).resolve().parents[3]
    for line in (root / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            normalized = " ".join(row["program_solution"].split())
            return hashlib.sha256(normalized.encode()).hexdigest()[:12]
    raise AssertionError("canonical row missing")


def test_rule_hash_and_all_canonical_pairs():
    assert gen.RULE_HASH == _canonical_rule_hash()
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_override_boundaries_and_unknown_axis(band):
    cases = [
        dict(grid_h=9, grid_w=9, n_objs=3, marker_pairing="same", shape_cells=5, docking_state="all_move"),
        dict(grid_h=9, grid_w=14, n_objs=2, marker_pairing="reverse", shape_cells=2, docking_state="one_docked"),
        dict(grid_h=14, grid_w=9, n_objs=3, marker_pairing="reverse", shape_cells=4, docking_state="all_move"),
        dict(grid_h=14, grid_w=14, n_objs=2, marker_pairing="same", shape_cells=3, docking_state="one_docked"),
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(1000 + index, index, difficulty=band, **overrides)
        assert gen.self_check(grid) == []
        observed = gen.observe_overrides(grid)
        assert all(observed[key] == value for key, value in overrides.items())
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, difficulty=band, typo_axis=1)


def test_every_four_consecutive_samples_identify_rule():
    for start in range(16):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(55, sample_index, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        q_grid = gen.generate(55, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        assert gen.lesson_identifiable(
            demos, {"input": q_grid, "output": gen.rule_mirror(q_grid)}
        ) == []


def test_rivals_have_default_killing_witnesses():
    grids = [gen.generate(91, index, difficulty="medium") for index in range(12)]
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert any(gen.rule_mirror(grid) != rival(grid) for grid in grids), name


def test_declared_mutations_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_determinism_fresh_returns_and_global_rng_state():
    random.seed(123456)
    before = random.getstate()
    first = gen.generate(777, 9, difficulty="hard")
    after = random.getstate()
    second = gen.generate(777, 9, difficulty="hard")
    assert first == second
    assert first is not second and first[0] is not second[0]
    assert before == after
