"""Focused regressions for generator 77e696585932."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module("puzzle_generators.per_puzzle.77e696585932.generator")


def _canonical_row():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == GEN.TASK_ID:
            return row
    raise AssertionError("canonical row missing")


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_all_canonical_pairs_are_accepted_and_exact():
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN._expected_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_three_example_schedule_covers_decisive_profiles_and_branches():
    for band in ("easy", "medium", "hard"):
        analyses = [GEN._analyze(GEN.generate(41, i, difficulty=band)) for i in range(3)]
        assert {item["profile"] for item in analyses} == set(GEN.SCENE_PROFILES)
        assert {branch for item in analyses for branch in item["branches"]} >= {
            "row", "column", "tie_row"
        }
        assert all(item["distractors"] for item in analyses)
        assert any({"above", "below"}.issubset(item["sides"]) for item in analyses)
        assert any({"left", "right"}.issubset(item["sides"]) for item in analyses)


def test_exact_axes_are_observable_at_all_boundaries():
    cases = (
        {"grid_h": 12}, {"grid_h": 20},
        {"grid_w": 12}, {"grid_w": 26},
        {"scene_profile": "rows"},
        {"scene_profile": "columns"},
        {"scene_profile": "cross"},
        {"matching_pixel_count": 3}, {"matching_pixel_count": 8},
        {"distractor_count": 1}, {"distractor_count": 3},
    )
    for band in ("easy", "medium", "hard"):
        for index, case in enumerate(cases):
            grid = GEN.generate(9000 + index, 7000 + index, difficulty=band, **case)
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            for key, expected in case.items():
                assert observed[key] == expected


def test_targeted_mutations_and_negative_recombination_reject():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert GEN.self_check(grid), name
    recombination = dict(fixtures)["novel_line_color_without_matching_pixel"]
    # Oracle mirror deliberately refuses the teaching-invalid recombination;
    # the canonical Racket runtime is checked separately in the review audit.
    with pytest.raises(ValueError):
        GEN._expected_output(recombination)


def test_named_rivals_are_actually_refuted():
    grids = {profile: GEN.generate(77, i, scene_profile=profile)
             for i, profile in enumerate(GEN.SCENE_PROFILES)}
    assert GEN._rival_columns_only(grids["rows"]) != GEN._expected_output(grids["rows"])
    assert GEN._rival_rows_only(grids["columns"]) != GEN._expected_output(grids["columns"])
    assert GEN._rival_tie_to_column(grids["cross"]) != GEN._expected_output(grids["cross"])
    for grid in grids.values():
        assert GEN._rival_keep_distractors(grid) != GEN._expected_output(grid)
        assert GEN._rival_move_only_first(grid) != GEN._expected_output(grid)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(20260725)
    state = random.getstate()
    first = GEN.generate(123, 456, difficulty="hard")
    pristine = copy.deepcopy(first)
    second = GEN.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(123, 456, difficulty="hard") == pristine


def test_unknown_and_invalid_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, invented_axis=True)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, grid_h=11)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, scene_profile="diagonal")


def test_selected_authority_and_rule_hash_are_synchronized():
    canonical = _canonical_row()["program_solution"]
    base = json.loads((ROOT / "data/base/solutions/training/1a07d186__77e696585932.json").read_text())
    target = base["racket_target"]
    assert target["target_code"] == canonical
    assert target["target_code_role"] == "selected_task_rule"
    assert target["raw_code_role"] == "archival_executable_source"
    assert GEN.RULE_HASH == _normalized_rule_hash(canonical) == "315cb8671701"
