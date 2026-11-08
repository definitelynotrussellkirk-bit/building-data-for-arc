"""Focused regressions for the reviewed 97f17772dd96 generator."""
from __future__ import annotations

import copy
import importlib.util
import os
from itertools import combinations
from pathlib import Path
import random

import pytest

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK_ID = "97f17772dd96"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=ROOT)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_rule_pin_and_independent_mirror_match_all_canonical_pairs():
    assert GEN.RULE_HASH == "1fab8c098fd0"
    assert GEN.RULE_HASH == Catalog(ROOT).describe(TASK_ID)["rule_hash"]
    assert len(PAIRS) == 3
    catalog = Catalog(ROOT)
    for pair in PAIRS:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original

        receipt = catalog.apply(TASK_ID, [pair["input"]])
        assert receipt["rule_hash_matches_catalog"] is True
        assert receipt["executed_rule_hash"] == GEN.RULE_HASH
        assert receipt["results"][0]["error"] is None
        assert receipt["results"][0]["output"] == pair["output"]


def test_exact_axes_round_trip_in_every_difficulty_band():
    cases = (
        {"grid_h": 12, "grid_w": 15, "n_frames": 3, "asymmetry_force": True},
        {"grid_h": 15, "grid_w": 12, "n_frames": 2, "asymmetry_force": False},
    )
    for band in (None, "easy", "medium", "hard"):
        for offset, requested in enumerate(cases):
            grid = GEN.generate(1701 + offset, 23 + offset, difficulty=band, **requested)
            assert GEN.self_check(grid, difficulty=band, meta=requested) == []
            assert GEN.observe_overrides(grid) == requested
            assert grid == GEN.generate(1701 + offset, 23 + offset, difficulty=band, **requested)


def test_unknown_invalid_and_coercive_controls_fail_closed():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis=3)

    for name, values in {
        "grid_h": (True, 12.0, "12", 11, 16),
        "grid_w": (False, 15.0, "15", 11, 16),
        "n_frames": (True, 2.0, "2", 1, 4),
        "asymmetry_force": (0, 1, "true", None),
    }.items():
        for value in values:
            with pytest.raises((TypeError, ValueError)):
                GEN.generate(0, 0, **{name: value})

    for seed in (True, 1.5, "1"):
        with pytest.raises(TypeError, match="seed"):
            GEN.generate(seed, 0)
    for index in (True, -1, 1.5, "1"):
        with pytest.raises((TypeError, ValueError), match="sample_index"):
            GEN.generate(0, index)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="extreme")


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[1]],
        [[0], [0, 1]],
        [[True] * 12 for _ in range(12)],
        [[10] * 12 for _ in range(12)],
        [[0] * 12 for _ in range(12)],
    ],
)
def test_self_check_rejects_malformed_and_minimal_impostors(grid):
    assert GEN.self_check(grid)


def test_validator_rejects_broken_or_touching_frame_geometry():
    good = GEN.generate(
        31,
        5,
        grid_h=13,
        grid_w=13,
        n_frames=3,
        asymmetry_force=False,
    )
    assert GEN.self_check(good) == []

    broken = copy.deepcopy(good)
    frame_cell = next(
        (r, c)
        for r, row in enumerate(broken)
        for c, value in enumerate(row)
        if value == 1 and 0 < r < len(broken) - 1 and 0 < c < len(row) - 1
    )
    broken[frame_cell[0]][frame_cell[1]] = 0
    assert GEN.self_check(broken)

    touching = copy.deepcopy(good)
    # Add a bridge between the outer and next frame; this merges components.
    analysis = GEN.analyze_grid(touching)
    outer, middle = analysis["frames"][:2]
    col = middle[1]
    for row in range(outer[0] + 1, middle[0] + 1):
        touching[row][col] = 1
    assert GEN.self_check(touching)


def test_named_concentric_shortcut_fits_canonical_but_generated_witness_refutes_it():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"concentric_only"}
    rival = GEN.CANONICAL_SHORTCUTS["concentric_only"]
    for pair in PAIRS:
        assert rival(pair["input"]) == pair["output"]

    witness = GEN.generate(
        20261011,
        97,
        grid_h=12,
        grid_w=15,
        n_frames=3,
        asymmetry_force=True,
    )
    expected = GEN.rule_mirror(witness)
    assert GEN.SEMANTIC_WITNESSES["offset_inner_frame"](witness)
    assert rival(witness) != expected

    receipt = Catalog(ROOT).apply(TASK_ID, [witness])
    assert receipt["results"][0]["error"] is None
    assert receipt["results"][0]["output"] == expected


def test_default_four_example_windows_expose_the_named_shortcut_under_every_rotation():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            lesson = [_pair(GEN.generate(9000 + start, start + offset, difficulty=band)) for offset in range(4)]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                assert GEN.lesson_identifiable(demos, lesson[query_index]) == []
                assert any(GEN.SEMANTIC_WITNESSES["offset_inner_frame"](pair["input"]) for pair in demos)


def test_default_schedule_covers_frame_counts_asymmetry_and_canonical_sizes():
    for band in (None, "easy", "medium", "hard"):
        observed = [GEN.observe_overrides(GEN.generate(421, index, difficulty=band)) for index in range(12)]
        assert {item["n_frames"] for item in observed} == {2, 3}
        assert {item["asymmetry_force"] for item in observed} == {False, True}
        assert {(item["grid_h"], item["grid_w"]) for item in observed} >= {
            (12, 12),
            (13, 13),
            (15, 15),
        }


def test_determinism_fresh_return_and_process_global_rng_purity():
    random.seed(8675309)
    before = random.getstate()
    a = GEN.generate(314159, 7, difficulty="medium")
    middle = random.getstate()
    b = GEN.generate(314159, 7, difficulty="medium")
    after = random.getstate()
    assert a == b
    assert a is not b
    assert all(row_a is not row_b for row_a, row_b in zip(a, b))
    assert before == middle == after

    a[0][0] = (a[0][0] + 1) % 2
    assert GEN.generate(314159, 7, difficulty="medium") == b


def test_fixed_schedule_position_still_has_seed_driven_layout_diversity():
    grids = {
        tuple(tuple(row) for row in GEN.generate(seed, 0, difficulty="easy"))
        for seed in range(20)
    }
    assert len(grids) >= 4
