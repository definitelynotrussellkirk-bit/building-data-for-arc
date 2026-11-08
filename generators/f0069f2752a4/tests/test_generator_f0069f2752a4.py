from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.base import set_ctx_observer
from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from src.core.canonical_pairs import load_task_pairs

TASK_ID = "f0069f2752a4"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.f0069f2752a4.generator"
)
AUTHORITY = ROOT / (
    "data/base/solutions/banks/647beeb937e1/"
    "S9_E4__f0069f2752a4.json"
)


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_metadata_and_normalized_rule_hash_are_pinned():
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "4.0.0"
    assert GEN.RULE_HASH == "9502d1357bdc"

    record = json.loads(AUTHORITY.read_text())
    assert _normalized_hash(record["racket_target"]["target_code"]) == GEN.RULE_HASH
    canonical = next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    assert _normalized_hash(canonical["program_solution"]) == GEN.RULE_HASH


def test_all_canonical_pairs_are_owned_exact_and_input_pure():
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_racket_exactness_generated_parity_and_a_b_a_repeat():
    pairs = load_task_pairs(TASK_ID)
    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == pair["output"]
            assert source == before

        generated = [
            GEN.generate(7000 + i, i * 17 + 3, difficulty=("easy", "medium", "hard")[i % 3])
            for i in range(40)
        ]
        for grid in generated:
            source = copy.deepcopy(grid)
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == GEN.rule_mirror(grid)
            assert source == before

        grid_a, grid_b = generated[3], generated[29]
        out_a1 = _apply_rule(bridge, fn_name, grid_a)
        out_b = _apply_rule(bridge, fn_name, grid_b)
        out_a2 = _apply_rule(bridge, fn_name, grid_a)
        assert out_a1 == GEN.rule_mirror(grid_a)
        assert out_b == GEN.rule_mirror(grid_b)
        assert out_a2 == out_a1
    finally:
        bridge.shutdown()


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 8, "grid_w": 8, "n_border": 1, "n_interior": 1, "palette_kind": "default"},
        {"grid_h": 18, "grid_w": 18, "n_border": 4, "n_interior": 4, "palette_kind": "warm"},
        {"grid_h": 8, "grid_w": 18, "n_border": 4, "n_interior": 4, "palette_kind": "cool"},
        {"grid_h": 18, "grid_w": 8, "n_border": 4, "n_interior": 4, "palette_kind": "varied"},
    ],
)
def test_full_valid_boundary_overrides_are_exact(overrides):
    grid = GEN.generate(1201, 73, difficulty="hard", **overrides)
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.self_check(grid, meta={"overrides": overrides}) == []


def test_unknown_and_out_of_range_overrides_fail_loudly():
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 1, texture="warm")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 1, grid_h=7)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 1, n_border=5)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 1, palette_kind="neon")


def test_determinism_fresh_returns_and_process_global_rng_isolation():
    random.seed(8128)
    state = random.getstate()
    first = GEN.generate(444, 19, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(444, 19, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(444, 19, difficulty="medium") == second


def test_default_keyed_provenance_matches_every_observable_axis():
    for band in ("easy", "medium", "hard"):
        for index in range(12):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(55_000 + index, index * 13 + 2, difficulty=band)
            finally:
                set_ctx_observer(None)
            assert len(captured) == 1
            observed = GEN.observe_overrides(grid)
            assert set(observed) == set(GEN.AXES)
            for axis in GEN.AXES:
                assert captured[0].axis_value(axis) == observed[axis]


def test_strict_semantic_census_and_disjoint_seed_stability():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        rates = []
        for cohort in range(2):
            strict = 0
            unique = set()
            witness_counts = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
            for index in range(200):
                seed = 100_000 * (cohort + 1) + 10_000 * band_index + index
                grid = GEN.generate(seed, index * 31 + cohort, difficulty=band)
                assert GEN.self_check(grid) == []
                assert GEN.rule_mirror(grid) != grid
                strict += GEN.strict_canonical_like(grid) == []
                unique.add(_frozen(grid))
                for name, witness in GEN.SEMANTIC_WITNESSES.items():
                    witness_counts[name] += bool(witness(grid))
            assert strict >= 40
            assert len(unique) == 200
            assert all(count > 0 for count in witness_counts.values())
            rates.append(strict / 200)
        assert abs(rates[0] - rates[1]) <= 0.12


def test_consecutive_lessons_identify_border_contact_not_color_or_shape():
    for seed in range(30):
        pairs = [
            _pair(GEN.generate(seed + 3000, index, difficulty="medium"))
            for index in range(4)
        ]
        assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_self_check_rejects_targeted_structural_impostors():
    valid = GEN.generate(
        404,
        7,
        difficulty="medium",
        grid_h=10,
        grid_w=10,
        n_border=2,
        n_interior=2,
        palette_kind="default",
    )
    info = GEN._analysis(valid)

    all_background = [[0 for _ in row] for row in valid]
    errors = GEN.self_check(all_background)
    assert any("border-touching" in error for error in errors)
    assert any("strictly interior" in error for error in errors)

    only_border = copy.deepcopy(valid)
    for component in info["interior"]:
        for row, col in component["cells"]:
            only_border[row][col] = 0
    assert any("strictly interior" in error for error in GEN.self_check(only_border))

    only_interior = copy.deepcopy(valid)
    for component in info["border"]:
        for row, col in component["cells"]:
            only_interior[row][col] = 0
    assert any("border-touching" in error for error in GEN.self_check(only_interior))

    bridged = [[0 for _ in range(8)] for _ in range(8)]
    bridged[0][1] = 2
    bridged[3][4] = 6
    bridged[3][5] = 6
    assert GEN.self_check(bridged) == []
    for rr in range(4):
        bridged[rr][4] = 6
    assert any("strictly interior" in error for error in GEN.self_check(bridged))

    adjacent = copy.deepcopy(valid)
    occupied = {(r, c) for r, values in enumerate(adjacent) for c, value in enumerate(values) if value}
    placed = False
    for r, c in sorted(occupied):
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < len(adjacent) and 0 <= cc < len(adjacent[0]) and adjacent[rr][cc] == 0:
                adjacent[rr][cc] = 9 if adjacent[r][c] != 9 else 8
                placed = True
                break
        if placed:
            break
    assert placed
    assert any("orthogonally adjacent" in error for error in GEN.self_check(adjacent))

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    assert any("rectangular" in error for error in GEN.self_check(ragged))


def test_negative_recombination_is_distribution_invalid_but_oracle_executable():
    grid = GEN.generate(909, 5, difficulty="hard")
    info = GEN._analysis(grid)
    interior_only = copy.deepcopy(grid)
    for component in info["border"]:
        for row, col in component["cells"]:
            interior_only[row][col] = 0

    # Border contact — the feature that licenses survival — is absent from
    # every remaining object. The task oracle is still total, but the lesson
    # distribution correctly rejects this one-role recombination.
    assert all(not component["touches_border"] for component in GEN._components(interior_only))
    assert any("border-touching" in error for error in GEN.self_check(interior_only))

    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        assert _apply_rule(bridge, fn_name, interior_only) == GEN.rule_mirror(interior_only)
    finally:
        bridge.shutdown()
