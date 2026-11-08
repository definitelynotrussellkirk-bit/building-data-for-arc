"""Focused regressions for generator 2ad9e1922f57."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

TASK_ID = "2ad9e1922f57"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
AUTHORITY = ROOT / "data/base/solutions/banks/1cd6e373f225/hard_p04__2ad9e1922f57.json"


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical task {TASK_ID}")


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN._authority_output(grid)}


def test_metadata_rule_pin_and_selected_authority_are_exact():
    canonical = _canonical_row()
    authority = json.loads(AUTHORITY.read_text())
    selected = authority["racket_target"]["target_code"]
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "3.0.0"
    assert selected == canonical["program_solution"]
    assert GEN.RULE_HASH == _normalized_hash(selected) == "07dadf929353"


def test_all_canonical_pairs_are_accepted_and_solved_exactly():
    canonical = _canonical_row()
    pairs = list(canonical["train"]) + list(canonical["test"])
    assert len(pairs) == 4
    for pair in pairs:
        grid = pair["input"]
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN._authority_output(grid) == pair["output"]


def test_four_slot_curriculum_is_complete_in_every_band():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos = []
            for index in range(start, start + 4):
                grid = GEN.generate(500 + start, index, difficulty=band)
                assert GEN.self_check(grid) == []
                demos.append(_pair(grid))
            query = _pair(GEN.generate(700 + start, start + 4, difficulty=band))
            assert GEN.lesson_identifiable(demos, query) == []
            assert {code for demo in demos for code in GEN._codes(demo["input"])} == {1, 2, 3, 4}
            assert any(
                len(GEN._codes(demo["input"])) != len(set(GEN._codes(demo["input"])))
                for demo in demos
            )
            assert any(
                GEN._analysis(demo["input"])["motif_shape"] in ("wide", "tall")
                for demo in demos
            )


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 9, "grid_w": 10, "n_codes": 2, "motif_color": 5,
         "motif_cells": 5, "motif_shape": "square", "motif_position": "left"},
        {"grid_h": 12, "grid_w": 14, "n_codes": 4, "motif_color": 9,
         "motif_cells": 8, "motif_shape": "wide", "motif_position": "center"},
        {"grid_h": 10, "grid_w": 12, "n_codes": 3, "motif_color": 7,
         "motif_cells": 7, "motif_shape": "tall", "motif_position": "right"},
    ],
)
def test_representative_boundary_overrides_are_exact(band, overrides):
    grid = GEN.generate(991, 37, difficulty=band, **overrides)
    assert GEN.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
    assert GEN.observe_overrides(grid) == overrides


def test_unknown_and_invalid_overrides_are_rejected():
    bad_calls = (
        {"unknown": 1},
        {"grid_h": 8},
        {"grid_w": 15},
        {"n_codes": 1},
        {"motif_color": 4},
        {"motif_cells": 9},
        {"motif_shape": "diagonal"},
        {"motif_position": "top"},
    )
    for overrides in bad_calls:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 2, **overrides)


def test_self_check_rejects_targeted_near_misses():
    base = GEN.generate(123, 2, difficulty="hard")

    gapped_program = copy.deepcopy(base)
    gapped_program[0][1], gapped_program[0][4] = 0, gapped_program[0][1]

    dirty_separator = copy.deepcopy(base)
    dirty_separator[1][0] = 9

    multicolor = copy.deepcopy(base)
    motif = [(r, c) for r in range(3, len(base)) for c, v in enumerate(base[r]) if v]
    multicolor[motif[0][0]][motif[0][1]] = 6 if base[motif[0][0]][motif[0][1]] != 6 else 7

    disconnected = copy.deepcopy(base)
    r, c = motif[0]
    disconnected[r][c] = 0
    disconnected[-1][-1] = GEN._analysis(base)["motif_color"]

    ragged = copy.deepcopy(base)
    ragged[0].pop()

    for mutation in (gapped_program, dirty_separator, multicolor, disconnected, ragged):
        assert GEN.self_check(mutation), mutation


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(20260727)
    state = random.getstate()
    first = GEN.generate(2026, 727, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(2026, 727, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
