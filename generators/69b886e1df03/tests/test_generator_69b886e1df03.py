from __future__ import annotations

import copy
import hashlib
import json
import random
import shutil
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators import base as generator_base
import importlib

module = importlib.import_module("puzzle_generators.per_puzzle.69b886e1df03.generator")
from scripts.rule_smoke import rule_application


TASK_ID = "69b886e1df03"
ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PATH = ROOT / "data/canonical/puzzles.jsonl"
AUTHORITY_PATH = (
    ROOT
    / "data/base/solutions/banks/2eea055c3155/medium_06__69b886e1df03.json"
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


def test_rule_hash_and_selected_task_rule_are_pinned():
    row = canonical_row()
    source = row["program_solution"]
    digest = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert module.RULE_HASH == digest == "3cad5a2fcf1f"
    authority = json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))
    assert authority["racket_target"]["target_code"] == source
    assert authority["racket_target"]["raw_code"] != source


def test_every_canonical_input_is_accepted():
    assert len(canonical_pairs()) == 4
    for pair in canonical_pairs():
        source = copy.deepcopy(pair["input"])
        assert module.self_check(source) == []
        assert source == pair["input"]


def test_exact_axes_are_observable_at_joint_boundaries():
    cases = (
        {"grid_h": 4, "grid_w": 5, "n_objects": 2},
        {"grid_h": 4, "grid_w": 18, "n_objects": 6},
        {"grid_h": 18, "grid_w": 5, "n_objects": 6},
        {"grid_h": 18, "grid_w": 18, "n_objects": 6},
    )
    for index, overrides in enumerate(cases):
        grid = module.generate(1_000 + index, index, difficulty="easy", **overrides)
        assert module.self_check(grid) == []
        assert module.observe_overrides(grid) == overrides


def test_default_keyed_axis_requests_equal_returned_grid_values():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band in ("easy", "medium", "hard"):
            for seed in range(40):
                grid = module.generate(seed, seed * 17 + 3, difficulty=band)
                ctx = captured[-1]
                assert set(ctx._drawn) >= set(module.AXES)
                assert module.observe_overrides(grid) == {
                    axis: ctx._drawn[axis] for axis in module.AXES
                }
    finally:
        generator_base.set_ctx_observer(None)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(91_157)
    state = random.getstate()
    first = module.generate(91, 13, difficulty="hard", n_objects=6)
    assert random.getstate() == state
    second = module.generate(91, 13, difficulty="hard", n_objects=6)
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert module.generate(91, 13, difficulty="hard", n_objects=6) == second


def test_every_ordinary_draw_fires_and_mixes_identity_and_expansion_branches():
    for band in ("easy", "medium", "hard"):
        grids = [
            module.generate(20_000 + seed, seed * 19 + 7, difficulty=band)
            for seed in range(120)
        ]
        facts = [module.semantic_observables(grid) for grid in grids]
        assert all(item["expanding_objects"] >= 1 for item in facts)
        assert all(item["identity_objects"] >= 1 for item in facts)
        assert any(item["edge_objects"] >= 1 for item in facts)
        assert len({frozen(grid) for grid in grids}) >= 115
        assert len({(item["grid_h"], item["grid_w"], item["n_objects"]) for item in facts}) >= 8




def test_every_three_demo_schedule_refutes_identity_and_per_color_shortcuts():
    for band in ("easy", "medium", "hard"):
        for seed in range(60):
            grids = [
                module.generate(70_000 + seed, base + offset, difficulty=band)
                for base in (seed * 3,)
                for offset in range(3)
            ]
            facts = [module.semantic_observables(grid) for grid in grids]
            assert all(item["expanding_objects"] >= 1 for item in facts)
            assert any(item["per_color_bbox_traps"] >= 1 for item in facts)

def test_repeated_color_scene_refutes_per_color_bbox_shortcut():
    grid = module.generate(
        303,
        1,
        difficulty="hard",
        grid_h=14,
        grid_w=15,
        n_objects=5,
    )
    facts = module.semantic_observables(grid)
    assert facts["repeated_colors"] == 1
    assert facts["per_color_bbox_traps"] == 1
    assert facts["n_colors"] == facts["n_objects"] - 1


def test_self_check_rejects_minimal_and_targeted_impostors():
    impostors = (
        [[0] * 6 for _ in range(5)],
        [[0, 0, 0], [0, 4, 0], [0, 0, 0]],
        [[0, 0, 0, 0], [0, 5, 5, 0], [0, 0, 0, 0]],
        [[0, 0, 0, 0], [0, 6, 6, 0], [0, 6, 6, 0], [0, 0, 0, 0]],
    )
    for grid in impostors:
        assert module.self_check(grid)

    valid = module.generate(404, 8, difficulty="hard", n_objects=5)
    comps = module._components(valid)
    malformed = copy.deepcopy(valid)
    comp = max(comps, key=lambda item: len(item["cells"]))
    r1, c1, r2, c2 = module._bbox(comp["cells"])
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            malformed[r][c] = comp["color"]
    assert module.self_check(malformed)


@pytest.mark.skipif(shutil.which("racket") is None, reason="racket is not installed")
def test_real_racket_matches_all_canonical_pairs_and_40_generated_applications():
    source = canonical_row()["program_solution"]
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for pair in canonical_pairs():
            grid = copy.deepcopy(pair["input"])
            snapshot = copy.deepcopy(grid)
            assert bridge.eval_text(rule_application(source, grid)) == pair["output"]
            assert grid == snapshot
        exact = 0
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for seed in range(12):
                grid = module.generate(50_000 + seed, band_index * 100 + seed, difficulty=band)
                snapshot = copy.deepcopy(grid)
                output = bridge.eval_text(rule_application(source, grid))
                assert isinstance(output, list)
                assert output != grid
                assert grid == snapshot
                exact += 1
        assert exact == 36
    finally:
        bridge.shutdown()


def test_rejected_recombination_is_distribution_invalid_but_oracle_executable():
    grid = module.generate(505, 10, difficulty="medium", n_objects=4)
    malformed = copy.deepcopy(grid)
    comp = next(
        item
        for item in module._components(malformed)
        if len(module._rect_cells(module._bbox(item["cells"]))) > len(item["cells"])
    )
    r1, c1, r2, c2 = module._bbox(comp["cells"])
    absent_color = next(color for color in range(1, 10) if color not in {v for row in grid for v in row})
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            malformed[r][c] = absent_color
    assert module.self_check(malformed)
    if shutil.which("racket") is not None:
        bridge = RacketBridge(max_calls_before_restart=8)
        try:
            output = bridge.eval_text(rule_application(canonical_row()["program_solution"], malformed))
            assert isinstance(output, list)
        finally:
            bridge.shutdown()
