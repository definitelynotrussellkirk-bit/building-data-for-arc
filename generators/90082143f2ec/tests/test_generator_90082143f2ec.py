"""Focused regressions for canonical noisy-band generator 90082143f2ec."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid

ROOT = find_root(__file__)
DATA_ROOT = canonical_path(ROOT).parent.parent
TASK = "90082143f2ec"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")
AUTHORITY_PATHS = (
    DATA_ROOT / "base/solutions/augmented/e26a3af2__85b43dce29a8.json",
    DATA_ROOT / "base/solutions/training/e26a3af2__90082143f2ec.json",
)


def _canonical_rows() -> list[dict]:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK:
                    rows.append(row)
    assert rows, f"missing canonical rows for {TASK}"
    return rows


def _canonical_pairs() -> list[dict]:
    return canonical_pairs(TASK, root=ROOT)


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_rule_hash_and_all_task_local_authorities_are_exactly_synchronized():
    source = _canonical_rows()[0]["program_solution"]
    normalized = " ".join(source.split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH
    assert GEN.RULE_HASH == "a86d1f36d1d2"
    for path in AUTHORITY_PATHS:
        base = json.loads(path.read_text())
        target = base["racket_target"]
        assert target["target_code"] == source
        assert hashlib.sha256(target["raw_code"].encode()).hexdigest() == (
            "8e980dd15265004ac344da8fb01424ea641bc738edc8083d904f541e3f98cdd6"
        )  # Archived source is preserved; only selected target_code is synchronized.
        assert target["canonicalization_status"] == "canonical_exact_sync"


def test_all_eight_canonical_inputs_are_accepted_and_outputs_match():
    pairs = _canonical_pairs()
    assert len(pairs) == 8
    # Both canonical variants are retained in the portable ledger; all eight
    # labeled inputs are checked rather than relying on a private deduplicator.
    for pair in pairs:
        grid = normalize_grid(pair["input"])
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == normalize_grid(pair["output"])
        assert grid == snapshot


def test_eight_slot_schedule_decouples_shape_from_axis_and_every_three_demo_window_identifies_rule():
    expected = [
        (13, 14, "vertical", 3, "moderate"),
        (13, 14, "horizontal", 4, "high"),
        (15, 14, "horizontal", 5, "moderate"),
        (15, 14, "vertical", 3, "high"),
        (13, 17, "vertical", 4, "moderate"),
        (13, 17, "horizontal", 5, "high"),
        (15, 15, "horizontal", 3, "moderate"),
        (15, 15, "vertical", 4, "high"),
    ]
    assert GEN.LESSON_SCHEDULE_PERIOD == len(expected)
    assert "shape_axis_shortcut" in GEN.LESSON_COMPETITORS

    for difficulty in ("easy", "medium", "hard"):
        observed = []
        for index in range(GEN.LESSON_SCHEDULE_PERIOD):
            grid = GEN.generate(20260725, index, difficulty=difficulty)
            axes = GEN.observe_overrides(grid)
            observed.append(
                (
                    axes["grid_h"], axes["grid_w"], axes["orientation"],
                    axes["band_count"], axes["noise_level"],
                )
            )
        assert observed == expected

        by_shape = {}
        for h, w, orientation, _bands, _noise in observed:
            by_shape.setdefault((h, w), set()).add(orientation)
        assert by_shape == {
            (13, 14): {"vertical", "horizontal"},
            (13, 17): {"vertical", "horizontal"},
            (15, 14): {"vertical", "horizontal"},
            (15, 15): {"vertical", "horizontal"},
        }

        for start in range(GEN.LESSON_SCHEDULE_PERIOD):
            grids = [GEN.generate(719, start + i, difficulty=difficulty) for i in range(4)]
            labeled = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]
            for query_index in range(4):
                demos = [pair for i, pair in enumerate(labeled) if i != query_index]
                query = labeled[query_index]
                assert GEN.lesson_identifiable(demos, query) == []
                assert any(
                    GEN.LESSON_COMPETITORS["shape_axis_shortcut"](demo["input"])
                    != demo["output"]
                    for demo in demos
                )


def test_every_override_boundary_is_exact_observable_and_composable():
    cases = [
        {"grid_h": 13}, {"grid_h": 15},
        {"grid_w": 14}, {"grid_w": 17},
        {"orientation": "vertical"}, {"orientation": "horizontal"},
        {"band_count": 3}, {"band_count": 5},
        {"noise_level": "moderate"}, {"noise_level": "high"},
        {
            "grid_h": 14, "grid_w": 16, "orientation": "horizontal",
            "band_count": 5, "noise_level": "high",
        },
        {
            "grid_h": 15, "grid_w": 17, "orientation": "vertical",
            "band_count": 3, "noise_level": "moderate",
        },
    ]
    for difficulty in ("easy", "medium", "hard"):
        for case in cases:
            grid = GEN.generate(73, 13, difficulty=difficulty, **case)
            assert GEN.self_check(grid) == []
            observed = GEN.observe_overrides(grid)
            for key, value in case.items():
                assert observed[key] == value, (difficulty, case, observed)


def test_invalid_controls_fail_closed():
    bad_cases = (
        {"grid_h": 12}, {"grid_h": 16},
        {"grid_w": 13}, {"grid_w": 18},
        {"orientation": "diagonal"},
        {"band_count": 2}, {"band_count": 6},
        {"noise_level": "none"},
        {"invented_axis": 1},
    )
    for case in bad_cases:
        with pytest.raises(ValueError):
            GEN.generate(0, 0, difficulty="medium", **case)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(0, 0, difficulty="extreme")


def test_determinism_fresh_returns_mutation_safety_and_global_rng_purity():
    random.seed(987654321)
    global_state = random.getstate()
    first = GEN.generate(111, 222, difficulty="hard")
    assert random.getstate() == global_state
    second = GEN.generate(111, 222, difficulty="hard")
    assert random.getstate() == global_state
    assert first == second
    assert first is not second and all(a is not b for a, b in zip(first, second))
    frozen = _frozen(second)
    first[0][0] = 0
    assert _frozen(GEN.generate(111, 222, difficulty="hard")) == frozen

    by_seed = {_frozen(GEN.generate(seed, 17, difficulty="medium")) for seed in range(30)}
    by_index = {_frozen(GEN.generate(17, index, difficulty="medium")) for index in range(30)}
    assert len(by_seed) >= 28
    assert len(by_index) >= 28


def test_named_mutation_fixtures_are_all_rejected_without_mutation():
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        snapshot = copy.deepcopy(grid)
        assert GEN.self_check(grid), name
        assert grid == snapshot


def test_negative_recombination_rejected_while_racket_oracle_executes():
    valid = GEN.generate(551, 0, difficulty="medium")
    # Remove every noisy replacement, so the decisive replacement feature
    # (noise) is absent from every remaining scene part.  This is executable
    # by the total Racket rule but intentionally outside the teaching grammar.
    recombined = GEN.rule_mirror(valid)
    assert GEN.self_check(recombined)

    bundle = _load_bundle(TASK)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        snapshot = copy.deepcopy(recombined)
        output = _apply_rule(bridge, fn_name, recombined)
    finally:
        bridge.shutdown()
    assert recombined == snapshot
    assert output == recombined


def test_600_draw_linked_semantic_census_and_disjoint_stability():
    expected_profiles = {
        (13, 14, "vertical", 3, "moderate"),
        (13, 14, "horizontal", 4, "high"),
        (15, 14, "horizontal", 5, "moderate"),
        (15, 14, "vertical", 3, "high"),
        (13, 17, "vertical", 4, "moderate"),
        (13, 17, "horizontal", 5, "high"),
        (15, 15, "horizontal", 3, "moderate"),
        (15, 15, "vertical", 4, "high"),
    }
    for difficulty in ("easy", "medium", "hard"):
        grids = [
            GEN.generate(seed, index, difficulty=difficulty)
            for index, seed in enumerate(range(1000, 1200))
        ]
        assert all(GEN.strict_canonical_like(grid) == [] for grid in grids)
        profiles = Counter(
            (
                axes["grid_h"], axes["grid_w"], axes["orientation"],
                axes["band_count"], axes["noise_level"],
            )
            for axes in map(GEN.observe_overrides, grids)
        )
        assert set(profiles) == expected_profiles
        assert min(profiles.values()) >= 20
        assert all(GEN.rule_mirror(grid) != grid for grid in grids)
        assert len({_frozen(grid) for grid in grids}) >= 195

        stable = [
            GEN.generate(50_000 + seed, 90_000 + index, difficulty=difficulty)
            for index, seed in enumerate(range(200))
        ]
        assert all(GEN.strict_canonical_like(grid) == [] for grid in stable)
        assert len({_frozen(grid) for grid in stable}) >= 195
