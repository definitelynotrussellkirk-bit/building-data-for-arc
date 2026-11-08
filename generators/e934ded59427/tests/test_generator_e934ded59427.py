"""Focused semantic and regression tests for generator e934ded59427."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from scripts.rule_smoke import purity_body, rule_application
from puzzle_generators.per_puzzle.e934ded59427 import generator as gen

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/base/solutions/banks/f4425e302da7/medium_l13__e934ded59427.json"


def canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    return [*row["train"], *row["test"]]


def normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def profile(grid: list[list[int]]) -> dict:
    by_color = gen._by_color(grid)
    boxes = []
    diagonals = set()
    thin_h = thin_w = square = edge = interior = 0
    for cells in by_color.values():
        (ra, ca), (rb, cb) = cells
        r0, c0, r1, c1 = gen._bbox(cells)
        rh, rw = r1 - r0 + 1, c1 - c0 + 1
        boxes.append((r0, c0, r1, c1))
        diagonals.add("main" if (ra - rb) * (ca - cb) > 0 else "anti")
        thin_h += rh == 2
        thin_w += rw == 2
        square += rh == rw
        edge += r0 == 0 or c0 == 0 or r1 == len(grid) - 1 or c1 == len(grid[0]) - 1
        interior += r0 > 0 and c0 > 0 and r1 < len(grid) - 1 and c1 < len(grid[0]) - 1
    return {
        **gen.observe_overrides(grid),
        "boxes": boxes,
        "diagonals": diagonals,
        "thin_h": thin_h,
        "thin_w": thin_w,
        "square": square,
        "edge": edge,
        "interior": interior,
    }


def test_rule_hash_authority_and_canonical_pairs() -> None:
    row = canonical_row()
    source = row["program_solution"]
    assert gen.RULE_HASH == normalized_hash(source) == "fd190ef6787c"
    base = json.loads(BASE.read_text(encoding="utf-8"))
    target = base["racket_target"]
    assert target["raw_code"] == source
    assert target["target_code"] == source
    assert target["rule_hash"] == gen.RULE_HASH

    pairs = canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_canonical_racket_exact_input_pure_and_a_b_a() -> None:
    source = canonical_row()["program_solution"]
    pairs = canonical_pairs()
    bridge = RacketBridge(max_calls_before_restart=128)
    try:
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            assert bridge.eval_text(rule_application(source, pair["input"])) == pair["output"]
            assert pair["input"] == before
        probe = bridge.eval_text(purity_body(source, pairs[0]["input"], pairs[1]["input"]))
        assert probe[0] == pairs[0]["output"]
        assert probe[1] == pairs[0]["output"]
        assert probe[2] == pairs[0]["input"]
    finally:
        bridge.shutdown()


def test_determinism_fresh_returns_rng_purity_and_hashseed_safe_inputs() -> None:
    random.seed(93459427)
    before = random.getstate()
    first = gen.generate(71, 19, difficulty="hard")
    assert random.getstate() == before
    second = gen.generate(71, 19, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert gen.generate(71, 19, difficulty="hard") == second
    assert gen.generate(72, 19, difficulty="hard") != second
    assert gen.generate(71, 20, difficulty="hard") != second


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_override_boundaries_in_every_band(difficulty: str) -> None:
    index = 0
    for h in (6, 20):
        for w in (7, 20):
            for n_pairs in (2, 5):
                for texture in gen.HELPFUL_TEXTURES:
                    grid = gen.generate(
                        1000 + index,
                        17,
                        difficulty=difficulty,
                        grid_h=h,
                        grid_w=w,
                        n_pairs=n_pairs,
                        texture=texture,
                    )
                    assert gen.self_check(grid, difficulty=difficulty) == []
                    assert gen.observe_overrides(grid) == {
                        "grid_h": h,
                        "grid_w": w,
                        "n_pairs": n_pairs,
                        "texture": texture,
                    }
                    index += 1


def test_strict_linked_semantic_census_200_per_band() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        seen_inputs = set()
        seen_outputs = set()
        textures = set()
        pair_counts = set()
        diagonals = set()
        thin_h = thin_w = square = edge = interior = 0
        for offset in range(200):
            seed = 20_000 + band_index * 10_000 + offset
            grid = gen.generate(seed, offset, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            out = gen.rule_mirror(grid)
            assert out != grid
            obs = profile(grid)
            textures.add(obs["texture"])
            pair_counts.add(obs["n_pairs"])
            diagonals |= obs["diagonals"]
            thin_h += obs["thin_h"]
            thin_w += obs["thin_w"]
            square += obs["square"]
            edge += obs["edge"]
            interior += obs["interior"]
            seen_inputs.add(json.dumps(grid, separators=(",", ":")))
            seen_outputs.add(json.dumps(out, separators=(",", ":")))
        assert len(seen_inputs) == 200
        assert len(seen_outputs) == 200
        assert textures == set(gen.HELPFUL_TEXTURES)
        assert diagonals == {"main", "anti"}
        assert thin_h > 0 and thin_w > 0 and square > 0
        assert edge > 0 and interior > 0
        assert pair_counts == ({2} if band == "easy" else ({2, 3} if band == "medium" else {3, 4, 5}))


def test_every_three_demo_window_contains_a_hollow_rule_witness() -> None:
    lessons = 200
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for offset in range(lessons):
            seed = 40_000 + band_index * 10_000 + offset
            for start in range(4):
                demos = [gen.generate(seed, start + index, difficulty=band) for index in range(3)]
                query = gen.generate(seed, start + 3, difficulty=band)
                assert all(gen.self_check(grid) == [] and gen.rule_mirror(grid) != grid for grid in [*demos, query])
                assert any(
                    any(
                        (r1 - r0 + 1) >= 3 and (c1 - c0 + 1) >= 3
                        for cells in gen._by_color(grid).values()
                        for r0, c0, r1, c1 in [gen._bbox(cells)]
                    )
                    for grid in demos
                )


def test_self_check_rejects_regression_witnesses_and_targeted_mutations() -> None:
    lawful = gen.generate(888, 9, difficulty="medium", n_pairs=3, texture="default")

    for texture in gen.DEGENERATE_TEXTURES:
        bad = gen.generate(1, 1, texture=texture)
        assert gen.self_check(bad), texture

    lost_corner = copy.deepcopy(lawful)
    r, c = next((r, c) for r, row in enumerate(lost_corner) for c, v in enumerate(row) if v != 0)
    lost_corner[r][c] = 0
    assert any("expected exactly 2" in err for err in gen.self_check(lost_corner))

    extra_anchor = copy.deepcopy(lawful)
    used = set(gen._by_color(extra_anchor))
    foreign_anchor = next(color for color in gen._TEXTURE_ANCHOR.values() if color not in used)
    r, c = next((r, c) for r, row in enumerate(extra_anchor) for c, v in enumerate(row) if v == 0)
    extra_anchor[r][c] = foreign_anchor
    assert gen.self_check(extra_anchor)

    with pytest.raises(TypeError, match="unsupported override"):
        gen.generate(1, 1, palette_kind="warm")
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 1, difficulty="extreme")
