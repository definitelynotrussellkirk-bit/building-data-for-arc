from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators import base
from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash, canonical_rule_source


TASK_ID = "f3acfc6e19e1"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = (
    ROOT
    / "data/base/solutions/banks/a54e1d9e1d4b"
    / "hard_j20__f3acfc6e19e1.json"
)
BANDS = ("easy", "medium", "hard")


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_rule_pin_selected_authorities_and_canonical_pairs_are_exact():
    source = canonical_rule_source(TASK_ID)
    authority = json.loads(AUTHORITY.read_text())["racket_target"]

    assert GEN.GENERATOR_ID == GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "4.0.0"
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "708e3724b016"
    assert authority["target_code"] == source
    assert authority["raw_code"] == source

    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        source_grid = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source_grid)
        assert GEN.self_check(source_grid) == []
        assert GEN.strict_canonical_like(source_grid) == []
        assert GEN.rule_mirror(source_grid) == pair["output"]
        assert source_grid == before


def test_racket_parity_input_purity_and_reentrant_a_b_a():
    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        for pair in canonical_pairs(TASK_ID):
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == pair["output"]
            assert source == before

        generated = [
            GEN.generate(
                70_000 + index,
                index * 17 + 3,
                difficulty=BANDS[index % len(BANDS)],
            )
            for index in range(24)
        ]
        for grid in generated:
            source = copy.deepcopy(grid)
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == GEN.rule_mirror(grid)
            assert source == before

        grid_a, grid_b = generated[5], generated[19]
        first_a = _apply_rule(bridge, fn_name, grid_a)
        middle_b = _apply_rule(bridge, fn_name, grid_b)
        second_a = _apply_rule(bridge, fn_name, grid_a)
        assert first_a == GEN.rule_mirror(grid_a)
        assert middle_b == GEN.rule_mirror(grid_b)
        assert second_a == first_a
    finally:
        bridge.shutdown()


@pytest.mark.parametrize("difficulty", BANDS)
def test_every_declared_axis_boundary_is_exact_and_observable(difficulty):
    cases = {
        "grid_h": (8, 12),
        "grid_w": (10, 14),
        "code_profile": GEN.CODE_PROFILE_NAMES,
        "motif_profile": GEN.MOTIF_PROFILE_NAMES,
        "motif_color": (1, 9),
        "placement_profile": GEN.PLACEMENT_PROFILES,
        "decoy_profile": GEN.DECOY_PROFILES,
    }
    base_overrides = {
        "grid_h": 10,
        "grid_w": 12,
        "code_profile": "cw_180_transpose",
        "motif_profile": "f_pentomino",
        "motif_color": 8,
        "placement_profile": "lower_right",
        "decoy_profile": "two_small",
    }
    for axis, values in cases.items():
        for value in values:
            overrides = {**base_overrides, axis: value}
            grid = GEN.generate(12_345, 73, difficulty=difficulty, **overrides)
            assert GEN.self_check(grid, difficulty=difficulty) == []
            assert GEN.observe_overrides(grid) == overrides


def test_default_keyed_provenance_matches_every_observable_axis():
    for band_index, band in enumerate(BANDS):
        for index in range(24):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(
                    80_000 + band_index * 1_000 + index,
                    index * 19 + 5,
                    difficulty=band,
                )
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            observed = GEN.observe_overrides(grid)
            assert set(observed) == set(GEN.AXES)
            assert {
                axis: captured[0].axis_value(axis) for axis in GEN.AXES
            } == observed


def test_invalid_overrides_and_difficulty_fail_loudly():
    invalid_calls = (
        {"difficulty": "expert"},
        {"texture": "noise"},
        {"grid_h": 7},
        {"grid_h": 13},
        {"grid_w": 9},
        {"grid_w": 15},
        {"grid_h": True},
        {"code_profile": "unknown"},
        {"motif_profile": "square"},
        {"motif_color": 0},
        {"motif_color": 10},
        {"placement_profile": "center"},
        {"decoy_profile": "many"},
    )
    for kwargs in invalid_calls:
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(1, 1, **kwargs)


def test_motif_families_are_distinct_and_fully_asymmetric():
    signatures = set()
    for cells in GEN.MOTIF_PROFILES.values():
        orbit = {GEN._transform_cells(cells, transform) for transform in range(8)}
        assert len(orbit) == 8
        signatures.add(GEN._shape_signature(cells))
    assert len(signatures) == len(GEN.MOTIF_PROFILES)


def test_every_sliding_three_demo_window_refutes_all_named_competitors():
    assert GEN.EXAMPLES_NEEDED == 3
    for band_index, band in enumerate(BANDS):
        for seed in range(12):
            for start in range(8):
                demos = [
                    _pair(
                        GEN.generate(
                            200_000 + band_index * 10_000 + seed,
                            start + offset,
                            difficulty=band,
                        )
                    )
                    for offset in range(GEN.EXAMPLES_NEEDED)
                ]
                query = _pair(
                    GEN.generate(
                        200_000 + band_index * 10_000 + seed,
                        start + GEN.EXAMPLES_NEEDED,
                        difficulty=band,
                    )
                )
                assert GEN.lesson_identifiable(demos, query) == []
                keys = {
                    value
                    for pair in demos
                    for value in pair["input"][0]
                    if value != 0
                }
                assert keys == set(GEN.CODES)
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        rival(pair["input"]) != pair["output"] for pair in demos
                    ), name


def test_two_demo_windows_are_not_claimed_identifiable():
    # Starts 1 and 3 are the deliberate lower bound: each misses one key.
    for start, missing in ((1, 3), (3, 5)):
        demos = [
            _pair(GEN.generate(333, start + offset, difficulty="medium"))
            for offset in range(2)
        ]
        query = _pair(GEN.generate(333, start + 2, difficulty="medium"))
        reasons = GEN.lesson_identifiable(demos, query)
        assert any("need at least 3" in reason for reason in reasons)
        assert any(str(missing) in reason for reason in reasons)


def test_self_check_rejects_targeted_structural_impostors():
    valid = GEN.generate(
        404,
        7,
        difficulty="hard",
        grid_h=12,
        grid_w=14,
        code_profile="cw_180_transpose",
        motif_profile="l_tetromino",
        motif_color=6,
        placement_profile="upper_left",
        decoy_profile="none",
    )
    assert GEN.self_check(valid) == []

    contaminated_separator = copy.deepcopy(valid)
    contaminated_separator[1][0] = 9
    assert any("blank separator" in error for error in GEN.self_check(contaminated_separator))

    gapped_keys = copy.deepcopy(valid)
    gapped_keys[0][4] = gapped_keys[0][1]
    gapped_keys[0][1] = 0
    assert any("contiguous" in error for error in GEN.self_check(gapped_keys))

    unknown_key = copy.deepcopy(valid)
    unknown_key[0][0] = 9
    assert any("{2,3,4,5}" in error for error in GEN.self_check(unknown_key))

    tied_largest = copy.deepcopy(valid)
    tie_color = 8
    for row, col in ((9, 10), (9, 11), (10, 10), (10, 11)):
        tied_largest[row][col] = tie_color
    assert any("unique largest" in error for error in GEN.self_check(tied_largest))

    contaminating_bbox = copy.deepcopy(valid)
    info, errors = GEN._analyse(contaminating_bbox)
    assert errors == []
    r0, c0, r1, c1 = info["target_bbox"]
    target_cells = set(info["target"]["cells"])
    hole = next(
        (row, col)
        for row in range(r0, r1 + 1)
        for col in range(c0, c1 + 1)
        if (row, col) not in target_cells
    )
    contaminating_bbox[hole[0]][hole[1]] = 7
    assert any("inside the largest-object bbox" in error for error in GEN.self_check(contaminating_bbox))

    no_op = [[0] * 10 for _ in range(8)]
    no_op[0][0] = 5
    for row, col in ((3, 3), (3, 4), (4, 3), (4, 4)):
        no_op[row][col] = 6
    assert any("visually unchanged" in error for error in GEN.self_check(no_op))

    too_small = [[0] * 10 for _ in range(8)]
    too_small[0][0] = 2
    too_small[3][3] = too_small[3][4] = 6
    assert any("at least 3" in error for error in GEN.self_check(too_small))


def test_negative_recombination_is_rejected_but_racket_oracle_executes():
    grid = GEN.generate(
        909,
        5,
        difficulty="hard",
        grid_h=12,
        grid_w=14,
        motif_profile="l_tetromino",
        placement_profile="upper_left",
        decoy_profile="none",
    )
    recombined = copy.deepcopy(grid)
    target_color = GEN._analyse(grid)[0]["target"]["color"]
    tie_color = 9 if target_color != 9 else 8
    for row, col in ((9, 10), (9, 11), (10, 10), (10, 11)):
        recombined[row][col] = tie_color
    assert any("unique largest" in error for error in GEN.self_check(recombined))

    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    snapshot = copy.deepcopy(recombined)
    try:
        output = _apply_rule(bridge, fn_name, recombined)
    finally:
        bridge.shutdown()
    assert recombined == snapshot
    assert output and all(output)


def test_determinism_fresh_returns_and_process_global_rng_isolation():
    random.seed(8128)
    state = random.getstate()
    kwargs = {
        "difficulty": "hard",
        "grid_h": 12,
        "grid_w": 14,
        "code_profile": "lr_transpose_cw",
        "motif_profile": "zig_hexomino",
        "motif_color": 9,
        "placement_profile": "lower_right",
        "decoy_profile": "two_small",
    }
    first = GEN.generate(444, 19, **kwargs)
    assert random.getstate() == state
    second = GEN.generate(444, 19, **kwargs)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 1
    assert GEN.generate(444, 19, **kwargs) == second


def test_generated_counterexamples_refute_the_canonical_ambiguous_shortcut():
    canonical = canonical_pairs(TASK_ID)
    shortcut = GEN.CANONICAL_SHORTCUTS["crop_all_body_content"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in canonical)

    witnesses = []
    for band in BANDS:
        for index in range(40):
            grid = GEN.generate(500_000 + index, index, difficulty=band)
            if shortcut(grid) != GEN.rule_mirror(grid):
                witnesses.append((band, index, _frozen(grid)))
                break
    assert {band for band, _, _ in witnesses} == set(BANDS)
