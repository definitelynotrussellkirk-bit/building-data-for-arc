"""Focused regressions for the nearest-border ray curriculum."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from puzzle_generators import base as generator_base
gen = importlib.import_module("puzzle_generators.per_puzzle.126da449328f.generator")


def _canonical_row():
    path = REPO_ROOT / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def test_rule_hash_and_all_canonical_pairs_include_priority_tie():
    row = _canonical_row()
    actual_hash = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == actual_hash

    pairs = list(row["train"]) + list(row["test"])
    assert len(pairs) == 4
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == pair["output"]

    tied = row["train"][2]["input"]
    facts = gen._analyze(tied)
    seed = next(seed for seed in facts["seeds"] if seed["position"] == (1, 7))
    assert seed["nearest_sides"] == ("top", "right")
    assert seed["chosen_side"] == "top"


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h", [7, 9])
@pytest.mark.parametrize("grid_w", [7, 9])
@pytest.mark.parametrize("seed_count", [3, 4])
def test_all_exact_axis_boundaries_are_observable(band, grid_h, grid_w, seed_count):
    grid = gen.generate(
        1031,
        77,
        difficulty=band,
        grid_h=grid_h,
        grid_w=grid_w,
        seed_count=seed_count,
    )
    assert gen.self_check(grid, difficulty=band) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "seed_count": seed_count,
    }


def test_unknown_and_invalid_calls_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_h=6)


def test_every_six_demo_window_identifies_priority_and_all_directions():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(8801, start + offset, difficulty=band)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(8801, start + gen.EXAMPLES_NEEDED, difficulty=band)
            query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
            assert gen.lesson_identifiable(demos, query) == []

            profiles = {
                gen.semantic_observables(pair["input"])["scene_profile"]
                for pair in demos
            }
            assert profiles == set(gen.SCENE_PROFILES)
            for name, competitor in gen.LESSON_COMPETITORS.items():
                assert any(
                    competitor(pair["input"]) != pair["output"]
                    for pair in demos
                ), name


def test_default_keyed_axes_match_returned_observation():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for sample_index in range(40):
                grid = gen.generate(
                    20_000 + band_index * 1_000,
                    sample_index,
                    difficulty=band,
                )
                ctx = captured[-1]
                expected = {axis: ctx.recorded_draws()[axis] for axis in gen.AXES}
                assert gen.observe_overrides(grid) == expected
    finally:
        generator_base.set_ctx_observer(None)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(126449)
    state = random.getstate()
    first = gen.generate(17, 9, difficulty="medium")
    assert random.getstate() == state
    second = gen.generate(17, 9, difficulty="medium")
    assert first == second
    assert first is not second and first[0] is not second[0]
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert first != second
    assert second != gen.generate(18, 9, difficulty="medium")
    assert second != gen.generate(17, 10, difficulty="medium")


def test_targeted_impostors_and_absent_feature_recombination_are_rejected():
    valid = gen.generate(
        901,
        12,
        difficulty="medium",
        grid_h=9,
        grid_w=9,
        seed_count=4,
    )
    assert gen.self_check(valid) == []
    facts = gen._analyze(valid)

    no_seeds = [[0 for _ in row] for row in valid]

    border_seed = copy.deepcopy(valid)
    r, c = facts["seeds"][0]["position"]
    color = border_seed[r][c]
    border_seed[r][c] = 0
    border_seed[0][c] = color

    duplicate_color = copy.deepcopy(valid)
    a, b = facts["seeds"][:2]
    br, bc = b["position"]
    duplicate_color[br][bc] = a["color"]

    seed_on_ray = copy.deepcopy(valid)
    source = facts["seeds"][0]
    target = next(cell for cell in source["ray"] if cell != source["position"])
    tr, tc = target
    replacement = next(
        value for value in range(1, 10)
        if value not in {seed["color"] for seed in facts["seeds"]}
    )
    seed_on_ray[tr][tc] = replacement

    invalid_cell = copy.deepcopy(valid)
    invalid_cell[0][0] = 12

    for name, impostor in {
        "no_seeds": no_seeds,
        "border_seed": border_seed,
        "duplicate_color": duplicate_color,
        "seed_on_ray": seed_on_ray,
        "invalid_cell": invalid_cell,
    }.items():
        assert gen.self_check(impostor), name

    # Negative recombination: add a color absent from every remaining scene
    # part on an existing ray.  The teaching grammar rejects it, while the
    # Racket-equivalent mirror still executes deterministically.
    assert gen.self_check(seed_on_ray)
    output = gen.rule_mirror(seed_on_ray)
    assert len(output) == len(seed_on_ray)
    assert len(output[0]) == len(seed_on_ray[0])
