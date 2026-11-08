from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.dd231d152e42 import generator as gen


ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        row = next(json.loads(line) for line in handle if json.loads(line)["task_id"] == gen.TASK_ID)
    return [*row["train"], *row["test"]]


def _valid_grid(seed: int = 314159, sample_index: int = 3):
    grid = gen.generate(seed, sample_index, difficulty="medium")
    assert gen.self_check(grid) == []
    return grid


def test_rule_hash_and_every_canonical_pair_are_synchronized():
    assert gen.RULE_HASH == "7c29c678f8b1"
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._predict(pair["input"]) == pair["output"]


def test_boundary_overrides_are_exact_and_observable():
    cases = (
        {"grid_h": 5, "grid_w": 5, "n_emitters": 2, "n_blockers": 1, "n_distractors": 0},
        {"grid_h": 10, "grid_w": 10, "n_emitters": 6, "n_blockers": 3, "n_distractors": 2},
        {"grid_h": 5, "grid_w": 10, "n_emitters": 6, "n_blockers": 3, "n_distractors": 2},
        {"grid_h": 10, "grid_w": 5, "n_emitters": 2, "n_blockers": 3, "n_distractors": 2},
    )
    for seed, overrides in enumerate(cases):
        grid = gen.generate(seed, seed + 11, difficulty="hard", **overrides)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        assert gen.observe_overrides(grid) == overrides


def test_replay_returns_fresh_objects_and_preserves_global_rng():
    before = random.getstate()
    first = gen.generate(77, 8, difficulty="easy")
    after = random.getstate()
    second = gen.generate(77, 8, difficulty="easy")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert gen.generate(77, 8, difficulty="easy") == second


def test_self_check_rejects_targeted_structural_impostors():
    original = _valid_grid()
    analysis, errors = gen._analyze(original)
    assert errors == []

    mutants = {}

    corner = copy.deepcopy(original)
    er, ec, color, _ = analysis["emitters"][0]
    corner[er][ec] = 0
    corner[0][0] = color
    mutants["corner emitter"] = corner

    border_gray = copy.deepcopy(original)
    br, bc = next(iter(analysis["blockers"]))
    border_gray[br][bc] = 0
    border_gray[0][1] = 5
    mutants["border blocker"] = border_gray

    duplicate_color = copy.deepcopy(original)
    first, second = analysis["emitters"][:2]
    duplicate_color[second[0]][second[1]] = first[2]
    mutants["duplicate emitter color"] = duplicate_color

    no_blocker = copy.deepcopy(original)
    for r, c in analysis["blockers"]:
        no_blocker[r][c] = 0
    mutants["no blockers"] = no_blocker

    no_horizontal = copy.deepcopy(original)
    for r, c, _, side in analysis["emitters"]:
        if side in gen.HORIZONTAL_SIDES:
            no_horizontal[r][c] = 0
    mutants["no horizontal emitter"] = no_horizontal

    for name, mutant in mutants.items():
        assert gen.self_check(mutant), name


def test_sample_schedule_covers_every_declared_semantic_witness():
    grids = [gen.generate(20260725, sample_index, difficulty="medium") for sample_index in range(10)]
    missing = [
        name
        for name, predicate in gen.SEMANTIC_WITNESSES.items()
        if not any(predicate(grid) for grid in grids)
    ]
    assert missing == []


def test_degenerate_textures_are_rejected_by_self_check():
    for texture in gen.DEGENERATE_TEXTURES:
        assert gen.self_check(gen.generate(0, 0, texture=texture)), texture


def test_unknown_override_rejects_loudly():
    with pytest.raises(ValueError, match="unsupported override"):
        gen.generate(0, 0, imaginary_axis=1)
