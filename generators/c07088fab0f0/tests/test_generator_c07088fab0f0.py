"""Focused regression, authority, override, and semantic tests for c07088fab0f0."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.base import set_ctx_observer
from scripts.generator_module_loader import load_module_from_path
from scripts.rule_smoke import purity_body, rule_application

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "c07088fab0f0"
GENERATOR_PATH = ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py"
BASE_PATH = (
    ROOT
    / "data/base/solutions/banks/534c4be491a1"
    / "S10_H6__c07088fab0f0.json"
)
MODULE = load_module_from_path(f"test_generator_{TASK_ID}_module", GENERATOR_PATH)


def _canonical_row() -> dict:
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _norm_grid(grid) -> list[list[int]]:
    return [
        [int(value) for value in row] if isinstance(row, str) else list(row)
        for row in grid
    ]


def _all_pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"]
    pairs = list(row["train"]) + (list(test) if isinstance(test, list) else [test])
    return [
        {"input": _norm_grid(pair["input"]), "output": _norm_grid(pair["output"])}
        for pair in pairs
    ]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _clear_quadrant(grid, index: int) -> list[list[int]]:
    out = copy.deepcopy(grid)
    q = len(grid) // 2
    origin_r, origin_c = MODULE._quadrant_origins(q)[index]
    for r in range(q):
        for c in range(q):
            out[origin_r + r][origin_c + c] = 0
    return out


def _replace_quadrant(grid, index: int, cells, color: int) -> list[list[int]]:
    out = _clear_quadrant(grid, index)
    q = len(grid) // 2
    origin_r, origin_c = MODULE._quadrant_origins(q)[index]
    for r, c in cells:
        out[origin_r + r][origin_c + c] = color
    return out


def test_metadata_rule_hash_and_selected_authority_are_exact() -> None:
    row = _canonical_row()
    canonical = row["program_solution"]
    base = json.loads(BASE_PATH.read_text(encoding="utf-8"))
    target = base["racket_target"]

    assert MODULE.VERSION == "3.0.0"
    assert MODULE.RULE_HASH == "722f434cd224"
    assert MODULE.RULE_HASH == _normalized_rule_hash(canonical)
    assert target["target_code"] == canonical
    assert target["raw_code"] == canonical


def test_all_canonical_pairs_are_accepted_mirrored_and_input_pure() -> None:
    pairs = _all_pairs()
    assert len(pairs) == 3
    assert [MODULE.observe_overrides(pair["input"])["missing_quadrant"] for pair in pairs] == [
        "bottom_right",
        "top_left",
        "top_right",
    ]
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.strict_canonical_like(pair["input"]) == []
        assert MODULE.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_canonical_racket_parity_input_purity_and_a_b_a() -> None:
    source = _canonical_row()["program_solution"]
    pairs = _all_pairs()
    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        for pair in pairs:
            before = copy.deepcopy(pair["input"])
            actual = bridge.eval_text(rule_application(source, pair["input"]))
            assert actual == pair["output"]
            assert pair["input"] == before
        probe = bridge.eval_text(
            purity_body(source, pairs[0]["input"], pairs[1]["input"])
        )
        assert probe[0] == pairs[0]["output"]
        assert probe[1] == pairs[0]["output"]
        assert probe[2] == pairs[0]["input"]
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exact_override_boundaries_are_observable(difficulty: str) -> None:
    cases = [
        {"quad_size": 4},
        {"quad_size": 12},
        {"shape_cells": 3},
        {"shape_cells": 10},
        {"foreground_color": 1},
        {"foreground_color": 9},
        {"missing_quadrant": "top_left"},
        {"missing_quadrant": "top_right"},
        {"missing_quadrant": "bottom_left"},
        {"missing_quadrant": "bottom_right"},
        {
            "quad_size": 4,
            "shape_cells": 10,
            "foreground_color": 9,
            "missing_quadrant": "bottom_right",
        },
    ]
    for index, overrides in enumerate(cases):
        grid = MODULE.generate(
            10_000 + index,
            500 + index,
            difficulty=difficulty,
            **overrides,
        )
        assert MODULE.self_check(grid) == []
        observed = MODULE.observe_overrides(grid)
        for name, requested in overrides.items():
            assert observed[name] == requested


def test_unknown_invalid_and_wrong_typed_overrides_fail_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        MODULE.generate(1, 2, obsolete_axis=3)
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, quad_size=3)
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, quad_size=13)
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, shape_cells=2)
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, shape_cells=11)
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, foreground_color=5)
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, missing_quadrant="center")
    with pytest.raises(ValueError, match="difficulty"):
        MODULE.generate(1, 2, difficulty="expert")


def test_default_draw_provenance_matches_exact_observer() -> None:
    captured = []
    set_ctx_observer(captured.append)
    try:
        grid = MODULE.generate(73, 19, difficulty="hard")
    finally:
        set_ctx_observer(None)
    assert len(captured) == 1
    assert set(captured[0].recorded_draws()) == set(MODULE.AXES)
    assert captured[0].recorded_draws() == MODULE.observe_overrides(grid)
    assert captured[0].overrides_used() == {}


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(987_654_321)
    state = random.getstate()
    first = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    replay = MODULE.generate(901, 17, difficulty="hard")
    assert random.getstate() == state
    assert replay == first
    assert replay is not first
    assert all(a is not b for a, b in zip(replay, first))
    replay[0][0] = 9 if replay[0][0] != 9 else 8
    assert MODULE.generate(901, 17, difficulty="hard") == first


def test_linked_semantic_census_200_per_band_and_disjoint_stability() -> None:
    witness_names = set(MODULE.SEMANTIC_WITNESSES)
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [
            MODULE.generate(20_000 + band_index * 1_000 + seed, seed, difficulty=band)
            for seed in range(200)
        ]
        assert all(MODULE.self_check(grid) == [] for grid in grids)
        assert all(MODULE.rule_mirror(grid) != grid for grid in grids)
        assert len({_frozen(grid) for grid in grids}) >= 150
        assert len({_frozen(MODULE.rule_mirror(grid)) for grid in grids}) >= 150
        assert sum(not MODULE.strict_canonical_like(grid) for grid in grids) >= 40

        fired = {
            name
            for name, witness in MODULE.SEMANTIC_WITNESSES.items()
            if any(witness(grid) for grid in grids)
        }
        assert fired == witness_names
        observed = [MODULE.observe_overrides(grid) for grid in grids]
        assert {item["missing_quadrant"] for item in observed} == set(MODULE._QUADRANT_NAMES)
        assert {item["shape_cells"] for item in observed} == set(range(3, 11))
        assert {item["foreground_color"] for item in observed} == set(MODULE._COLORS)

        later = [
            MODULE.generate(80_000 + band_index * 1_000 + seed, 1_000 + seed, difficulty=band)
            for seed in range(200)
        ]
        assert all(MODULE.self_check(grid) == [] for grid in later)
        assert len({_frozen(grid) for grid in later}) >= 150
        assert {
            name
            for name, witness in MODULE.SEMANTIC_WITNESSES.items()
            if any(witness(grid) for grid in later)
        } == witness_names
        assert {_frozen(grid) for grid in grids} != {_frozen(grid) for grid in later}


def test_three_demo_schedule_rebuts_orientation_copy_and_identity_shortcuts() -> None:
    for seed in range(40):
        pairs = []
        for sample_index in range(4):
            grid = MODULE.generate(seed, sample_index, difficulty="medium")
            pairs.append({"input": grid, "output": MODULE.rule_mirror(grid)})
        assert MODULE.lesson_identifiable(pairs[:3], pairs[3]) == []
        assert {
            MODULE.observe_overrides(pair["input"])["missing_quadrant"]
            for pair in pairs
        } == set(MODULE._QUADRANT_NAMES)
        assert all(pair["input"] != pair["output"] for pair in pairs)


def test_self_check_rejects_targeted_structural_impostors() -> None:
    valid = MODULE.generate(
        312,
        4,
        difficulty="medium",
        quad_size=12,
        shape_cells=4,
        missing_quadrant="bottom_right",
    )
    facts = MODULE._analyze(valid)
    assert facts["errors"] == []
    q = facts["quad_size"]

    no_cross = copy.deepcopy(valid)
    no_cross[q][0] = 0
    assert MODULE.self_check(no_cross)

    no_shape = copy.deepcopy(valid)
    for r in range(len(no_shape)):
        for c in range(len(no_shape[0])):
            if r != q and c != q:
                no_shape[r][c] = 0
    assert MODULE.self_check(no_shape)

    two_missing = _clear_quadrant(valid, facts["filled_indices"][0])
    assert MODULE.self_check(two_missing)

    no_missing = MODULE.rule_mirror(valid)
    assert MODULE.self_check(no_missing)

    mixed_color = copy.deepcopy(valid)
    changed = False
    for r, row in enumerate(mixed_color):
        for c, value in enumerate(row):
            if value == facts["foreground_color"]:
                mixed_color[r][c] = next(color for color in MODULE._COLORS if color != value)
                changed = True
                break
        if changed:
            break
    assert MODULE.self_check(mixed_color)

    filled_index = facts["filled_indices"][0]
    local = facts["quadrant_cells"][filled_index]
    shifted = _replace_quadrant(
        valid,
        filled_index,
        tuple((r + 1, c + 1) for r, c in local),
        facts["foreground_color"],
    )
    assert MODULE.self_check(shifted)

    wrong_orientation = _replace_quadrant(
        valid,
        filled_index,
        MODULE._orient((filled_index + 1) % 4, facts["canonical_shape"]),
        facts["foreground_color"],
    )
    assert MODULE.self_check(wrong_orientation)

    stray_gray = copy.deepcopy(valid)
    stray_gray[1][q - 1] = 5
    assert MODULE.self_check(stray_gray)


def test_negative_recombination_is_rejected_but_racket_executes() -> None:
    source = _canonical_row()["program_solution"]
    grid = MODULE.generate(
        744,
        5,
        difficulty="hard",
        quad_size=9,
        missing_quadrant="bottom_left",
    )
    facts = MODULE._analyze(grid)
    malformed = copy.deepcopy(grid)
    target_index = facts["filled_indices"][-1]
    origin_r, origin_c = MODULE._quadrant_origins(facts["quad_size"])[target_index]
    local_r, local_c = facts["quadrant_cells"][target_index][-1]
    absent = next(color for color in MODULE._COLORS if color != facts["foreground_color"])
    malformed[origin_r + local_r][origin_c + local_c] = absent
    assert MODULE.self_check(malformed)

    bridge = RacketBridge(max_calls_before_restart=64)
    try:
        result = bridge.eval_text(rule_application(source, malformed))
    finally:
        bridge.shutdown()
    assert isinstance(result, list)
    assert len(result) == len(malformed)
    assert all(len(row) == len(malformed[0]) for row in result)


def test_missing_quadrants_shape_sizes_and_colors_are_balanced() -> None:
    grids = [MODULE.generate(4_000 + i, i, difficulty="medium") for i in range(400)]
    observed = [MODULE.observe_overrides(grid) for grid in grids]
    missing_counts = Counter(item["missing_quadrant"] for item in observed)
    shape_counts = Counter(item["shape_cells"] for item in observed)
    assert set(missing_counts.values()) == {100}
    assert max(shape_counts.values()) - min(shape_counts.values()) <= 2
    assert all(MODULE._analyze(grid)["orientation_count"] == 4 for grid in grids)
