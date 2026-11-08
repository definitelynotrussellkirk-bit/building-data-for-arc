from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import ROOT, canonical_pairs


TASK_ID = "b6592c220670"
BASE_PATH = ROOT / "data/base/solutions/banks/056856052daa/hard_p06__b6592c220670.json"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def test_rule_pin_canonical_pairs_and_selected_source_are_exact() -> None:
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "042a7b2c96f6"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]

    row = _canonical_row()
    target = json.loads(BASE_PATH.read_text(encoding="utf-8"))["racket_target"]
    assert target["target_code"] == row["program_solution"]
    assert target["raw_code"] != target["target_code"]


def test_four_sample_schedule_covers_semantics_and_refutes_rivals() -> None:
    grids = [gen.generate(1701, index, difficulty="medium") for index in range(4)]
    observed = [gen.observe_overrides(grid) for grid in grids]
    assert {item["first_code"] for item in observed} == {1, 2, 3, 4}
    assert {item["palette_relation"] for item in observed} == {"overlap", "disjoint"}
    assert any(item["motif_colors"] >= 2 for item in observed)

    demos = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]
    assert gen.lesson_identifiable(demos, demos[0]) == []

    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness_grid = next(
            grid for grid in grids if gen.SEMANTIC_WITNESSES[witness_name](grid)
        )
        answer = gen.rule_mirror(witness_grid)
        for rival_name in rival_names:
            assert gen.SEMANTIC_RIVALS[rival_name](witness_grid) != answer


def test_every_sliding_four_demo_window_is_identifiable() -> None:
    for start in range(12):
        grids = [gen.generate(8000 + start, start + offset, difficulty="hard") for offset in range(5)]
        pairs = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]
        assert gen.lesson_identifiable(pairs[:4], pairs[4]) == []


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_override_boundaries_are_exact_observable_and_band_safe(difficulty: str) -> None:
    case = 0
    for grid_h in (7, 16):
        for grid_w in (9, 20):
            for n_codes in (1, 6):
                for motif_cells in (4, 8):
                    for motif_colors in (1, 3):
                        for palette_relation in ("overlap", "disjoint"):
                            for first_code in (1, 4):
                                requested = {
                                    "grid_h": grid_h,
                                    "grid_w": grid_w,
                                    "n_codes": n_codes,
                                    "motif_cells": motif_cells,
                                    "motif_colors": motif_colors,
                                    "palette_relation": palette_relation,
                                    "first_code": first_code,
                                }
                                grid = gen.generate(
                                    9000 + case,
                                    case % 17,
                                    difficulty=difficulty,
                                    **requested,
                                )
                                assert gen.self_check(grid) == []
                                assert gen.observe_overrides(grid) == requested
                                case += 1

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)


def test_structural_mutations_are_rejected() -> None:
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_replay_is_fresh_deterministic_and_global_rng_pure() -> None:
    random.seed(20260726)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_palette_shortcuts_are_both_present_and_refuted() -> None:
    grids = [gen.generate(31415, index, difficulty="medium") for index in range(8)]
    relations = {gen.observe_overrides(grid)["palette_relation"] for grid in grids}
    assert relations == {"overlap", "disjoint"}
    multicolor = next(grid for grid in grids if gen.observe_overrides(grid)["motif_colors"] >= 2)
    assert gen.rule_mirror(multicolor) != gen.SEMANTIC_RIVALS["collapse_motif_to_one_color"](multicolor)
