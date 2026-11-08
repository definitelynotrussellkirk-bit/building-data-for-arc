"""Focused semantic regressions for generator 3b75d3395ebb."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from puzzle_generators import base as generator_base  # noqa: E402
from scripts.canonical_profile_gate import canonical_pairs  # noqa: E402

MODULE_PATH = Path(__file__).with_name("generator.py")
SPEC = importlib.util.spec_from_file_location("generator_3b75d3395ebb", MODULE_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"


def _canonical_rule() -> str:
    for line in CANONICAL.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == GEN.TASK_ID:
            return str(row["program_solution"])
    raise AssertionError("canonical task row missing")


def _pair(seed: int, sample_index: int, difficulty: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_every_canonical_pair_are_pinned():
    normalized = " ".join(_canonical_rule().split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH
    pairs = canonical_pairs(GEN.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_canonical_connected_wall_exception_is_not_fill_every_frame():
    pairs = canonical_pairs(GEN.TASK_ID)
    connected = [
        pair for pair in pairs
        if GEN.observe_overrides(pair["input"])["scene_profile"] == "connected_only"
    ]
    assert len(connected) == 3
    for pair in connected:
        assert pair["output"] == pair["input"]
        assert GEN._fill_all_visual_frames(pair["input"]) != pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_boundary_override_is_exact_and_observable(difficulty):
    for height in (10, 14):
        for width in (11, 16):
            for index, profile in enumerate(GEN.SCENE_PROFILES):
                requested = {
                    "grid_h": height,
                    "grid_w": width,
                    "scene_profile": profile,
                }
                grid = GEN.generate(
                    20_000 + index,
                    700 + index,
                    difficulty=difficulty,
                    **requested,
                )
                assert GEN.self_check(
                    grid,
                    difficulty=difficulty,
                    meta={"overrides": requested},
                ) == []
                assert GEN.observe_overrides(grid) == requested


def test_default_keyed_axes_match_observed_scene():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        seen = set()
        for band_index, difficulty in enumerate(("easy", "medium", "hard")):
            for sample_index in range(20):
                grid = GEN.generate(
                    40_000 + band_index,
                    sample_index,
                    difficulty=difficulty,
                )
                ctx = captured[-1]
                expected = {axis: ctx.axis_value(axis) for axis in GEN.AXES}
                observed = GEN.observe_overrides(grid)
                assert observed == expected
                assert observed["scene_profile"] == GEN.schedule_profile(
                    40_000 + band_index, sample_index, difficulty
                )
                seen.add(observed["scene_profile"])
        assert seen == set(GEN.SCENE_PROFILES)
    finally:
        generator_base.set_ctx_observer(None)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_sliding_two_demo_lesson_refutes_named_competitors(difficulty):
    pairs = [_pair(88_210, index, difficulty) for index in range(10)]
    for start in range(8):
        demos = pairs[start : start + GEN.EXAMPLES_NEEDED]
        query = pairs[start + GEN.EXAMPLES_NEEDED]
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            survives_demos = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            assert not (
                survives_demos
                and rival(query["input"]) != query["output"]
            ), name


def test_targeted_impostors_and_negative_recombination_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 5
    for name, grid in fixtures:
        assert GEN.self_check(copy.deepcopy(grid)), name

    valid = GEN.generate(
        77,
        1,
        difficulty="medium",
        grid_h=11,
        grid_w=13,
        scene_profile="mixed",
    )
    analysis = GEN._analyze(valid)
    recombined = copy.deepcopy(valid)
    wall_cell = next(iter(GEN._perimeter(analysis["rooms"][0])))
    replacement = next(
        color for color in range(1, 10)
        if color not in analysis["palette"] and color != GEN._WALL
    )
    recombined[wall_cell[0]][wall_cell[1]] = replacement
    assert replacement not in {value for row in valid for value in row}
    assert GEN.self_check(recombined)
    oracle_output = GEN.rule_mirror(recombined)
    assert len(oracle_output) == len(recombined)
    assert len(oracle_output[0]) == len(recombined[0])


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(99117)
    state = random.getstate()
    first = GEN.generate(117, 9, difficulty="hard")
    assert random.getstate() == state
    replay = GEN.generate(117, 9, difficulty="hard")
    assert first == replay
    assert first is not replay
    assert all(a is not b for a, b in zip(first, replay))
    expected = copy.deepcopy(replay)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(117, 9, difficulty="hard") == expected
    assert GEN.generate(118, 9, difficulty="hard") != expected
    assert GEN.generate(117, 10, difficulty="hard") != expected


def test_invalid_calls_reject_loudly():
    for kwargs in (
        {"unknown_axis": 3},
        {"grid_h": 9},
        {"grid_h": True},
        {"grid_w": 17},
        {"scene_profile": "all_touching"},
    ):
        with pytest.raises(ValueError):
            GEN.generate(1, 1, **kwargs)
    with pytest.raises(ValueError):
        GEN.generate(1, 1, difficulty="extreme")
