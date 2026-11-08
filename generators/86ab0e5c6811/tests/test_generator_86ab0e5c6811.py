"""Focused regression tests for generator 86ab0e5c6811."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

import pytest

from scripts.generator_module_loader import load_module_from_path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "86ab0e5c6811"
DEFAULT_PATH = ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
MODULE_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_PATH))
GEN = load_module_from_path(f"test_generator_{TASK_ID}_{abs(hash(str(MODULE_PATH)))}", MODULE_PATH)


def _canonical_inputs():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [pair["input"] for pair in row["train"] + row["test"]]
    raise AssertionError("canonical task row not found")


def _valid_grid():
    return GEN.generate(
        941,
        0,
        difficulty="medium",
        grid_h=10,
        grid_w=12,
        blob_size=4,
        delta_row_sign="down",
        delta_col_sign="right",
        delta_row_abs=3,
        delta_col_abs=4,
        clipping="none",
        blocked_destination=False,
        decoration_color=5,
    )


def _positions(grid, color):
    return {
        (row, column)
        for row, values in enumerate(grid)
        for column, value in enumerate(values)
        if value == color
    }


def test_rule_hash_and_canonical_inputs_are_synchronized():
    assert GEN.RULE_HASH == "0b37a0a27f79"
    for grid in _canonical_inputs():
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []


def test_every_declared_exact_axis_is_observable():
    cases = [
        {
            "grid_h": 8,
            "grid_w": 10,
            "blob_size": 3,
            "delta_row_sign": "down",
            "delta_col_sign": "left",
            "delta_row_abs": 2,
            "delta_col_abs": 2,
            "clipping": "none",
            "blocked_destination": False,
            "decoration_color": 8,
        },
        {
            "grid_h": 12,
            "grid_w": 14,
            "blob_size": 6,
            "delta_row_sign": "up",
            "delta_col_sign": "right",
            "delta_row_abs": 4,
            "delta_col_abs": 5,
            "clipping": "partial",
            "blocked_destination": True,
            "decoration_color": 9,
        },
    ]
    for index, overrides in enumerate(cases):
        grid = GEN.generate(1100 + index, index, difficulty="hard", **overrides)
        assert GEN.self_check(grid) == []
        observed = GEN.observe_overrides(grid)
        for name, expected in overrides.items():
            assert observed[name] == expected
        assert GEN.generate(1100 + index, index, difficulty="hard", **overrides) == grid


def test_unknown_and_rule_hiding_override_combinations_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis=3)
    with pytest.raises(ValueError, match="incompatible"):
        GEN.generate(0, 0, blocked_destination=True, decoration_color=8)


def test_default_schedule_covers_decisive_semantic_branches():
    observations = [GEN.observe_overrides(GEN.generate(77, index, difficulty="easy")) for index in range(4)]
    quadrants = {(row["delta_row_sign"], row["delta_col_sign"]) for row in observations}
    assert quadrants == {
        ("down", "right"),
        ("down", "left"),
        ("up", "right"),
        ("up", "left"),
    }
    assert {row["clipping"] for row in observations} == {"none", "partial"}
    assert {row["blocked_destination"] for row in observations} == {False, True}


def test_self_check_rejects_four_structural_impostors():
    base = _valid_grid()
    assert GEN.self_check(base) == []

    # 1. Missing endpoint: the vector is underdetermined.
    missing_yellow = copy.deepcopy(base)
    yr, yc = next(iter(_positions(missing_yellow, 4)))
    missing_yellow[yr][yc] = 0
    assert any("yellow" in reason for reason in GEN.self_check(missing_yellow))

    # 2. Same red count, but one cell is recombined into a disconnected island.
    disconnected = copy.deepcopy(base)
    red = sorted(_positions(disconnected, 2))
    disconnected[red[-1][0]][red[-1][1]] = 0
    occupied = _positions(disconnected, 2) | _positions(disconnected, 3) | _positions(disconnected, 4) | _positions(disconnected, 5)
    replacement = next(
        (r, c)
        for r in range(len(disconnected) - 1, -1, -1)
        for c in range(len(disconnected[0]) - 1, -1, -1)
        if (r, c) not in occupied
        and all(abs(r - rr) + abs(c - cc) > 1 for rr, cc in _positions(disconnected, 2))
    )
    disconnected[replacement[0]][replacement[1]] = 2
    assert any("connected" in reason for reason in GEN.self_check(disconnected))

    # 3. Negative recombination: inject a feature (9) absent everywhere else.
    mixed_decoration = copy.deepcopy(base)
    blank = next(
        (r, c)
        for r in range(len(base))
        for c in range(len(base[0]))
        if base[r][c] == 0
    )
    mixed_decoration[blank[0]][blank[1]] = 9
    assert any("one decoration color" in reason for reason in GEN.self_check(mixed_decoration))

    # 4. Hide the rule by blocking every otherwise eligible destination.
    no_effect = copy.deepcopy(base)
    dr, dc = GEN._marker_delta(no_effect)
    for r, c in _positions(no_effect, 2):
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(no_effect) and 0 <= nc < len(no_effect[0]):
            no_effect[nr][nc] = 5
    assert GEN.self_check(no_effect)
    assert any(
        "eligible" in reason or "blocked" in reason
        for reason in GEN.self_check(no_effect)
    )
