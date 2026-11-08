"""Focused semantic and contract regressions for ARC task 62b74c02."""
from __future__ import annotations

import copy
import importlib
import json
import random
from itertools import product
from pathlib import Path

import pytest

from puzzle_generators import base
from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from scripts.canonical_profile_gate import (
    canonical_pairs,
    canonical_rule_hash,
    canonical_rule_source,
)

GEN = importlib.import_module("puzzle_generators.per_puzzle.a7a7065ca9b4.generator")
ROOT = Path(__file__).resolve().parents[1]
BANDS = ("easy", "medium", "hard")
AUTHORITY_PATHS = (
    ROOT / "data/base/solutions/augmented/62b74c02__67fe3b15193c.json",
    ROOT / "data/base/solutions/training/62b74c02__a7a7065ca9b4.json",
)


def _pair(seed: int, sample_index: int, band: str) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _frozen(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _unchecked_rule(grid: list[list[int]]) -> list[list[int]]:
    """Apply the selected rule mechanically, without distribution validation."""
    height = len(grid)
    width = len(grid[0])
    pattern_width = next(
        (
            col
            for col in range(width)
            if all(grid[row][col] == 0 for row in range(height))
        ),
        width,
    )
    return [
        [
            grid[row][col]
            if col < pattern_width
            else (
                grid[row][col - (width - pattern_width)]
                if col >= width - pattern_width
                else grid[row][0]
            )
            for col in range(width)
        ]
        for row in range(height)
    ]


def test_metadata_rule_hash_and_all_authorities_are_synchronized() -> None:
    selected = canonical_rule_source(GEN.TASK_ID)
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == canonical_rule_hash(GEN.TASK_ID) == "9c55d00ff53c"

    for path in AUTHORITY_PATHS:
        target = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code"] == selected
        assert target["raw_code"] == selected


def test_all_eight_canonical_pairs_are_accepted_exact_and_input_pure() -> None:
    pairs = canonical_pairs(GEN.TASK_ID)
    assert len(pairs) == 8
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_racket_canonical_generated_parity_purity_and_a_b_a() -> None:
    bundle = _load_bundle(GEN.TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        for pair in canonical_pairs(GEN.TASK_ID):
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == pair["output"]
            assert source == before

        generated = [
            GEN.generate(
                710_000 + index,
                index * 17 + 3,
                difficulty=BANDS[index % len(BANDS)],
            )
            for index in range(45)
        ]
        for grid in generated:
            source = copy.deepcopy(grid)
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == GEN.rule_mirror(grid)
            assert source == before

        grid_a, grid_b = generated[7], generated[37]
        a1 = _apply_rule(bridge, fn_name, grid_a)
        b = _apply_rule(bridge, fn_name, grid_b)
        a2 = _apply_rule(bridge, fn_name, grid_a)
        assert a1 == GEN.rule_mirror(grid_a)
        assert b == GEN.rule_mirror(grid_b)
        assert a2 == a1
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("difficulty", BANDS)
def test_every_boundary_axis_combination_round_trips(difficulty: str) -> None:
    values = {
        "grid_h": (3, 12),
        "grid_w": (10, 18),
        "pattern_w": (3, 4),
        "palette_size": (2, 6),
        "pattern_mode": GEN.PATTERN_MODES,
    }
    names = tuple(values)
    for index, combination in enumerate(product(*(values[name] for name in names))):
        requested = dict(zip(names, combination))
        grid = GEN.generate(
            820_000 + index,
            73,
            difficulty=difficulty,
            **requested,
        )
        assert GEN.self_check(grid, meta={"overrides": requested}) == []
        assert GEN.observe_overrides(grid) == requested


def test_invalid_overrides_and_difficulty_fail_loudly() -> None:
    bad_calls = (
        {"difficulty": "expert"},
        {"unknown_texture": "silently-ignored-before-repair"},
        {"grid_h": 2},
        {"grid_h": 13},
        {"grid_w": 9},
        {"grid_w": 19},
        {"pattern_w": 2},
        {"pattern_w": 5},
        {"palette_size": 1},
        {"palette_size": 7},
        {"grid_h": True},
        {"pattern_mode": "full_pattern"},
    )
    for kwargs in bad_calls:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 1, **kwargs)


def test_default_keyed_provenance_matches_every_observable_axis() -> None:
    for band in BANDS:
        for index in range(36):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(830_000 + index, index, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            observed = GEN.observe_overrides(grid)
            assert set(observed) == set(GEN.AXES)
            for axis in GEN.AXES:
                assert captured[0].axis_value(axis) == observed[axis]


@pytest.mark.parametrize("start", range(24))
@pytest.mark.parametrize("band", BANDS)
def test_every_sliding_four_demo_window_identifies_the_rule(start: int, band: str) -> None:
    demos = [_pair(910_001, index, band) for index in range(start, start + 4)]
    query = _pair(910_001, start + 4, band)
    assert GEN.lesson_identifiable(demos, query) == []

    observed = [GEN.observe_overrides(demo["input"]) for demo in demos]
    assert {item["pattern_mode"] for item in observed} == set(GEN.PATTERN_MODES)
    assert {item["pattern_w"] for item in observed} == {3, 4}
    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_canonical_shortcuts_fit_canonical_but_generated_witnesses_kill_them() -> None:
    pairs = canonical_pairs(GEN.TASK_ID)
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    mismatch = GEN.generate(
        920_001,
        1,
        difficulty="medium",
        pattern_mode="edge_mismatch_dense",
    )
    sparse = GEN.generate(
        920_002,
        2,
        difficulty="medium",
        pattern_mode="sparse_holes",
    )
    assert GEN._edge_matched_only_copy(mismatch) != GEN.rule_mirror(mismatch)
    assert GEN._nonzero_overlay(sparse) != GEN.rule_mirror(sparse)


def test_strict_census_has_full_mode_width_and_profile_support() -> None:
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), GEN._analyze(pair["input"])["pattern_w"])
        for pair in canonical_pairs(GEN.TASK_ID)
    }
    for band_index, band in enumerate(BANDS):
        modes = set()
        widths = set()
        profiles = set()
        inputs = set()
        outputs = set()
        for index in range(200):
            grid = GEN.generate(1_000_000 + band_index * 10_000 + index, index, difficulty=band)
            output = GEN.rule_mirror(grid)
            observed = GEN.observe_overrides(grid)
            assert GEN.strict_canonical_like(grid) == []
            assert output != grid
            modes.add(observed["pattern_mode"])
            widths.add(observed["pattern_w"])
            profiles.add((observed["grid_h"], observed["grid_w"], observed["pattern_w"]))
            inputs.add(_frozen(grid))
            outputs.add(_frozen(output))
        assert modes == set(GEN.PATTERN_MODES)
        assert widths == {3, 4}
        assert canonical_profiles <= profiles
        assert len(inputs) == 200
        assert len(outputs) >= 198


def test_targeted_structural_impostors_are_rejected() -> None:
    valid = GEN.generate(
        404,
        7,
        difficulty="medium",
        grid_h=5,
        grid_w=12,
        pattern_w=4,
        palette_size=4,
        pattern_mode="edge_mismatch_dense",
    )
    pw = GEN.observe_overrides(valid)["pattern_w"]

    right_nonzero = copy.deepcopy(valid)
    right_nonzero[0][-1] = right_nonzero[0][0]
    assert any("right must be background" in error for error in GEN.self_check(right_nonzero))

    zero_first = copy.deepcopy(valid)
    zero_first[0][0] = 0
    assert any("column 0" in error for error in GEN.self_check(zero_first))

    no_contrast = copy.deepcopy(valid)
    for row in range(len(no_contrast)):
        for col in range(1, pw):
            no_contrast[row][col] = no_contrast[row][0]
    assert any("different from its row fill" in error for error in GEN.self_check(no_contrast))

    too_narrow = [row[: 2 * pw + 1] for row in valid]
    assert any("two middle columns" in error for error in GEN.self_check(too_narrow))

    shifted_divider = copy.deepcopy(valid)
    for row in range(len(shifted_divider)):
        shifted_divider[row][pw] = shifted_divider[row][0]
    assert any("divider must be column 3 or 4" in error for error in GEN.self_check(shifted_divider))

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    assert GEN.self_check(ragged) == ["grid must be rectangular"]


def test_negative_recombination_is_distribution_invalid_but_racket_executable() -> None:
    grid = GEN.generate(909, 5, difficulty="hard", pattern_mode="sparse_holes")
    recombined = copy.deepcopy(grid)
    recombined[0][-1] = recombined[0][0]
    assert any("right must be background" in error for error in GEN.self_check(recombined))

    bundle = _load_bundle(GEN.TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        output = _apply_rule(bridge, fn_name, recombined)
        assert output == _unchecked_rule(recombined)
    finally:
        bridge.shutdown()


def test_determinism_fresh_returns_and_process_global_rng_isolation() -> None:
    random.seed(8128)
    state = random.getstate()
    kwargs = {
        "difficulty": "hard",
        "grid_h": 12,
        "grid_w": 18,
        "pattern_w": 4,
        "palette_size": 6,
        "pattern_mode": "sparse_holes",
    }
    first = GEN.generate(444, 19, **kwargs)
    assert random.getstate() == state
    second = GEN.generate(444, 19, **kwargs)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(444, 19, **kwargs) == second


def test_four_is_the_smallest_schedule_wide_identifiable_demo_count() -> None:
    for band in BANDS:
        for start in range(32):
            demos = [_pair(930_001, index, band) for index in range(start, start + 4)]
            query = _pair(930_001, start + 4, band)
            assert GEN.lesson_identifiable(demos, query) == []

    # The window beginning at residue 3 contains mismatch, matched, mismatch;
    # it has no copied-zero witness, so nonzero-overlay survives and changes
    # the sparse query at residue 2.
    demos = [_pair(930_001, index, "easy") for index in range(3, 6)]
    query = _pair(930_001, 6, "easy")
    assert GEN.lesson_identifiable(demos, query) == [
        "competing rule 'nonzero_overlay' matches every demo yet answers the query differently"
    ]
