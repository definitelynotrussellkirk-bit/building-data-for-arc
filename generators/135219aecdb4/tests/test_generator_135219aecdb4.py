"""Focused semantic and regression tests for generator 135219aecdb4."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root


TASK_ID = "135219aecdb4"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = find_root(__file__)


def _canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _canonical_pairs():
    row = _canonical_row()
    return list(row["train"]) + list(row["test"])


def _pair(seed, sample_index, band):
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_canonical_inputs_and_outputs_match_three_pass_rule():
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_rule_hash_and_selected_authority_are_synchronized():
    canonical = _canonical_row()["program_solution"]
    normalized = " ".join(canonical.split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH

    base = json.loads(
        (canonical_path(ROOT).parents[1]
         / "base/solutions/training/4cd1b7b2__135219aecdb4.json")
        .read_text(encoding="utf-8")
    )
    target = base["racket_target"]
    assert target["target_code"] == canonical
    assert target["raw_code"] != canonical


def test_default_three_slot_schedule_requires_three_pass_witness():
    for band in ("easy", "medium", "hard"):
        expected_n = {"easy": 5, "medium": 6, "hard": 7}[band]
        for start in range(6):
            lesson = [_pair(9000 + start, start + offset, band) for offset in range(4)]
            demos, query = lesson[:3], lesson[3]
            assert GEN.lesson_identifiable(demos, query) == []
            facts = [GEN.semantic_observables(pair["input"]) for pair in demos]
            assert {fact["n_erased"] for fact in facts} == {expected_n}
            assert any(fact["passes_to_complete"] == 1 for fact in facts)
            assert any(fact["passes_to_complete"] == 3 for fact in facts)
            assert any(fact["joint_forced_count"] >= 1 for fact in facts)
            # Five-hole three-pass chains necessarily erase only two symbol
            # values; the lesson-level fixed-color shortcut is still refuted by
            # the one-pass and joint-constraint demonstrations.
            assert any(fact["missing_symbol_count"] >= 3 for fact in facts)
            assert len({fact["completed_square"] for fact in facts}) >= 2


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_cascade_slot_always_refutes_a_two_pass_shortcut(band):
    for seed in range(12):
        grid = GEN.generate(seed, 1, difficulty=band)
        facts = GEN.semantic_observables(grid)
        assert facts["passes_to_complete"] == 3


def test_exact_erased_count_override_boundaries_in_every_band():
    for band in ("easy", "medium", "hard"):
        for n_erased in (1, 10):
            grid = GEN.generate(1729, 41, difficulty=band, n_erased=n_erased)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == {"n_erased": n_erased}
            assert sum(value == 0 for row in grid for value in row) == n_erased
            assert GEN.rule_mirror(grid) != grid


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260726)
    before = random.getstate()
    first = GEN.generate(90210, 17, difficulty="hard")
    second = GEN.generate(90210, 17, difficulty="hard")
    assert random.getstate() == before
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second, strict=True))
    first[0][0] = 9
    assert GEN.generate(90210, 17, difficulty="hard") == second


def test_unknown_invalid_overrides_and_difficulty_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, bogus_axis=1)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, n_erased=0)
    with pytest.raises(ValueError):
        GEN.generate(1, 0, n_erased=11)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 0, difficulty="extreme")


@pytest.mark.parametrize("invalid", [True, 1.9, "3"])
def test_n_erased_override_rejects_non_exact_integers(invalid):
    """Catch coercion that silently changes an exact experimental slice."""
    with pytest.raises(ValueError, match="n_erased must be an exact integer"):
        GEN.generate(1, 0, n_erased=invalid)


def test_self_check_rejects_targeted_structural_impostors():
    valid = GEN.generate(77, 2, difficulty="medium")
    assert GEN.self_check(valid) == []

    no_holes = GEN.rule_mirror(valid)
    illegal_color = copy.deepcopy(valid)
    illegal_color[0][0] = 9
    boolean_cell = copy.deepcopy(valid)
    boolean_cell[0][0] = True
    repeated_row = copy.deepcopy(valid)
    repeated_row[0] = [1, 1, 0, 0]
    repeated_col = copy.deepcopy(valid)
    repeated_col[0][0] = 1
    repeated_col[1][0] = 1
    all_erased = [[0] * 4 for _ in range(4)]
    ragged = copy.deepcopy(valid)
    ragged[0].pop()

    for mutation in (
        no_holes,
        illegal_color,
        boolean_cell,
        repeated_row,
        repeated_col,
        all_erased,
        ragged,
    ):
        assert GEN.self_check(mutation), mutation


def test_named_rivals_are_refuted_by_their_witnesses():
    grids = [GEN.generate(31415, index, difficulty="hard") for index in range(12)]
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        firing = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert firing, witness_name
        for grid in firing:
            official = GEN.rule_mirror(grid)
            assert any(GEN.SEMANTIC_RIVALS[name](grid) != official for name in rival_names)
