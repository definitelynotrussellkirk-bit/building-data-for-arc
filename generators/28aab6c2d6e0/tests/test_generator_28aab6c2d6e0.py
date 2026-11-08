from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import shutil
from pathlib import Path

import pytest

from puzzle_generators import base as generator_base


TASK_ID = "28aab6c2d6e0"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "shared/data/canonical/puzzles.jsonl").is_file():
            return parent
    raise AssertionError("could not locate staged repository root")


REPO_ROOT = _repo_root()
CANONICAL_PATH = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
AUTHORITY_PATH = (
    REPO_ROOT
    / "shared/data/base/solutions/banks/91ced140cdc4/M2__28aab6c2d6e0.json"
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
    assert GEN.RULE_HASH == digest == "c86a6d30fc9f"
    authority = json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))
    assert authority["racket_target"]["target_code"] == source


def test_canonical_inputs_are_accepted_and_python_mirror_matches_outputs():
    assert len(canonical_pairs()) == 3
    for pair in canonical_pairs():
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN._canonical_rule(source) == pair["output"]
        assert source == pair["input"]


def test_declared_axes_are_exact_observable_and_unknown_keys_are_rejected():
    cases = (
        {"grid_h": 7, "grid_w": 7, "n_objects": 2},
        {"grid_h": 7, "grid_w": 9, "n_objects": 4},
        {"grid_h": 8, "grid_w": 7, "n_objects": 4},
        {"grid_h": 8, "grid_w": 9, "n_objects": 2},
    )
    for index, overrides in enumerate(cases):
        grid = GEN.generate(1_000 + index, index, difficulty="easy", **overrides)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == overrides
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(9, 0, __override_contract_unknown_axis__=1)


def test_default_keyed_axis_requests_equal_returned_values():
    captured = []
    generator_base.set_ctx_observer(captured.append)
    try:
        for band in ("easy", "medium", "hard"):
            for seed in range(18):
                grid = GEN.generate(seed, seed * 17 + 3, difficulty=band)
                ctx = captured[-1]
                drawn = ctx.recorded_draws()
                assert set(drawn) >= set(GEN.AXES)
                assert GEN.observe_overrides(grid) == {
                    axis: drawn[axis] for axis in GEN.AXES
                }
    finally:
        generator_base.set_ctx_observer(None)


def test_determinism_fresh_returns_and_global_rng_isolation():
    random.seed(91_157)
    state = random.getstate()
    first = GEN.generate(91, 13, difficulty="hard", n_objects=4)
    assert random.getstate() == state
    second = GEN.generate(91, 13, difficulty="hard", n_objects=4)
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(91, 13, difficulty="hard", n_objects=4) == second


def test_ordinary_draws_cover_the_real_rule_not_only_l_trominoes():
    for band in ("easy", "medium", "hard"):
        grids = [
            GEN.generate(20_000 + seed, seed * 19 + 7, difficulty=band)
            for seed in range(90)
        ]
        facts = [GEN.semantic_observables(grid) for grid in grids]
        assert all(item["expanding_objects"] == item["n_objects"] for item in facts)
        assert all(item["non_l_expanding_objects"] >= 1 for item in facts)
        assert all(item["n_colors"] == 2 for item in facts)
        assert len({frozen(grid) for grid in grids}) >= 85


def test_every_three_demo_window_refutes_all_declared_competitors():
    for band in ("easy", "medium", "hard"):
        for seed in range(24):
            start = seed * 11
            grids = [
                GEN.generate(70_000 + seed, start + offset, difficulty=band)
                for offset in range(GEN.EXAMPLES_NEEDED)
            ]
            demos = [
                {"input": grid, "output": GEN._canonical_rule(grid)}
                for grid in grids
            ]
            query_grid = GEN.generate(80_000 + seed, start + 9, difficulty=band)
            query = {"input": query_grid, "output": GEN._canonical_rule(query_grid)}
            assert GEN.lesson_identifiable(demos, query) == []
            assert any(
                GEN.semantic_observables(grid)["per_color_bbox_traps"] >= 1
                for grid in grids
            )
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_canonical_shortcut_fits_public_pairs_but_generated_witness_refutes_it():
    shortcut = GEN.CANONICAL_SHORTCUTS["per_color_bbox"]
    for pair in canonical_pairs():
        assert shortcut(pair["input"]) == pair["output"]

    grid = GEN.generate(303, 1, difficulty="easy", n_objects=3)
    assert GEN.SEMANTIC_WITNESSES["repeated_color_components"](grid)
    assert shortcut(grid) != GEN._canonical_rule(grid)


def test_each_witness_claim_has_a_real_generated_disagreement():
    samples = [
        GEN.generate(501, 0, difficulty="easy", n_objects=2),
        GEN.generate(502, 1, difficulty="medium", n_objects=3),
        GEN.generate(503, 2, difficulty="hard", n_objects=4),
    ]
    for witness_name, rivals in GEN.WITNESS_RIVALS.items():
        matching = [grid for grid in samples if GEN.SEMANTIC_WITNESSES[witness_name](grid)]
        assert matching, witness_name
        for rival_name in rivals:
            assert any(
                GEN.SEMANTIC_RIVALS[rival_name](grid) != GEN._canonical_rule(grid)
                for grid in matching
            ), (witness_name, rival_name)


def test_self_check_rejects_identity_branch_and_missing_non_l_branch():
    valid = GEN.generate(404, 2, difficulty="hard", n_objects=4)
    assert GEN.self_check(valid) == []

    identity = copy.deepcopy(valid)
    component = GEN._components(identity)[0]
    r1, c1, r2, c2 = GEN._bbox(component["cells"])
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            identity[r][c] = component["color"]
    assert GEN.self_check(identity)

    all_l = [[0] * 7 for _ in range(7)]
    for r, c in ((0, 0), (0, 1), (1, 0)):
        all_l[r][c] = 2
    for r, c in ((5, 5), (5, 6), (6, 6)):
        all_l[r][c] = 4
    assert GEN.self_check(all_l)


@pytest.mark.skipif(shutil.which("racket") is None, reason="racket is not installed")
def test_real_racket_matches_canonical_and_generated_cases():
    from arc_repl.racket_bridge import RacketBridge
    from scripts.rule_smoke import rule_application

    source = canonical_row()["program_solution"]
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for pair in canonical_pairs():
            grid = copy.deepcopy(pair["input"])
            snapshot = copy.deepcopy(grid)
            assert bridge.eval_text(rule_application(source, grid)) == pair["output"]
            assert grid == snapshot
        count = 0
        for band_index, band in enumerate(("easy", "medium", "hard")):
            for seed in range(10):
                grid = GEN.generate(50_000 + seed, band_index * 100 + seed, difficulty=band)
                snapshot = copy.deepcopy(grid)
                assert bridge.eval_text(rule_application(source, grid)) == GEN._canonical_rule(grid)
                assert grid == snapshot
                count += 1
        assert count == 30
    finally:
        bridge.shutdown()
