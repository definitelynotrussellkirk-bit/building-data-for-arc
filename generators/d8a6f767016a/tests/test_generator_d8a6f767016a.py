from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "d8a6f767016a"
ROOT = find_root(__file__)
GEN_PATH = Path("puzzle_generators/per_puzzle") / TASK_ID / "generator.py"
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _canonical_rule_hash() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return hashlib.sha256(" ".join(row["program_solution"].split()).encode()).hexdigest()[:12]
    raise AssertionError("canonical rule not found")


def _load():
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", GEN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ring(height: int, width: int) -> list[list[int]]:
    return [
        [8 if r in (0, height - 1) or c in (0, width - 1) else 0
         for c in range(width)]
        for r in range(height)
    ]


def test_rule_hash_and_all_canonical_pairs_match_python_mirror():
    gen = _load()
    assert gen.RULE_HASH == _canonical_rule_hash()
    pairs = PAIRS
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        before = copy.deepcopy(pair["input"])
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_unknown_override_rejects_and_dimensions_round_trip():
    gen = _load()
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(3, 0, typo_axis=1)
    for band in ("easy", "medium", "hard"):
        grid = gen.generate(7, 2, difficulty=band, grid_h=12, grid_w=15)
        assert (len(grid), len(grid[0])) == (12, 15)
        assert gen.observe_overrides(grid) == {"grid_h": 12, "grid_w": 15}
        assert gen.self_check(grid) == []


def test_self_check_rejects_minimal_impostors():
    gen = _load()
    assert gen.self_check([[0] * 11 for _ in range(9)])
    assert gen.self_check([[8] * 11 for _ in range(9)])
    one_small_ring = [[0] * 11 for _ in range(9)]
    ring = _ring(3, 3)
    for r, row in enumerate(ring):
        for c, value in enumerate(row):
            one_small_ring[r][c] = value
    assert gen.self_check(one_small_ring)


def test_component_size_shortcut_fits_training_demos_but_not_large_one_hole_ring():
    gen = _load()
    train_pairs = [pair for pair in PAIRS if pair["split"] == "train"]
    assert len(train_pairs) == 4
    assert all(gen._rival_canonical_size_bins(pair["input"]) == pair["output"]
               for pair in train_pairs)

    grid = [[0] * 7 for _ in range(7)]
    for r, row in enumerate(_ring(5, 5), start=1):
        for c, value in enumerate(row, start=1):
            grid[r][c] = value
    intended = gen.rule_mirror(grid)
    rival = gen._rival_canonical_size_bins(grid)
    assert intended != rival
    assert {intended[r][c] for r in range(1, 6) for c in range(1, 6) if grid[r][c] == 8} == {1}
    assert {rival[r][c] for r in range(1, 6) for c in range(1, 6) if grid[r][c] == 8} == {3}


def test_every_default_draw_contains_a_size_shortcut_counterexample():
    gen = _load()
    for band in ("easy", "medium", "hard"):
        for index in range(24):
            grid = gen.generate(10_000 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen._witness_size_shortcut_counterexample(grid)
            assert gen._rival_canonical_size_bins(grid) != gen.rule_mirror(grid)


def test_every_four_demo_cyclic_start_identifies_the_declared_rival():
    gen = _load()
    for band in ("easy", "medium", "hard"):
        pairs = []
        for index in range(12):
            inp = gen.generate(20_000 + index, index, difficulty=band)
            pairs.append({"input": inp, "output": gen.rule_mirror(inp)})
        for start in range(8):
            demos = pairs[start:start + gen.EXAMPLES_NEEDED]
            query = pairs[start + gen.EXAMPLES_NEEDED]
            assert gen.lesson_identifiable(demos, query) == []


def test_schedule_covers_mapping_and_else_branch_in_each_four_sample_window():
    gen = _load()
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            profiles = [gen.schedule_profile(0, index, band) for index in range(start, start + 4)]
            assert set(profiles) == set(gen.SCHEDULE_PROFILES)
            realized = []
            for index in range(start, start + 4):
                grid = gen.generate(30_000 + index, index, difficulty=band)
                realized.extend(gen._count_holes(cells) for cells in gen._objects4(grid))
            assert {1, 2, 3, 4, 0}.issubset(set(realized))


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    gen = _load()
    random.seed(778899)
    state_before = random.getstate()
    first = gen.generate(1234, 2, difficulty="hard")
    state_after = random.getstate()
    second = gen.generate(1234, 2, difficulty="hard")
    assert state_after == state_before
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(1234, 2, difficulty="hard")


def test_small_canvas_count4_orientation_regression():
    gen = _load()
    # Override-contract minimized witness: sample_index 27*17+3 has phase count_4.
    grid = gen.generate(27, 27 * 17 + 3, difficulty="easy", grid_h=9, grid_w=11)
    assert (len(grid), len(grid[0])) == (9, 11)
    assert gen.self_check(grid) == []
    assert gen._witness_size_shortcut_counterexample(grid)
