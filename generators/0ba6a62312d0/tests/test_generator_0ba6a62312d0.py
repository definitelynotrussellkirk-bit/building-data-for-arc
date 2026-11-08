"""Focused regression tests for task 0ba6a62312d0."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs

TASK_ID = "0ba6a62312d0"
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.0ba6a62312d0.generator"
)


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_canonical_linked_profiles_are_pinned():
    assert GEN.RULE_HASH == "4a2f94aea981"
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        for rival in GEN.SEMANTIC_RIVALS.values():
            assert rival(pair["input"]) == pair["output"]


def test_every_five_sample_window_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(10):
            grids = [
                GEN.generate(7000 + start, start + offset, difficulty=band)
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            demos = [_pair(grid) for grid in grids[: GEN.EXAMPLES_NEEDED]]
            query = _pair(grids[-1])
            assert {GEN.observe_overrides(pair["input"])["texture"] for pair in demos} == set(
                GEN.TEXTURES
            )
            assert GEN.lesson_identifiable(demos, query) == []


def test_exact_override_boundaries_and_unknown_keys():
    for band in ("easy", "medium", "hard"):
        for texture in GEN.TEXTURES:
            for height, width in ((6, 6), (6, 16), (16, 6), (16, 16)):
                grid = GEN.generate(
                    901,
                    7,
                    difficulty=band,
                    texture=texture,
                    grid_h=height,
                    grid_w=width,
                )
                assert GEN.self_check(grid) == []
                assert GEN.observe_overrides(grid) == {
                    "grid_h": height,
                    "grid_w": width,
                    "texture": texture,
                }
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_texture="plain")


def test_each_profile_kills_its_canonical_compatible_rival():
    mapping = {
        "clip": "discard_whole_component_when_any_cell_clips",
        "multi_object": "rotate_only_first_non6_component",
        "multicolor": "collapse_object_to_modal_color",
        "extra_six": "preserve_every_color6_marker",
    }
    for texture, rival_name in mapping.items():
        grid = GEN.generate(123, 4, difficulty="medium", texture=texture)
        assert GEN.SEMANTIC_RIVALS[rival_name](grid) != GEN.rule_mirror(grid)
    extra = GEN.generate(124, 4, difficulty="medium", texture="extra_six")
    assert GEN.SEMANTIC_RIVALS["use_last_color6_as_pivot"](extra) != GEN.rule_mirror(extra)


def test_self_check_rejects_targeted_impostors():
    canonical = copy.deepcopy(canonical_pairs(TASK_ID)[0]["input"])

    no_pivot = copy.deepcopy(canonical)
    for row_index, row in enumerate(no_pivot):
        for column_index, value in enumerate(row):
            if value == 6:
                no_pivot[row_index][column_index] = 0
    assert any("pivot" in reason or "color-6" in reason for reason in GEN.self_check(no_pivot))

    too_small = [[0] * 6 for _ in range(6)]
    too_small[2][2] = 6
    too_small[1][1] = 3
    assert any("at least three" in reason for reason in GEN.self_check(too_small))

    adjacent_sixes = copy.deepcopy(canonical)
    pivot = GEN._positions(adjacent_sixes, 6)[0]
    adjacent_sixes[pivot[0]][pivot[1] + 1] = 6
    assert any("singleton" in reason for reason in GEN.self_check(adjacent_sixes))

    all_clipped = [[0] * 6 for _ in range(6)]
    all_clipped[1][0] = 6
    all_clipped[3][0] = 4
    all_clipped[4][0] = 4
    all_clipped[5][0] = 4
    assert any("all rotated" in reason for reason in GEN.self_check(all_clipped))

    invariant = [[0] * 7 for _ in range(7)]
    invariant[3][3] = 6
    for point in ((2, 3), (3, 4), (4, 3), (3, 2)):
        invariant[point[0]][point[1]] = 8
    assert any("invariant" in reason for reason in GEN.self_check(invariant))


def test_negative_recombination_is_rejected_even_when_oracle_executes():
    grid = GEN.generate(777, 1, difficulty="easy", texture="clip")
    changed = copy.deepcopy(grid)
    cells = GEN._non_six_cells(changed)
    changed[cells[0][0]][cells[0][1]] = 1
    changed[cells[1][0]][cells[1][1]] = 2
    assert any("clipping scenes" in reason for reason in GEN.self_check(changed))
    assert GEN.rule_mirror(changed)  # The authority can execute this malformed lesson.


def test_replay_fresh_returns_and_global_rng_purity():
    random.seed(314159)
    before = random.getstate()
    first = GEN.generate(42, 17, difficulty="hard")
    middle = GEN.generate(43, 18, difficulty="easy")
    second = GEN.generate(42, 17, difficulty="hard")
    after = random.getstate()

    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second, strict=True))
    assert middle != first
    assert before == after
