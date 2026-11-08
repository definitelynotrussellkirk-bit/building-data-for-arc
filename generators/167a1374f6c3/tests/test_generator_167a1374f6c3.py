"""Focused regressions for generator 167a1374f6c3."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "167a1374f6c3"
HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared" / "runtime"))
SPEC = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_row():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN._authority_output(grid)}


def test_metadata_rule_pin_and_canonical_authority_are_exact():
    canonical = _canonical_row()
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "2.0.0"
    assert GEN.RULE_HASH == _normalized_hash(canonical["program_solution"]) == "91349b01b34b"


def test_all_canonical_pairs_are_accepted_and_solved_exactly():
    canonical = _canonical_row()
    pairs = list(canonical["train"]) + list(canonical["test"])
    assert len(pairs) == 4
    for pair in pairs:
        grid = pair["input"]
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN._authority_output(grid) == pair["output"]


def test_three_slot_curriculum_is_complete_in_every_band():
    for band in ("easy", "medium", "hard"):
        for start in range(9):
            demos = []
            for index in range(start, start + 3):
                grid = GEN.generate(500 + start, index, difficulty=band)
                assert GEN.self_check(grid) == []
                demos.append(_pair(grid))
            query = _pair(GEN.generate(700 + start, start + 3, difficulty=band))
            assert GEN.lesson_identifiable(demos, query) == []
            assert {code for demo in demos for code in GEN._codes(demo["input"])} == {1, 2, 3, 4}
            assert any(
                len(GEN._codes(demo["input"])) != len(set(GEN._codes(demo["input"])))
                for demo in demos
            )
            assert {GEN._analysis(demo["input"])["motif_connectivity"] for demo in demos} == {
                "connected",
                "disconnected",
            }
            assert any(
                GEN._analysis(demo["input"])["motif_shape"] in ("wide", "tall")
                for demo in demos
            )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 7, "grid_w": 10, "n_codes": 1, "motif_color": 5,
         "motif_cells": 3, "motif_connectivity": "connected"},
        {"grid_h": 14, "grid_w": 16, "n_codes": 5, "motif_color": 9,
         "motif_cells": 8, "motif_connectivity": "disconnected"},
        {"grid_h": 8, "grid_w": 12, "n_codes": 3, "motif_color": 7,
         "motif_cells": 4, "motif_connectivity": "disconnected"},
    ],
)
def test_representative_boundary_overrides_are_exact(band, overrides):
    grid = GEN.generate(991, 37, difficulty=band, **overrides)
    assert GEN.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
    assert GEN.observe_overrides(grid) == overrides


def test_unknown_and_invalid_overrides_are_rejected():
    bad_calls = (
        {"unknown": 1},
        {"grid_h": 6},
        {"grid_w": 17},
        {"n_codes": 0},
        {"motif_color": 4},
        {"motif_cells": 9},
        {"motif_connectivity": "diagonal"},
    )
    for overrides in bad_calls:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 2, **overrides)


def test_declared_canonical_shortcut_is_real_and_generated_lessons_refute_it():
    canonical = _canonical_row()
    shortcut = GEN.CANONICAL_SHORTCUTS["deduplicate_codes"]
    for pair in list(canonical["train"]) + list(canonical["test"]):
        assert shortcut(pair["input"]) == pair["output"]

    witness = GEN.generate(20261003, 0, difficulty="medium")
    assert len(GEN._codes(witness)) != len(set(GEN._codes(witness)))
    assert shortcut(witness) != GEN._authority_output(witness)
    assert GEN.SEMANTIC_WITNESSES["repeated_code_visible"](witness)


def test_self_check_rejects_targeted_near_misses():
    base = GEN.generate(123, 0, difficulty="hard")

    gapped_program = copy.deepcopy(base)
    gapped_program[0][1], gapped_program[0][5] = 0, gapped_program[0][1]

    dirty_separator = copy.deepcopy(base)
    dirty_separator[1][0] = 9

    multicolor = copy.deepcopy(base)
    motif = [(r, c) for r in range(2, len(base)) for c, v in enumerate(base[r]) if v]
    multicolor[motif[0][0]][motif[0][1]] = 6 if base[motif[0][0]][motif[0][1]] != 6 else 7

    ragged = copy.deepcopy(base)
    ragged[0].pop()

    for mutation in (gapped_program, dirty_separator, multicolor, ragged):
        assert GEN.self_check(mutation), mutation


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(20261003)
    state = random.getstate()
    first = GEN.generate(2026, 1003, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(2026, 1003, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))


def test_default_schedule_varies_program_order_without_losing_slot_semantics():
    programs_by_slot = {
        slot: {
            tuple(GEN._codes(GEN.generate(seed, slot, difficulty="medium")))
            for seed in range(40)
        }
        for slot in range(3)
    }
    assert all(len(programs) >= 2 for programs in programs_by_slot.values())
    assert all(len(program) == 3 and len(set(program)) == 2 for program in programs_by_slot[0])
    assert all(set(program) == {2, 3} for program in programs_by_slot[1])
    assert all(set(program) == {1, 3, 4} for program in programs_by_slot[2])
