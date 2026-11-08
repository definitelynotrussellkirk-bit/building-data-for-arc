from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

import pytest


gen = importlib.import_module("puzzle_generators.per_puzzle.54a83e6bbc20.generator")
ROOT = Path(__file__).resolve().parents[1]


from scripts.canonical_profile_gate import canonical_pairs


def test_rule_hash_matches_task_local_authority():
    base = json.loads(
        (ROOT / "data/base/solutions/training/18447a8d__54a83e6bbc20.json").read_text()
    )
    normalized = " ".join(base["racket_target"]["target_code"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == gen.RULE_HASH


def test_all_canonical_pairs_are_accepted_and_mirrored_exactly():
    pairs = canonical_pairs(gen.TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_every_scene_profile_round_trips_through_observation():
    for profile in gen.SCENE_PROFILES:
        grid = gen.generate(771, 4, scene_profile=profile)
        assert gen.self_check(grid, meta={"scene_profile": profile}) == []
        assert gen.observe_overrides(grid)["scene_profile"] == profile
        assert gen.observe_overrides(grid)["shape_profile"] in gen.SHAPE_PROFILES
        assert gen.rule_mirror(grid) != grid


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="pairs3_rotate")


def test_minimal_impostors_and_broken_structure_are_rejected():
    grid = gen.generate(91, 1, difficulty="hard")
    assert gen.self_check([[7] * 11 for _ in range(9)])
    assert gen.self_check([[8] * 11 for _ in range(9)])
    assert gen.self_check([list(row) for row in zip(*grid)])
    broken = [row[:] for row in grid]
    broken[0][0] = 8
    assert gen.self_check(broken)


def test_named_rivals_are_killed_by_a_permuted_equal_area_scene():
    grid = gen.generate(1234, 1, scene_profile="pairs3_rotate", shape_profile="equal_area")
    official = gen.rule_mirror(grid)
    assert gen.SEMANTIC_WITNESSES["right_pieces_are_permuted"](grid)
    assert gen.SEMANTIC_WITNESSES["color_order_is_not_the_rule"](grid)
    assert gen.SEMANTIC_WITNESSES["equal_area_requires_shape_matching"](grid)
    for name in ("pair_by_input_row", "pair_by_sorted_color", "pair_by_area_only"):
        assert gen.SEMANTIC_RIVALS[name](grid) != official
