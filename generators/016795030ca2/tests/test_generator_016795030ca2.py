from __future__ import annotations

import importlib
import json
import random
from copy import deepcopy
from pathlib import Path

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.016795030ca2.generator")

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "016795030ca2"
BASE_PATH = ROOT / "data/base/solutions/training/22233c11__016795030ca2.json"


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


def _empty(h: int = 10, w: int = 10) -> list[list[int]]:
    return [[0 for _ in range(w)] for _ in range(h)]


def _fill(grid: list[list[int]], r: int, c: int, n: int, value: int = 3) -> None:
    for rr in range(r, r + n):
        for cc in range(c, c + n):
            grid[rr][cc] = value


def test_rule_pin_canonical_pairs_and_selected_source_are_exact():
    row = _canonical_row()
    assert gen.RULE_HASH == "9a16e24d93be"
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]

    target = json.loads(BASE_PATH.read_text(encoding="utf-8"))["racket_target"]
    assert target["target_code"] == row["program_solution"]
    assert target["raw_code"] != target["target_code"]  # archival executable source


def test_scheduled_lesson_covers_canonical_branches_and_is_identifiable():
    grids = [gen.generate(1701, index, difficulty="medium") for index in range(8)]
    observed = [gen.observe_overrides(grid) for grid in grids]
    assert [item["block_size"] for item in observed[:4]] == [1, 2, 1, 3]
    assert [item["n_motifs"] for item in observed[:4]] == [1, 1, 2, 1]
    assert [item["texture"] for item in observed[:4]] == [
        "plain",
        "clip_edge",
        "plain",
        "plain",
    ]
    for grid in grids:
        assert gen.self_check(grid) == []

    for name, witness in gen.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), name

    lessons = [
        {"input": grid, "output": gen.rule_mirror(grid)}
        for grid in grids[:4]
    ]
    assert gen.lesson_identifiable(lessons[:3], lessons[3]) == []


def test_override_boundaries_are_exact_observable_and_band_safe():
    cases = {
        "grid_h": (9, 16),
        "grid_w": (9, 16),
        "block_size": (1, 3),
        "n_motifs": (1, 2),
        "texture": ("plain", "clip_edge"),
    }
    for difficulty in ("easy", "medium", "hard"):
        for axis, values in cases.items():
            for value in values:
                for seed in (0, 7, 29):
                    grid = gen.generate(seed, seed + 3, difficulty=difficulty, **{axis: value})
                    assert gen.self_check(grid) == []
                    observed = gen.observe_overrides(grid)
                    assert observed[axis] == value

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, bogus_axis=3)


def test_replay_is_fresh_deterministic_global_rng_pure_and_band_live():
    random.seed(20260725)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert first != second

    by_band = {
        band: gen.generate(991, 17, difficulty=band)
        for band in ("easy", "medium", "hard")
    }
    assert len({repr(grid) for grid in by_band.values()}) >= 2


def test_mutation_impostors_and_degenerate_textures_are_rejected():
    valid = gen.generate(9, 6, difficulty="medium", block_size=2, texture="plain")
    analysis = gen._analyze_grid(valid)
    assert analysis["errors"] == []

    removed_cell = deepcopy(valid)
    r, c = sorted(analysis["motifs"][0]["source"])[0]
    removed_cell[r][c] = 0

    adjacent_quadrants = _empty()
    _fill(adjacent_quadrants, 3, 2, 2)
    _fill(adjacent_quadrants, 3, 4, 2)

    mixed_sizes = _empty(16, 16)
    _fill(mixed_sizes, 3, 3, 1)
    _fill(mixed_sizes, 4, 4, 1)
    _fill(mixed_sizes, 9, 9, 2)
    _fill(mixed_sizes, 11, 11, 2)

    fully_clipped_endpoint = _empty(9, 9)
    fully_clipped_endpoint[0][3] = 3
    fully_clipped_endpoint[1][4] = 3

    fixtures = {
        "removed_source_cell": removed_cell,
        "adjacent_not_opposite_quadrants": adjacent_quadrants,
        "mixed_block_sizes": mixed_sizes,
        "fully_clipped_endpoint": fully_clipped_endpoint,
    }
    for name, grid in fixtures.items():
        assert gen.self_check(grid), name

    for texture in gen.DEGENERATE_TEXTURES:
        grid = gen.generate(7, 9, difficulty="medium", texture=texture)
        assert gen.self_check(grid), texture
