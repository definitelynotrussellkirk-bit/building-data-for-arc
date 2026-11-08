"""Focused regression coverage for Motif Recolor Broadcast (18e652e005b1)."""
from __future__ import annotations

import copy
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "18e652e005b1"
ROOT = find_root(__file__)
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _rows(grid):
    return [
        [int(ch) for ch in row] if isinstance(row, str) else list(row)
        for row in grid
    ]


def _canonical_inputs():
    """Load canonical pairs through the staged-runtime portable support API."""
    return [
        _rows(pair["input"])
        for pair in canonical_pairs(TASK_ID, root=ROOT)
        if isinstance(pair, dict) and pair.get("input")
    ]


def _signature(grid):
    g = _rows(grid)
    h, w = len(g), len(g[0])
    cells = [
        (r, c)
        for r in range(h - 1)
        for c in range(w - 1)
        if g[r][c] != 0
    ]
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    motif = tuple(sorted((r - r0, c - c0) for r, c in cells))
    commands = tuple(v for v in g[-1] if v != 0)
    return h, w, len(commands), motif


def _valid_grid(seed=11, sample_index=7, difficulty="medium"):
    return GEN.generate(seed, sample_index, difficulty=difficulty)


def _derived_output_shape(grid):
    g = _rows(grid)
    motif = [
        (r, c)
        for r in range(len(g) - 1)
        for c in range(len(g[0]) - 1)
        if g[r][c] != 0
    ]
    motif_h = max(r for r, _ in motif) - min(r for r, _ in motif) + 1
    motif_w = max(c for _, c in motif) - min(c for _, c in motif) + 1
    commands = sum(value != 0 for value in g[-1])
    return motif_h, commands * motif_w + commands - 1


def test_canonical_scene_bank_matches_all_train_and_test_inputs():
    expected = Counter(_signature(grid) for grid in _canonical_inputs())
    assert expected == Counter(GEN.CANONICAL_SCENES)


def test_self_check_accepts_every_canonical_input():
    canonical = _canonical_inputs()
    assert len(canonical) == 5
    assert [GEN.self_check(copy.deepcopy(grid)) for grid in canonical] == [
        [], [], [], [], []
    ]


def test_regression_rule_excluded_final_column_is_always_blank():
    for band in ("easy", "medium", "hard"):
        for seed in range(80):
            grid = GEN.generate(seed, seed * 17 + 3, difficulty=band)
            assert all(row[-1] == 0 for row in grid)
            assert not GEN.self_check(grid)


def test_declared_override_boundaries_are_exact_and_observable():
    cases = (
        {"grid_h": 6, "grid_w": 8, "commands": 2, "motif_cells": 3,
         "motif_connectivity": "connected"},
        {"grid_h": 14, "grid_w": 16, "commands": 6, "motif_cells": 10,
         "motif_connectivity": "disconnected"},
    )
    for band in ("easy", "medium", "hard"):
        for index, case in enumerate(cases):
            grid = GEN.generate(900 + index, 40 + index, difficulty=band, **case)
            observed = GEN.observe_overrides(grid)
            assert {key: observed[key] for key in case} == case
            assert not GEN.self_check(grid)


def test_deterministic_fresh_returns_and_global_rng_is_untouched():
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(77, 19, difficulty="hard")
    middle = GEN.generate(78, 20, difficulty="easy")
    second = GEN.generate(77, 19, difficulty="hard")
    after = random.getstate()

    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    assert middle != first

    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(77, 19, difficulty="hard") == second


def test_self_check_rejects_targeted_impostors():
    base = _valid_grid()

    no_motif = copy.deepcopy(base)
    for r in range(len(no_motif) - 1):
        for c in range(len(no_motif[0]) - 1):
            no_motif[r][c] = 0

    mixed_motif = copy.deepcopy(base)
    motif = [
        (r, c)
        for r in range(len(base) - 1)
        for c in range(len(base[0]) - 1)
        if base[r][c]
    ]
    r, c = motif[0]
    mixed_motif[r][c] = next(
        color for color in range(1, 10) if color != base[r][c]
    )

    gapped_commands = copy.deepcopy(base)
    commands = [c for c, value in enumerate(base[-1]) if value]
    gapped_commands[-1][len(commands)] = gapped_commands[-1][1]
    gapped_commands[-1][1] = 0

    duplicate_commands = copy.deepcopy(base)
    duplicate_commands[-1][1] = duplicate_commands[-1][0]

    occupied_final_column = copy.deepcopy(base)
    occupied_final_column[0][-1] = 9

    motif_command_collision = copy.deepcopy(base)
    motif_color = base[motif[0][0]][motif[0][1]]
    motif_command_collision[-1][0] = motif_color

    oversized_output = [[0 for _ in range(16)] for _ in range(6)]
    oversized_output[0][0] = oversized_output[0][7] = oversized_output[0][14] = 4
    oversized_output[-1][0:2] = [2, 6]

    impostors = {
        "no_motif": no_motif,
        "mixed_motif": mixed_motif,
        "gapped_commands": gapped_commands,
        "duplicate_commands": duplicate_commands,
        "occupied_final_column": occupied_final_column,
        "motif_command_collision": motif_command_collision,
        "oversized_output": oversized_output,
    }
    findings = {name: GEN.self_check(grid) for name, grid in impostors.items()}
    assert all(findings.values()), findings


def test_strict_canonical_manifold_floor_in_two_disjoint_censuses():
    canonical = set(GEN.CANONICAL_SCENES)
    for seed_start in (10_000, 20_000):
        for band in ("easy", "medium", "hard"):
            matches = 0
            signatures = set()
            for offset in range(200):
                seed = seed_start + offset
                grid = GEN.generate(seed, offset * 29 + 5, difficulty=band)
                signature = _signature(grid)
                signatures.add(signature)
                matches += signature in canonical
            assert matches >= 10, (seed_start, band, matches)
            assert len(signatures) >= 50, (seed_start, band, len(signatures))


def test_three_demo_schedule_identifies_command_count_and_connectivity_branches():
    for seed in range(30):
        for start in range(3):
            observed = [
                GEN.observe_overrides(
                    GEN.generate(seed, start + offset, difficulty="medium")
                )
                for offset in range(3)
            ]
            assert {row["commands"] for row in observed} == {2, 3, 4}
            assert {row["motif_connectivity"] for row in observed} == {
                "connected", "disconnected"
            }


def test_all_generated_and_boundary_outputs_fit_arc_30x30():
    for band in ("easy", "medium", "hard"):
        for seed in range(200):
            grid = GEN.generate(30_000 + seed, seed * 31 + 7, difficulty=band)
            assert max(_derived_output_shape(grid)) <= 30
            assert not GEN.self_check(grid)

    for connectivity in ("connected", "disconnected"):
        grid = GEN.generate(
            44_000,
            13,
            difficulty="hard",
            grid_h=14,
            grid_w=16,
            commands=6,
            motif_cells=10,
            motif_connectivity=connectivity,
        )
        assert _derived_output_shape(grid)[1] <= 30
        assert not GEN.self_check(grid)
