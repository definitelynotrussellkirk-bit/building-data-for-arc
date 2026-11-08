from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs


GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.823621e5aa1f.generator"
)
ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "823621e5aa1f"


def _canonical_program() -> str:
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical row missing")


def _normalized_hash(text: str) -> str:
    return hashlib.sha256(" ".join(text.split()).encode()).hexdigest()[:12]


def test_rule_hash_and_all_canonical_pairs_are_exact():
    assert GEN.RULE_HASH == _normalized_hash(_canonical_program()) == "c6a5c373c678"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_generated_scene_uses_full_bands_and_exact_marker_semantics():
    for band in ("easy", "medium", "hard"):
        for seed in range(24):
            grid = GEN.generate(seed, seed, difficulty=band)
            assert GEN.self_check(grid) == []
            analysis, errors = GEN._analyze(grid)
            assert errors == []
            marker = analysis["marker_col"]
            stripe_rows = set(analysis["stripe_rows"])
            for row in range(analysis["height"]):
                outside = {grid[row][col] for col in range(analysis["width"]) if col != marker}
                assert len(outside) == 1
                assert grid[row][marker] == (1 if row in stripe_rows else 8)
                if row not in stripe_rows:
                    assert outside == {7}
            assert all(predicate(grid) for predicate in GEN.SEMANTIC_WITNESSES.values())
            expected = GEN.rule_mirror(grid)
            assert all(rival(grid) != expected for rival in GEN.SEMANTIC_RIVALS.values())


def test_exact_override_matrix_and_unknown_keys():
    cases = [
        {"height": 16, "width": 8, "marker_side": "left", "stripe_count": 2},
        {"height": 22, "width": 22, "marker_side": "right", "stripe_count": 5},
        {"height": 19, "width": 17, "marker_side": "center", "stripe_count": 4},
    ]
    for index, overrides in enumerate(cases):
        grid = GEN.generate(100 + index, 20 + index, difficulty="medium", **overrides)
        observed = GEN.observe_overrides(grid)
        assert {axis: observed[axis] for axis in overrides} == overrides
        assert GEN.self_check(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 1, obsolete_axis=3)


def test_deterministic_fresh_return_and_global_rng_purity():
    random.seed(918273645)
    state = random.getstate()
    first = GEN.generate(42, 7, difficulty="hard")
    assert random.getstate() == state
    replay = GEN.generate(42, 7, difficulty="hard")
    assert replay == first
    assert replay is not first
    assert all(a is not b for a, b in zip(first, replay))
    replay[0][0] = (replay[0][0] + 1) % 10
    assert GEN.generate(42, 7, difficulty="hard") == first


def test_self_check_rejects_targeted_impostors():
    valid = GEN.generate(777, 3, difficulty="medium")
    height, width = len(valid), len(valid[0])

    all_background = [[7 for _ in range(width)] for _ in range(height)]

    sparse_stripes = [[7 for _ in range(width)] for _ in range(height)]
    for row in range(height):
        sparse_stripes[row][1] = 8
    sparse_stripes[2][0] = 2
    sparse_stripes[6][0] = 3

    marker_mismatch = copy.deepcopy(valid)
    analysis, errors = GEN._analyze(valid)
    assert errors == []
    stripe_row = analysis["stripe_rows"][0]
    marker_mismatch[stripe_row][analysis["marker_col"]] = 8

    nonuniform_band = copy.deepcopy(valid)
    nonuniform_band[stripe_row][0] = (
        nonuniform_band[stripe_row][0] + 1
    ) % 10

    one_stripe_color = copy.deepcopy(valid)
    first_color = analysis["stripe_colors"][0]
    for row in analysis["stripe_rows"]:
        for col in range(width):
            if col != analysis["marker_col"]:
                one_stripe_color[row][col] = first_color

    for impostor in (
        all_background,
        sparse_stripes,
        marker_mismatch,
        nonuniform_band,
        one_stripe_color,
    ):
        assert GEN.self_check(impostor), impostor
