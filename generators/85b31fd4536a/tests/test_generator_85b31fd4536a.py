"""Focused semantic and distribution regressions for 85b31fd4536a."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base as generator_base
gen = importlib.import_module("puzzle_generators.per_puzzle.85b31fd4536a.generator")
from scripts.canonical_profile_gate import canonical_pairs

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"


def _canonical_rule() -> str:
    for line in CANONICAL.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return str(row["program_solution"])
    raise AssertionError("canonical task row missing")


def _pair(seed: int, sample_index: int, difficulty: str | None) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_pinned():
    normalized = " ".join(_canonical_rule().split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == gen.RULE_HASH
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_override_boundary_is_exact_and_observable(difficulty):
    index = 0
    for grid_h in (4, 6):
        for panel_w in (3, 5):
            for mask_components in (3, 4):
                for src_colors in (2, 7):
                    requested = {
                        "grid_h": grid_h,
                        "panel_w": panel_w,
                        "mask_components": mask_components,
                        "src_colors": src_colors,
                    }
                    grid = gen.generate(
                        20_000 + index,
                        700 + index,
                        difficulty=difficulty,
                        **requested,
                    )
                    assert gen.self_check(
                        grid,
                        difficulty=difficulty,
                        meta={"overrides": requested},
                    ) == []
                    assert gen.observe_overrides(grid) == requested
                    index += 1


def test_default_keyed_axes_equal_realized_axes_in_every_band():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band_index, difficulty in enumerate(("easy", "medium", "hard")):
            for sample_index in range(30):
                grid = gen.generate(
                    40_000 + band_index,
                    sample_index,
                    difficulty=difficulty,
                )
                ctx = captured[-1]
                expected = {axis: ctx.axis_value(axis) for axis in gen.AXES}
                assert gen.observe_overrides(grid) == expected
    finally:
        generator_base.set_ctx_observer(None)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_each_single_demo_refutes_every_named_competitor(difficulty):
    pairs = [_pair(88_210, index, difficulty) for index in range(12)]
    for start in range(8):
        demos = pairs[start : start + gen.EXAMPLES_NEEDED]
        query = pairs[start + gen.EXAMPLES_NEEDED]
        assert gen.lesson_identifiable(demos, query) == []
        for name, rival in gen.LESSON_COMPETITORS.items():
            assert any(
                rival(pair["input"]) != pair["output"] for pair in demos
            ), name


def test_targeted_impostors_and_negative_recombination_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(copy.deepcopy(grid)), name

    malformed, replacement = gen.negative_recombination_fixture()
    assert sum(
        value == replacement for row in malformed for value in row
    ) == 1
    assert gen.self_check(malformed)
    # The fixed transform is still executable; distribution validity and oracle
    # executability are intentionally separate outcomes.
    assert gen._rule_unchecked(malformed)


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(99_117)
    state = random.getstate()
    first = gen.generate(117, 9, difficulty="hard")
    assert random.getstate() == state
    replay = gen.generate(117, 9, difficulty="hard")
    assert first == replay
    assert first is not replay
    assert all(a is not b for a, b in zip(first, replay))
    expected = copy.deepcopy(replay)
    first[0][0] = 8 if first[0][0] != 8 else 7
    assert gen.generate(117, 9, difficulty="hard") == expected
    assert gen.generate(118, 9, difficulty="hard") != expected
    assert gen.generate(117, 10, difficulty="hard") != expected


def test_invalid_calls_reject_loudly():
    for kwargs in (
        {"unknown_axis": 3},
        {"grid_h": 3},
        {"grid_h": True},
        {"panel_w": 6},
        {"mask_components": 2},
        {"src_colors": 8},
    ):
        with pytest.raises(ValueError):
            gen.generate(1, 1, **kwargs)
    with pytest.raises(ValueError):
        gen.generate(1, 1, difficulty="extreme")
