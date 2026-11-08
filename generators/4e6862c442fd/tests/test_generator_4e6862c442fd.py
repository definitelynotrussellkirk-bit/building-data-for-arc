from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import importlib

gen = importlib.import_module("puzzle_generators.per_puzzle.4e6862c442fd.generator")


ROOT = Path(__file__).resolve().parents[1]


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row not found")


def test_canonical_inputs_are_accepted_and_python_mirror_matches():
    row = _canonical_row()
    pairs = list(row["train"]) + [row["test"]]
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_all_schedule_profiles_are_valid_observable_and_identifiable(difficulty):
    for start in range(len(gen.SCHEDULE_PROFILES)):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(1234, sample_index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            assert set(observed) == set(gen.AXES)
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(1234, start + gen.EXAMPLES_NEEDED, difficulty=difficulty)
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []


def test_boundary_overrides_are_exact_and_unknown_keys_reject():
    cases = [
        {"grid_h": 12, "grid_w": 18, "source_basis": 0, "target_basis": 7, "motif_id": 0},
        {"grid_h": 18, "grid_w": 26, "source_basis": 7, "target_basis": 0, "motif_id": 7},
        {"grid_h": 12, "grid_w": 26, "source_basis": 3, "target_basis": 3, "motif_id": 5},
        {"grid_h": 18, "grid_w": 18, "source_basis": 4, "target_basis": 2, "motif_id": 2},
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(9000 + index, 17, difficulty="hard", **overrides)
        assert gen.observe_overrides(grid) == overrides
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, typo_axis=1)


def test_generation_is_deterministic_fresh_and_does_not_mutate_prior_return():
    first = gen.generate(77, 5, difficulty="medium")
    expected = copy.deepcopy(first)
    first[0][0] = 9
    second = gen.generate(77, 5, difficulty="medium")
    assert second == expected
    assert second is not first
    assert all(a is not b for a, b in zip(second, first))


def test_self_check_rejects_targeted_structural_impostors():
    grid = gen.generate(222, 6, difficulty="hard")
    analysis = gen._analyze(grid)

    missing_marker = copy.deepcopy(grid)
    r, c = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3)
    missing_marker[r][c] = 0
    assert gen.self_check(missing_marker)

    collinear_frame = copy.deepcopy(grid)
    origin = analysis["source_origin"]
    vx = analysis["source_basis_value"][0]
    old_r, old_c = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 4)
    collinear_frame[old_r][old_c] = 0
    new_r, new_c = origin[0] - vx[0], origin[1] - vx[1]
    collinear_frame[new_r][new_c] = 4
    assert any("perpendicular" in e for e in gen.self_check(collinear_frame))

    noncatalog_motif = copy.deepcopy(grid)
    mr, mc = analysis["motif_cells"][0]
    noncatalog_motif[mr][mc] = 0
    assert gen.self_check(noncatalog_motif)

    occupied_target = copy.deepcopy(grid)
    tr, tc = analysis["target_footprint"][0]
    occupied_target[tr][tc] = 8
    assert any("target copy cell" in e or "catalogued" in e for e in gen.self_check(occupied_target))


def test_named_rivals_are_real_counterexamples_on_their_witnesses():
    for profile in gen.SCHEDULE_PROFILES:
        grid = gen.generate(31415, profile, difficulty="easy")
        truth = gen.rule_mirror(grid)
        for witness, rivals in gen.WITNESS_RIVALS.items():
            if gen.SEMANTIC_WITNESSES[witness](grid):
                assert any(gen.SEMANTIC_RIVALS[name](grid) != truth for name in rivals)
