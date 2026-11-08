from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "e3be2a9d8ce2"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]


def _canonical_inputs() -> list[list[list[int]]]:
    inputs: list[list[list[int]]] = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            inputs.extend(pair["input"] for pair in row.get("train", []))
            inputs.extend(pair["input"] for pair in row.get("test", []))
    return inputs


def test_canonical_inputs_and_single_pixel_are_lawful() -> None:
    canonical = _canonical_inputs()
    assert len(canonical) == 10
    assert all(MODULE.self_check(grid) == [] for grid in canonical)

    single = [[0] * 9 for _ in range(9)]
    single[4][4] = 7
    assert MODULE.self_check(single) == []


def test_boundary_overrides_are_exact_in_every_band() -> None:
    for difficulty in ("easy", "medium", "hard"):
        grid = MODULE.generate(
            17,
            11,
            difficulty=difficulty,
            grid_h=22,
            grid_w=8,
            n_pixels=8,
            palette_size=6,
            palette_kind="cool",
        )
        assert MODULE.observe_overrides(grid) == {
            "grid_h": 22,
            "grid_w": 8,
            "n_pixels": 8,
            "palette_size": 6,
        }
        assert MODULE.self_check(
            grid,
            difficulty=difficulty,
            meta={
                "overrides": {
                    "grid_h": 22,
                    "grid_w": 8,
                    "n_pixels": 8,
                    "palette_size": 6,
                }
            },
        ) == []


def test_incompatible_palette_count_rejects_loudly() -> None:
    with pytest.raises(ValueError, match="palette_size cannot exceed n_pixels"):
        MODULE.generate(3, 2, n_pixels=1, palette_size=6)


def test_generation_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(90210)
    state = random.getstate()
    first = MODULE.generate(23, 19, difficulty="hard")
    assert random.getstate() == state
    second = MODULE.generate(23, 19, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second, strict=True))

    mutated = copy.deepcopy(first)
    mutated[0][0] = 9
    assert MODULE.generate(23, 19, difficulty="hard") == second


def test_self_check_rejects_four_structural_impostors() -> None:
    empty = [[0] * 9 for _ in range(9)]
    assert any("1..8" in error for error in MODULE.self_check(empty))

    border = [[0] * 9 for _ in range(9)]
    border[0][4] = 3
    assert any("strictly interior" in error for error in MODULE.self_check(border))

    adjacent = [[0] * 9 for _ in range(9)]
    adjacent[2][2] = 3
    adjacent[2][3] = 8
    assert any("orthogonally adjacent" in error for error in MODULE.self_check(adjacent))

    crossing = [[0] * 10 for _ in range(10)]
    crossing[2][4] = 3
    crossing[4][2] = 8
    assert any("pairwise disjoint" in error for error in MODULE.self_check(crossing))


def test_generated_ray_footprints_are_disjoint_and_cover_all_directions() -> None:
    seen = set()
    ties = {"vertical": 0, "horizontal": 0}
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(70):
            grid = MODULE.generate(seed, seed, difficulty=difficulty)
            assert MODULE.self_check(grid) == []
            height, width = len(grid), len(grid[0])
            emitters = [
                (row, col)
                for row, values in enumerate(grid)
                for col, value in enumerate(values)
                if value
            ]
            footprints = [
                MODULE._ray_cells(height, width, row, col)
                for row, col in emitters
            ]
            for index, footprint in enumerate(footprints):
                assert all(
                    not footprint & other
                    for other in footprints[index + 1 :]
                )
            for row, col in emitters:
                seen.add(MODULE._direction_tag(height, width, row, col))
                ties["vertical"] += int(2 * row == height - 1)
                ties["horizontal"] += int(2 * col == width - 1)

    assert seen == {"TL", "TR", "BL", "BR"}
    assert ties["vertical"] > 0
    assert ties["horizontal"] > 0


def test_rule_hash_matches_canonical_program() -> None:
    canonical = set()
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                canonical.add(row["program_solution"])
    assert len(canonical) == 1
    import hashlib

    expected = hashlib.sha256(next(iter(canonical)).encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == expected == "116a1aaf2218"
