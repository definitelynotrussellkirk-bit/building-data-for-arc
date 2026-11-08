from __future__ import annotations

import importlib
import json
import random
from copy import deepcopy
from pathlib import Path

import pytest


TASK_ID = "3f851af785f7"
ROOT = Path(__file__).resolve().parents[1]
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [pair for split in ("train", "test") for pair in row[split]]


def test_rule_pin_canonical_pairs_and_selected_authority_are_exact():
    row = _canonical_row()
    assert gen.RULE_HASH == "846fcfd56ec8"
    assert gen.VERSION == "2.0.0"
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original

    base = json.loads(
        (ROOT / "data/base/solutions/banks/884454e62c49/E23__3f851af785f7.json")
        .read_text(encoding="utf-8")
    )
    assert base["racket_target"]["target_code"] == row["program_solution"]


def test_boundary_overrides_are_exact_observable_and_band_safe():
    cases = (
        {"grid_h": 7, "grid_w": 7, "n_shapes": 4, "palette_kind": "varied"},
        {"grid_h": 16, "grid_w": 16, "n_shapes": 1, "palette_kind": "default"},
        {"grid_h": 7, "grid_w": 16, "n_shapes": 4, "palette_kind": "warm"},
        {"grid_h": 16, "grid_w": 7, "n_shapes": 4, "palette_kind": "cool"},
    )
    for difficulty in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = gen.generate(index, 100 + index, difficulty=difficulty, **overrides)
            assert gen.self_check(grid, difficulty=difficulty) == []
            observed = gen.observe_overrides(grid)
            assert {axis: observed[axis] for axis in overrides} == overrides

    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(1, 2, typo_axis=3)


def test_four_sample_schedule_anchors_canonical_profiles_without_fixing_layout():
    profiles = []
    layouts = set()
    for sample_index in range(12):
        grid = gen.generate(77, sample_index, difficulty="hard")
        assert gen.self_check(grid) == []
        colors = {value for row in grid for value in row}
        profile = (len(grid), len(grid[0]), len(colors))
        if sample_index % 4 == 0:
            profiles.append(profile)
        layouts.add(tuple(tuple(row) for row in grid))
    assert profiles == [(7, 7, 3), (7, 8, 3), (9, 9, 4)]
    assert len(layouts) == 12


def test_self_check_rejects_named_impostors_and_negative_recombination():
    for name, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), name

    valid = gen.generate(9, 5, difficulty="medium", n_shapes=2, palette_kind="warm")
    analysis = gen._analyze(valid)
    assert analysis["errors"] == []
    recombined = deepcopy(valid)
    # A color absent from every remaining scene part turns one monochrome L into
    # a mixed-color near-match.  The Racket oracle can execute it, but the
    # teaching distribution must reject it.
    row, col = sorted(analysis["components"][0]["cells"])[0]
    replacement = next(color for color in range(1, 10) if color not in {v for r in valid for v in r})
    recombined[row][col] = replacement
    assert gen.self_check(recombined)
    oracle_output = gen.rule_mirror(recombined)
    assert len(oracle_output) == len(recombined)
    assert len(oracle_output[0]) == len(recombined[0])


def test_all_missing_corner_branches_and_shape_counts_have_support():
    corner_counts = {corner: 0 for corner in gen.MISSING_CORNERS}
    shape_counts = {count: 0 for count in range(1, 5)}
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(80):
            grid = gen.generate(seed, seed * 17 + 3, difficulty=difficulty)
            facts = gen._analyze(grid)
            assert facts["errors"] == []
            shape_counts[len(facts["components"])] += 1
            for window in facts["active_windows"]:
                corner_counts[(window["missing"][0] - window["row"], window["missing"][1] - window["col"])] += 1
    assert all(count > 0 for count in corner_counts.values())
    assert all(count > 0 for count in shape_counts.values())


def test_replay_freshness_input_purity_and_global_rng_purity():
    random.seed(20260725)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second

    source = gen.generate(33, 19, difficulty="easy")
    frozen = deepcopy(source)
    _ = gen.rule_mirror(source)
    assert source == frozen
