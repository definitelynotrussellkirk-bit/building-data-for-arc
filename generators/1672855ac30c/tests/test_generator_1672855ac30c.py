from __future__ import annotations

import importlib
import json
import random
from pathlib import Path

gen = importlib.import_module("puzzle_generators.per_puzzle.1672855ac30c.generator")


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "1672855ac30c"
EXPECTED_ORDER = [("BR", "TL", "TR", "BL")]


def _canonical_rows():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    return rows


def test_canonical_inputs_are_owned_and_selected_sources_are_synced():
    rows = _canonical_rows()
    assert len(rows) == 2
    canonical_rule = rows[0]["program_solution"]
    assert all(row["program_solution"] == canonical_rule for row in rows)
    pairs = [
        pair
        for row in rows
        for split in ("train", "test")
        for pair in row.get(split, [])
    ]
    assert len(pairs) == 14
    assert all(gen.self_check(pair["input"]) == [] for pair in pairs)

    base_paths = [
        ROOT / "data/base/solutions/training/e99362f0__1672855ac30c.json",
        ROOT / "data/base/solutions/augmented/e99362f0__ae42faa675a9.json",
    ]
    for path in base_paths:
        target = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code"] == canonical_rule
        assert target["raw_code"] != canonical_rule  # preserved archival source


def test_every_ordinary_draw_uniquely_identifies_the_priority_order():
    for band in ("easy", "medium", "hard"):
        for seed in range(30):
            grid = gen.generate(seed, seed * 13 + 5, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.matching_priority_orders(grid) == EXPECTED_ORDER
            analysis = gen._analyze(grid)
            counts = analysis["facts"]["branch_counts"]
            assert counts["br_priority"] >= 1
            assert counts["tl_priority"] >= 1
            assert counts["tr_priority"] >= 1
            assert counts["bl_fallback"] >= 1


def test_dimension_override_boundaries_are_exact_and_observable():
    for qh in (3, 9):
        for qw in (3, 9):
            grid = gen.generate(
                22,
                11,
                difficulty="easy",
                quadrant_h=qh,
                quadrant_w=qw,
                palette_kind="canonical",
                quadrant_density=0.08,
                position_bias="edges",
            )
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == {"quadrant_h": qh, "quadrant_w": qw}
            assert len(grid) == 2 * qh + 1
            assert len(grid[0]) == 2 * qw + 1


def test_mutation_fixtures_and_degenerate_textures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name
    for texture in gen.DEGENERATE_TEXTURES:
        grid = gen.generate(7, 9, difficulty="medium", texture=texture)
        assert gen.self_check(grid), texture


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20260724)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second
