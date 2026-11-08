"""Focused regression tests for generator b7e5824fc1ef."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from itertools import product
from pathlib import Path

import pytest

from puzzle_generators import base as generator_base
from scripts.canonical_profile_gate import canonical_pairs

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "b7e5824fc1ef"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        return next(json.loads(line) for line in handle if json.loads(line).get("task_id") == TASK_ID)


def test_rule_hash_authority_sync_and_all_canonical_pairs() -> None:
    row = _canonical_row()
    normalized = " ".join(row["program_solution"].split())
    assert GEN.RULE_HASH == hashlib.sha256(normalized.encode()).hexdigest()[:12]

    authority = json.loads(
        (ROOT / "data/base/solutions/training/e3497940__b7e5824fc1ef.json").read_text()
    )["racket_target"]
    assert authority["target_code"] == row["program_solution"]
    assert authority["raw_code"] != authority["target_code"]

    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror_merge(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_joint_override_is_exact_and_observable(difficulty: str) -> None:
    axes = product(
        GEN.SHAPE_PROFILES,
        (2, 3, 4),
        GEN.DENSITY_LEVELS,
        GEN.BALANCE_MODES,
    )
    for index, (shape_profile, palette_size, density, balance) in enumerate(axes):
        requested = {
            "shape_profile": shape_profile,
            "palette_size": palette_size,
            "density": density,
            "balance": balance,
        }
        grid = GEN.generate(73_000 + index, index * 31 + 7, difficulty=difficulty, **requested)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == requested


def test_default_draw_provenance_matches_realized_axes() -> None:
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band in ("easy", "medium", "hard"):
            for index in range(40):
                grid = GEN.generate(91_000 + index, index * 19 + 11, difficulty=band)
                draws = captured[-1].recorded_draws()
                assert GEN.observe_overrides(grid) == {
                    axis: draws[axis] for axis in GEN.AXES
                }
    finally:
        generator_base.set_ctx_observer(None)


def test_generated_draws_carry_all_decisive_witnesses_and_kill_rivals() -> None:
    for band in ("easy", "medium", "hard"):
        for index in range(60):
            grid = GEN.generate(110_000 + index, index * 37 + 5, difficulty=band)
            expected = GEN.rule_mirror_merge(grid)
            for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
                assert witness(grid), (band, index, witness_name)
                for rival_name in GEN.WITNESS_RIVALS[witness_name]:
                    assert GEN.SEMANTIC_RIVALS[rival_name](grid) != expected


def test_three_demo_lessons_identify_the_rule_in_every_band() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            pairs = []
            for offset in range(4):
                source = GEN.generate(220_000 + start, start * 7 + offset, difficulty=band)
                pairs.append({"input": source, "output": GEN.rule_mirror_merge(source)})
            assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_smaller_right_color_wins_different_color_overlap() -> None:
    grid = GEN.generate(
        414,
        9,
        difficulty="medium",
        shape_profile="canonical",
        palette_size=2,
        density="balanced",
        balance="even",
    )
    divider = len(grid[0]) // 2
    left = grid[2][divider - 1]
    right = grid[2][divider + 1]
    assert left > right > 0
    assert GEN.rule_mirror_merge(grid)[2][divider - 1] == right
    assert GEN.SEMANTIC_RIVALS["numeric_max_overlay"](grid)[2][divider - 1] == left


def test_mutations_and_unknown_overrides_fail_closed() -> None:
    fixtures = dict(GEN.mutation_fixtures())
    assert len(fixtures) >= 4
    for name, grid in fixtures.items():
        assert GEN.self_check(grid), name
    for overrides in (
        {"shape_profile": "huge"},
        {"palette_size": 1},
        {"density": "solid"},
        {"balance": "random"},
        {"texture": "empty_left"},
    ):
        with pytest.raises(ValueError):
            GEN.generate(1, 0, **overrides)


def test_negative_recombination_replacing_divider_is_rejected() -> None:
    grid = GEN.generate(12_345, 67, difficulty="hard")
    mutation = copy.deepcopy(grid)
    divider = len(mutation[0]) // 2
    replacement = next(color for color in range(1, 10) if color not in {5, *sum(mutation, [])})
    for row in mutation:
        row[divider] = replacement
    assert GEN.self_check(mutation)


def test_determinism_fresh_returns_global_rng_and_reentrant_aba() -> None:
    random.seed(20260727)
    before = random.getstate()
    first = GEN.generate(512, 23, difficulty="hard")
    assert random.getstate() == before
    middle = GEN.generate(513, 24, difficulty="easy")
    second = GEN.generate(512, 23, difficulty="hard")
    assert random.getstate() == before
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    snapshot = copy.deepcopy(first)
    middle[0][0] = 9 if middle[0][0] != 9 else 8
    second[0][0] = 9 if second[0][0] != 9 else 8
    assert first == snapshot
    assert GEN.generate(512, 23, difficulty="hard") == snapshot


def test_difficulty_bands_are_not_dead() -> None:
    for index in range(30):
        draws = [
            GEN.generate(771_000 + index, index * 13 + 3, difficulty=band)
            for band in ("easy", "medium", "hard")
        ]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in draws}) >= 2
