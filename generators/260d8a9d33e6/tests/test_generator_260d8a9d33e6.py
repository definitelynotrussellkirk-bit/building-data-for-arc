from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import shutil
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators import base as generator_base
from scripts.rule_smoke import rule_application


TASK_ID = "260d8a9d33e6"
ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PATH = ROOT / "data/canonical/puzzles.jsonl"
AUTHORITY_PATH = (
    ROOT
    / "data/base/solutions/banks/2eea055c3155/hard_05__260d8a9d33e6.json"
)
module = importlib.import_module(
    "puzzle_generators.per_puzzle.260d8a9d33e6.generator"
)


def canonical_row() -> dict:
    for line in CANONICAL_PATH.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical task row missing")


def canonical_pairs() -> list[dict]:
    row = canonical_row()
    return [pair for split in ("train", "test") for pair in row[split]]


def frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_and_selected_authority_are_pinned():
    row = canonical_row()
    source = row["program_solution"]
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert module.RULE_HASH == digest == "38b85f1dff1d"
    authority = json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))
    assert authority["racket_target"]["target_code"] == source


def test_every_canonical_input_is_accepted_without_mutation():
    pairs = canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        snapshot = copy.deepcopy(grid)
        assert module.self_check(grid) == []
        assert module.strict_canonical_like(grid) == []
        assert grid == snapshot


def test_exact_axes_are_observable_at_joint_boundaries():
    cases = (
        {
            "grid_h": 5,
            "grid_w": 6,
            "frame_shape": "square4",
            "inside_pattern": "singleton",
            "outside_pattern": "singleton",
        },
        {
            "grid_h": 5,
            "grid_w": 10,
            "frame_shape": "square5",
            "inside_pattern": "split",
            "outside_pattern": "connected",
        },
        {
            "grid_h": 8,
            "grid_w": 6,
            "frame_shape": "tall",
            "inside_pattern": "connected",
            "outside_pattern": "singleton",
        },
        {
            "grid_h": 8,
            "grid_w": 10,
            "frame_shape": "wide",
            "inside_pattern": "split",
            "outside_pattern": "connected",
        },
    )
    for index, overrides in enumerate(cases):
        grid = module.generate(10_000 + index, index, difficulty="easy", **overrides)
        assert module.self_check(grid) == []
        assert module.observe_overrides(grid) == overrides


def test_unknown_override_is_rejected_instead_of_silently_ignored():
    with pytest.raises(TypeError, match="unknown override"):
        module.generate(0, 0, __override_contract_unknown_axis__=1)


def test_default_keyed_axis_requests_equal_observed_values():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band in ("easy", "medium", "hard"):
            for seed in range(40):
                grid = module.generate(seed, seed * 17 + 3, difficulty=band)
                ctx = captured[-1]
                draws = ctx.recorded_draws()
                assert set(draws) >= set(module.AXES)
                assert module.observe_overrides(grid) == {
                    axis: draws[axis] for axis in module.AXES
                }
    finally:
        generator_base.set_ctx_observer(None)


def test_determinism_fresh_returns_and_global_rng_isolation():
    overrides = {
        "grid_h": 8,
        "grid_w": 10,
        "frame_shape": "square5",
        "inside_pattern": "connected",
        "outside_pattern": "connected",
    }
    random.seed(91_157)
    state = random.getstate()
    first = module.generate(91, 13, difficulty="hard", **overrides)
    assert random.getstate() == state
    second = module.generate(91, 13, difficulty="hard", **overrides)
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert module.generate(91, 13, difficulty="hard", **overrides) == second


def test_each_band_covers_profiles_and_both_decisive_effects():
    canonical_profiles = {(5, 6, 4), (5, 8, 4), (6, 7, 4)}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [
            module.generate(20_000 + band_index * 1_000 + seed, seed, difficulty=band)
            for seed in range(200)
        ]
        facts = [module.semantic_observables(grid) for grid in grids]
        assert all(module.SEMANTIC_WITNESSES["visible_inside_recolor"](grid) for grid in grids)
        assert all(module.SEMANTIC_WITNESSES["outside_erasure"](grid) for grid in grids)
        assert {item["inside_pattern"] for item in facts} == {
            "singleton",
            "connected",
            "split",
        }
        assert {item["outside_pattern"] for item in facts} == {
            "singleton",
            "connected",
        }
        assert {item["frame_shape"] for item in facts} == set(module._FRAME_SHAPES)
        exact = sum(
            (item["grid_h"], item["grid_w"], 4) in canonical_profiles
            and item["frame_shape"] == "square4"
            for item in facts
        )
        assert exact > 0
        assert len({frozen(grid) for grid in grids}) >= 195


def test_every_sliding_two_demo_window_refutes_named_competitors():
    # EXAMPLES_NEEDED=2.  Exhaust every residue-class start in the six-profile
    # topology schedule, across all bands, using real oracle outputs below.
    source = canonical_row()["program_solution"]
    if shutil.which("racket") is None:
        pytest.skip("racket is not installed")
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for band in ("easy", "medium", "hard"):
            for start in range(6):
                rows = []
                for offset in range(3):
                    grid = module.generate(30_000 + start, start + offset, difficulty=band)
                    rows.append(
                        {
                            "input": grid,
                            "output": bridge.eval_text(rule_application(source, grid)),
                        }
                    )
                assert module.lesson_identifiable(rows[:2], rows[2]) == []
    finally:
        bridge.shutdown()


def test_self_check_rejects_minimal_and_targeted_impostors():
    impostors = [
        [[0] * 7 for _ in range(6)],
        [[1] * 7 for _ in range(6)],
        [[0] * 7 for _ in range(6)],
        [[0] * 7 for _ in range(6)],
    ]
    # singleton-only and solid-2x2 impostors
    impostors[2][2][3] = 4
    for r in (2, 3):
        for c in (2, 3):
            impostors[3][r][c] = 5
    for grid in impostors:
        assert module.self_check(grid)

    valid = module.generate(
        404,
        4,
        difficulty="medium",
        grid_h=6,
        grid_w=8,
        frame_shape="square4",
        inside_pattern="connected",
        outside_pattern="connected",
    )
    facts = module._analyze(valid)
    frame = facts["frames"][0]

    no_outside = copy.deepcopy(valid)
    for comp in facts["outside"]:
        for r, c in comp["cells"]:
            no_outside[r][c] = 0
    assert module.self_check(no_outside)

    solid_frame = copy.deepcopy(valid)
    r0, c0, r1, c1 = frame["bbox"]
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            solid_frame[r][c] = frame["color"]
    assert module.self_check(solid_frame)

    same_role_color = copy.deepcopy(valid)
    for comp in facts["outside"]:
        for r, c in comp["cells"]:
            same_role_color[r][c] = frame["color"]
    assert module.self_check(same_role_color)


def test_negative_recombination_is_rejected_but_oracle_can_execute():
    grid = module.generate(505, 5, difficulty="medium")
    malformed = copy.deepcopy(grid)
    facts = module._analyze(malformed)
    frame = facts["frames"][0]
    used = {value for row in malformed for value in row}
    replacement_color = next(color for color in range(1, 10) if color not in used)

    # Remove the true frame, then insert a novel solid 2x2 replacement whose
    # color/shape is absent from every remaining scene part.
    for r, c in frame["cells"]:
        malformed[r][c] = 0
    for r in range(2):
        for c in range(2):
            malformed[r][c] = replacement_color
    assert module.self_check(malformed)

    if shutil.which("racket") is not None:
        bridge = RacketBridge(max_calls_before_restart=8)
        try:
            output = bridge.eval_text(
                rule_application(canonical_row()["program_solution"], malformed)
            )
            assert isinstance(output, list)
        finally:
            bridge.shutdown()


@pytest.mark.skipif(shutil.which("racket") is None, reason="racket is not installed")
def test_real_racket_matches_canonical_and_40_generated_applications():
    source = canonical_row()["program_solution"]
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        exact = 0
        for pair in canonical_pairs():
            grid = copy.deepcopy(pair["input"])
            snapshot = copy.deepcopy(grid)
            assert bridge.eval_text(rule_application(source, grid)) == pair["output"]
            assert grid == snapshot
            exact += 1
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for seed in range(12):
                grid = module.generate(50_000 + seed, band_index * 100 + seed, difficulty=band)
                snapshot = copy.deepcopy(grid)
                output = bridge.eval_text(rule_application(source, grid))
                assert isinstance(output, list)
                assert output != grid
                assert grid == snapshot
                exact += 1
        assert exact == 40
    finally:
        bridge.shutdown()
