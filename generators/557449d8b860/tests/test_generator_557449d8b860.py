from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

MODULE_PATH = REPO_ROOT / "generators" / "557449d8b860" / "generator.py"
SPEC = importlib.util.spec_from_file_location("review_generator_557449d8b860", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_inputs() -> list[list[list[int]]]:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return [
                    copy.deepcopy(pair["input"])
                    for split in ("train", "test")
                    for pair in row[split]
                ]
    raise AssertionError(f"canonical task {GEN.TASK_ID} not found")


def _gravity_down(grid: list[list[int]]) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    out = [[0] * width for _ in range(height)]
    for col in range(width):
        values = [grid[row][col] for row in range(height) if grid[row][col] != 0]
        for offset, value in enumerate(values):
            out[height - len(values) + offset][col] = value
    return out


def test_declares_authority_and_accepts_every_canonical_input():
    assert GEN.RULE_HASH == "c3638032481f"
    for grid in _canonical_inputs():
        assert GEN.self_check(copy.deepcopy(grid)) == []
        assert GEN.strict_canonical_like(copy.deepcopy(grid)) == []


def test_exact_override_contract_is_observable_in_every_band():
    cases = (
        {
            "grid_h": 6,
            "grid_w": 6,
            "n_cells": 5,
            "n_occupied_columns": 2,
            "palette_size": 2,
        },
        {
            "grid_h": 10,
            "grid_w": 10,
            "n_cells": 10,
            "n_occupied_columns": 4,
            "palette_size": 5,
        },
        {
            "grid_h": 6,
            "grid_w": 10,
            "n_cells": 10,
            "n_occupied_columns": 2,
            "palette_size": 5,
        },
    )
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = GEN.generate(91 + index, 17 + index, difficulty=band, **overrides)
            assert GEN.self_check(grid, difficulty=band) == []
            observed = GEN.observe_overrides(grid)
            assert {axis: observed[axis] for axis in overrides} == overrides

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, typo_axis=3)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, grid_h=5)
    with pytest.raises(ValueError):
        GEN.generate(1, 2, palette_size=6)


def test_distribution_is_lawful_canonical_anchored_and_branch_covering():
    for band in ("easy", "medium", "hard"):
        strict_hits = 0
        witness_hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        shapes: set[tuple[int, int]] = set()
        observed_counts: set[int] = set()
        for seed in range(180):
            grid = GEN.generate(seed, seed * 11 + 5, difficulty=band)
            assert GEN.self_check(grid, difficulty=band) == []
            assert _gravity_down(grid) != grid
            strict_hits += not GEN.strict_canonical_like(grid)
            shapes.add((len(grid), len(grid[0])))
            observed_counts.add(sum(value != 0 for row in grid for value in row))
            for name, witness in GEN.SEMANTIC_WITNESSES.items():
                witness_hits[name] += bool(witness(grid))

        assert strict_hits >= 45, (band, strict_hits)
        assert len(shapes) >= 8, (band, shapes)
        assert len(observed_counts) >= 5, (band, observed_counts)
        assert all(count >= 5 for count in witness_hits.values()), (band, witness_hits)


def test_self_check_rejects_rule_hiding_and_malformed_scenes():
    base = GEN.generate(
        22,
        9,
        grid_h=6,
        grid_w=6,
        n_cells=6,
        n_occupied_columns=3,
        palette_size=4,
    )
    blank = [[0] * 6 for _ in range(6)]
    identity_only = _gravity_down(base)
    one_column = [[0] * 6 for _ in range(6)]
    one_column[0][2], one_column[2][2], one_column[4][2] = 1, 2, 3
    monochrome = copy.deepcopy(base)
    for row in range(len(monochrome)):
        for col in range(len(monochrome[0])):
            if monochrome[row][col]:
                monochrome[row][col] = 7
    ragged = copy.deepcopy(base)
    ragged[-1].pop()
    illegal_cell = copy.deepcopy(base)
    illegal_cell[0][0] = 11

    for impostor in (blank, identity_only, one_column, monochrome, ragged, illegal_cell):
        assert GEN.self_check(impostor), impostor


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(90210)
    state = random.getstate()
    first = GEN.generate(23, 11, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(23, 11, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0
    assert GEN.generate(23, 11, difficulty="medium") == second


def test_named_witnesses_really_refute_their_named_rivals():
    grids = [
        GEN.generate(seed, seed * 13 + 1, difficulty=band)
        for band in ("easy", "medium", "hard")
        for seed in range(240)
    ]
    for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
        witnesses = [grid for grid in grids if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert witnesses, witness_name
        for rival_name in rival_names:
            rival = GEN.SEMANTIC_RIVALS[rival_name]
            assert any(rival(grid) != _gravity_down(grid) for grid in witnesses), (
                witness_name,
                rival_name,
            )

    for shortcut_name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(grid) == _gravity_down(grid) for grid in _canonical_inputs())
        assert any(shortcut(grid) != _gravity_down(grid) for grid in grids), shortcut_name
