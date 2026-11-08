from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random

import pytest

from puzzle_generators import runner
from scripts.canonical_profile_gate import canonical_pairs

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.1569ecfa4ff1.generator"
)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_pinned() -> None:
    canonical = next(
        json.loads(line)
        for line in (runner.ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == GEN.TASK_ID
    )
    normalized = " ".join(canonical["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH

    pairs = canonical_pairs(GEN.TASK_ID)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_every_declared_override_is_exact_and_unknown_keys_reject() -> None:
    for profile in GEN.GRID_PROFILES:
        for region in GEN.PIVOT_REGIONS:
            for n_cells in (3, 4):
                for color in GEN.FOREGROUND_COLORS:
                    grid = GEN.generate(
                        991,
                        17,
                        difficulty="hard",
                        grid_profile=profile,
                        pivot_region=region,
                        n_cells=n_cells,
                        foreground_color=color,
                    )
                    assert GEN.self_check(grid) == []
                    assert GEN.observe_overrides(grid) == {
                        "grid_profile": profile,
                        "pivot_region": region,
                        "n_cells": n_cells,
                        "foreground_color": color,
                    }
    with pytest.raises(TypeError):
        GEN.generate(0, 0, unknown_axis="typo")


def test_generation_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(81173)
    before = random.getstate()
    first = GEN.generate(13, 29, difficulty="medium")
    after = random.getstate()
    assert before == after

    pristine = copy.deepcopy(first)
    first[0][0] = 9
    second = GEN.generate(13, 29, difficulty="medium")
    assert second == pristine
    assert second is not first
    assert all(a is not b for a, b in zip(second, first))


def test_self_check_rejects_targeted_impostors() -> None:
    valid = GEN.generate(77, 6, grid_profile="7x7", pivot_region="center")
    assert GEN.self_check(valid) == []

    impostors = {}
    impostors["all_background"] = [[0] * 7 for _ in range(7)]

    no_pivot = copy.deepcopy(valid)
    for row in no_pivot:
        for col, value in enumerate(row):
            if value == 8:
                row[col] = 0
    impostors["no_pivot"] = no_pivot

    multiple_pivots = copy.deepcopy(valid)
    multiple_pivots[0][0] = 8
    impostors["multiple_pivots"] = multiple_pivots

    two_colors = copy.deepcopy(valid)
    foreground = [
        (r, c)
        for r, row in enumerate(two_colors)
        for c, value in enumerate(row)
        if value not in (0, 8)
    ]
    r, c = foreground[0]
    two_colors[r][c] = 9 if two_colors[r][c] != 9 else 7
    impostors["two_foreground_colors"] = two_colors

    collinear = [[0] * 7 for _ in range(7)]
    collinear[3][3] = 8
    collinear[3][0] = collinear[3][1] = collinear[3][2] = 4
    impostors["collinear_shortcut"] = collinear

    rotational_identity = [[0] * 7 for _ in range(7)]
    rotational_identity[3][3] = 8
    for r, c in ((2, 3), (3, 2), (3, 4), (4, 3)):
        rotational_identity[r][c] = 4
    impostors["rotational_identity"] = rotational_identity

    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_named_rivals_are_killed_by_every_two_demo_window() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(24):
            grids = [
                GEN.generate(seed, start + offset, difficulty=difficulty)
                for start in range(8)
                for offset in range(3)
            ]
            assert all(GEN.self_check(grid) == [] for grid in grids)

        for seed in range(16):
            for start in range(16):
                demos = [
                    _pair(GEN.generate(seed, start + offset, difficulty=difficulty))
                    for offset in range(GEN.EXAMPLES_NEEDED)
                ]
                query = _pair(
                    GEN.generate(
                        seed,
                        start + GEN.EXAMPLES_NEEDED,
                        difficulty=difficulty,
                    )
                )
                assert GEN.lesson_identifiable(demos, query) == []


def test_semantic_witnesses_have_positive_support_in_each_band() -> None:
    for difficulty in ("easy", "medium", "hard"):
        counts = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
        for seed in range(80):
            grid = GEN.generate(10000 + seed, seed, difficulty=difficulty)
            for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                counts[name] += bool(predicate(grid))
        assert all(count > 0 for count in counts.values()), counts
