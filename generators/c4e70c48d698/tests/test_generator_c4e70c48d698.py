from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
import statistics
import time
from collections import Counter, deque
from pathlib import Path

import pytest

from puzzle_generators.base import set_ctx_observer
from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from src.core.canonical_pairs import load_task_pairs

TASK_ID = "c4e70c48d698"
ROOT = Path(__file__).resolve().parents[1]
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.c4e70c48d698.generator"
)
AUTHORITY = ROOT / "data/base/solutions/banks/3a1815be7c2e/S12_H4__c4e70c48d698.json"


def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_metadata_rule_hash_and_selected_authorities_are_pinned():
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "a99ffbd8452c"

    record = json.loads(AUTHORITY.read_text())
    assert _normalized_hash(record["racket_target"]["target_code"]) == GEN.RULE_HASH
    canonical = next(
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )
    assert _normalized_hash(canonical["program_solution"]) == GEN.RULE_HASH


def test_all_canonical_pairs_are_accepted_exact_and_input_pure():
    pairs = load_task_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


@pytest.mark.parametrize("profile", GEN.SCENE_PROFILES)
def test_every_scene_profile_override_is_exact_and_observable(profile):
    for band in ("easy", "medium", "hard"):
        grid = GEN.generate(1201, 73, difficulty=band, scene_profile=profile)
        assert GEN.observe_overrides(grid) == {"scene_profile": profile}
        assert GEN.self_check(grid, meta={"scene_profile": profile}) == []
        assert GEN.strict_canonical_like(grid) == []


def test_unknown_and_invalid_overrides_fail_loudly():
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 1, texture="u_path_7")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 1, scene_profile="straight_line")


def test_determinism_fresh_returns_global_rng_and_default_provenance():
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

    for band in ("easy", "medium", "hard"):
        for index in range(18):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(55_000 + index, index * 13 + 2, difficulty=band)
            finally:
                set_ctx_observer(None)
            assert len(captured) == 1
            observed = GEN.observe_overrides(grid)
            assert observed == {
                "scene_profile": captured[0].axis_value("scene_profile")
            }


def test_canonical_profile_anchor_hits_all_real_dimension_palette_profiles():
    expected = {(9, 12, 6), (10, 13, 7), (10, 14, 8)}
    observed = Counter()
    for index in range(180):
        grid = GEN.generate(900_000 + index, index, difficulty="medium")
        profile = (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        if profile in expected:
            observed[profile] += 1
    assert set(observed) == expected
    assert min(observed.values()) >= 10


def test_strict_semantic_census_200_per_band_and_disjoint_stability():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        cohort_unique = []
        for cohort in range(2):
            strict = 0
            unique = set()
            profile_counts = Counter()
            witness_counts = Counter()
            rival_differences = Counter()
            for index in range(200):
                seed = 1_000_000 * (cohort + 1) + 10_000 * band_index + index
                sample_index = index * 31 + cohort
                grid = GEN.generate(seed, sample_index, difficulty=band)
                assert GEN.self_check(grid) == []
                strict += GEN.strict_canonical_like(grid) == []
                unique.add(_frozen(grid))
                profile_counts[GEN.observe_overrides(grid)["scene_profile"]] += 1
                official = GEN.rule_mirror(grid)
                assert official != grid
                for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                    witness_counts[name] += bool(predicate(grid))
                for name, rival in GEN.SEMANTIC_RIVALS.items():
                    rival_differences[name] += rival(grid) != official
            assert strict == 200
            assert len(unique) == 200
            assert set(profile_counts) == set(GEN.SCENE_PROFILES)
            assert all(count > 0 for count in witness_counts.values())
            assert all(count == 200 for count in rival_differences.values())
            cohort_unique.append(unique)
        # Disjoint seeds/sample indices should not collapse to a fixed template.
        assert len(cohort_unique[0] & cohort_unique[1]) == 0


def test_consecutive_lessons_refute_every_named_competitor():
    for band in ("easy", "medium", "hard"):
        for seed in range(30):
            pairs = [
                _pair(GEN.generate(seed + 3000, index, difficulty=band))
                for index in range(4)
            ]
            assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
            for competitor in GEN.LESSON_COMPETITORS.values():
                assert any(
                    competitor(pair["input"]) != pair["output"]
                    for pair in pairs[:3]
                )


def test_self_check_rejects_targeted_structural_impostors():
    valid = GEN.generate(
        404,
        7,
        difficulty="medium",
        scene_profile="double_branch_9",
    )
    analysis = GEN._analysis(valid)

    no_seed = copy.deepcopy(valid)
    for r, c in analysis["components"][analysis["seeds"][0]]["cells"]:
        no_seed[r][c] = 9
    assert any("exactly one" in error for error in GEN.self_check(no_seed))

    extra_seed = copy.deepcopy(valid)
    detached_index = min(analysis["disconnected"])
    for r, c in analysis["components"][detached_index]["cells"]:
        extra_seed[r][c] = 1
    assert any("exactly one" in error for error in GEN.self_check(extra_seed))

    no_detached = copy.deepcopy(valid)
    for index in analysis["disconnected"]:
        for r, c in analysis["components"][index]["cells"]:
            no_detached[r][c] = 0
    assert any("detached" in error for error in GEN.self_check(no_detached))

    no_far_layer = copy.deepcopy(valid)
    for index, distance in analysis["distances"].items():
        if distance >= 3:
            for r, c in analysis["components"][index]["cells"]:
                no_far_layer[r][c] = 0
    assert any("distance-3" in error for error in GEN.self_check(no_far_layer))

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    assert any("rectangular" in error for error in GEN.self_check(ragged))


def test_negative_recombination_is_distribution_invalid_but_oracle_total():
    grid = GEN.generate(909, 5, difficulty="easy", scene_profile="u_path_7")
    analysis = GEN._analysis(grid)
    assert len(analysis["disconnected"]) == 1
    assert all(2 not in row for row in grid)

    reachable_cells = {
        cell for index in analysis["reachable"]
        for cell in analysis["components"][index]["cells"]
    }
    detached_cells = {
        cell for index in analysis["disconnected"]
        for cell in analysis["components"][index]["cells"]
    }
    h, w = len(grid), len(grid[0])
    starts = {
        (r + dr, c + dc)
        for r, c in reachable_cells for dr, dc in GEN._DIR4
        if 0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 0
    }
    goals = {
        (r + dr, c + dc)
        for r, c in detached_cells for dr, dc in GEN._DIR4
        if 0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 0
    }
    queue = deque(starts)
    parent = {cell: None for cell in starts}
    endpoint = None
    while queue and endpoint is None:
        cell = queue.popleft()
        if cell in goals:
            endpoint = cell
            break
        r, c = cell
        for dr, dc in GEN._DIR4:
            nxt = (r + dr, c + dc)
            if (0 <= nxt[0] < h and 0 <= nxt[1] < w
                    and nxt not in parent and grid[nxt[0]][nxt[1]] == 0):
                parent[nxt] = cell
                queue.append(nxt)
    assert endpoint is not None

    bridged = copy.deepcopy(grid)
    cursor = endpoint
    while cursor is not None:
        bridged[cursor[0]][cursor[1]] = 2
        cursor = parent[cursor]

    # The replacement feature is a color-2 bridge, absent from every remaining
    # scene part. It absorbs the sole detached object into the seed graph.
    assert not GEN._analysis(bridged)["disconnected"]
    assert any("detached" in error for error in GEN.self_check(bridged))

    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        assert _apply_rule(bridge, fn_name, bridged) == GEN.rule_mirror(bridged)
    finally:
        bridge.shutdown()


def test_racket_exactness_40_generated_input_purity_a_b_a_and_latency():
    pairs = load_task_pairs(TASK_ID)
    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    latencies = []
    restarts = 0
    try:
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            started = time.perf_counter()
            assert _apply_rule(bridge, fn_name, source) == pair["output"]
            latencies.append((time.perf_counter() - started) * 1000.0)
            assert source == before

        generated = [
            GEN.generate(
                7000 + index,
                index * 17 + 3,
                difficulty=("easy", "medium", "hard")[index % 3],
            )
            for index in range(40)
        ]
        for grid in generated:
            source = copy.deepcopy(grid)
            before = copy.deepcopy(source)
            started = time.perf_counter()
            assert _apply_rule(bridge, fn_name, source) == GEN.rule_mirror(grid)
            latencies.append((time.perf_counter() - started) * 1000.0)
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

    assert len(latencies) == 43
    p95 = statistics.quantiles(latencies, n=20, method="inclusive")[18]
    assert p95 < 5000.0
    assert restarts == 0
