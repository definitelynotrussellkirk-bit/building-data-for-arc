from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest

TASK_ID = "db80068a483e"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]


def _canonical_pairs():
    for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["train"] + row["test"]
    raise AssertionError("canonical task row not found")


def test_canonical_inputs_are_owned_and_rule_mirror_is_exact():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_override_axes_are_observable_at_boundaries():
    cases = [
        {
            "profile": "17x18_3x5_3k",
            "key_row": 0,
            "key_stride": 4,
            "probe_mask_size": 3,
            "blank_count": 5,
        },
        {
            "profile": "18x20_3x4_4k",
            "key_row": 1,
            "key_stride": 5,
            "probe_mask_size": 4,
            "blank_count": 6,
        },
        {
            "profile": "20x18_4x4_4k",
            "key_row": 0,
            "key_stride": 5,
            "probe_mask_size": 3,
            "blank_count": 6,
        },
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(8800 + index, 71 + index, difficulty="hard", **overrides)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        assert gen.observe_overrides(grid) == overrides


def test_self_check_rejects_targeted_rule_hiding_mutations():
    grid = gen.generate(
        991,
        44,
        difficulty="medium",
        profile="18x20_3x4_4k",
        key_row=1,
        key_stride=5,
        probe_mask_size=3,
        blank_count=5,
    )
    facts, errors = gen._analyze(grid)
    assert not errors

    missing_marker = copy.deepcopy(grid)
    color, kr, kc = facts["key_markers"][0]
    missing_marker[kr][kc] = 0
    assert gen.self_check(missing_marker)

    empty_mask = copy.deepcopy(grid)
    for dr, dc in facts["masks"][color]:
        empty_mask[kr + 1 + dr][kc + 1 + dc] = 0
    assert gen.self_check(empty_mask)

    broken_frame = copy.deepcopy(grid)
    tr, tc = facts["tile_rows"][0], facts["tile_cols"][0]
    broken_frame[tr][tc] = 0
    assert gen.self_check(broken_frame)

    unkeyed_center = copy.deepcopy(grid)
    used = {0, 1, 5, *facts["key_colors"]}
    alien = next(c for c in range(10) if c not in used)
    unkeyed_center[tr + 1][tc + 1] = alien
    assert gen.self_check(unkeyed_center)

    duplicate_mask = copy.deepcopy(grid)
    color2, kr2, kc2 = facts["key_markers"][1]
    for dr in (0, 1):
        for dc in (0, 1):
            duplicate_mask[kr2 + 1 + dr][kc2 + 1 + dc] = 0
    for dr, dc in facts["masks"][color]:
        duplicate_mask[kr2 + 1 + dr][kc2 + 1 + dc] = 1
    assert gen.self_check(duplicate_mask)

    count_drift = copy.deepcopy(grid)
    keyed = facts["key_colors"][0]
    # Remove two canonical blank branches without breaking the tile lattice.
    for i, j in facts["blank_positions"][:2]:
        tr2, tc2 = facts["tile_rows"][i], facts["tile_cols"][j]
        count_drift[tr2 + 1][tc2 + 1] = keyed
    assert gen.self_check(count_drift) == []
    assert gen.strict_canonical_like(count_drift)


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = gen.generate(123456, 78, difficulty="easy")
    assert random.getstate() == state
    second = gen.generate(123456, 78, difficulty="easy")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(123456, 78, difficulty="easy") == second


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, made_up_axis="typo")


def test_every_generated_scene_refutes_named_shortcuts():
    for seed in range(12):
        grid = gen.generate(seed + 5000, seed * 7 + 3, difficulty=("easy", "medium", "hard")[seed % 3])
        intended = gen.rule_mirror(grid)
        for name, rival in gen.SEMANTIC_RIVALS.items():
            assert rival(grid) != intended, name
