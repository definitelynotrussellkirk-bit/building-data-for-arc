from __future__ import annotations

import copy
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.b7ad0d8d96f6 import generator as gen
from scripts.canonical_profile_gate import (
    canonical_pairs,
    canonical_rule_hash,
    canonical_rule_source,
)


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "b7ad0d8d96f6"
AUTHORITY_FILES = (
    ROOT / "data/base/solutions/training/5a719d11__b7ad0d8d96f6.json",
    ROOT / "data/base/solutions/augmented/5a719d11__91e002a2c0fc.json",
)


def _copy(grid):
    return [list(row) for row in grid]


def test_rule_pin_all_canonical_pairs_and_selected_authorities_are_exact() -> None:
    source = canonical_rule_source(TASK_ID)
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == canonical_rule_hash(TASK_ID) == "fcca49befb05"

    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 8
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original

    for path in AUTHORITY_FILES:
        target = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code"] == source
        assert target["raw_code"] != target["target_code"]
        assert target["canonicalization_status"] == (
            "selected_canonical_with_preserved_archival_raw"
        )


def test_every_declared_profile_is_exact_observable_and_band_linked() -> None:
    for index, profile in enumerate(gen.SCENE_PROFILES):
        band = profile.split("_", 1)[0]
        grid = gen.generate(
            7000 + index,
            index,
            difficulty=band,
            scene_profile=profile,
        )
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert gen.semantic_signature(grid)["scene_profile"] == profile


def test_unknown_override_and_unknown_difficulty_are_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis="previously_accepted")
    with pytest.raises(ValueError, match="unknown difficulty"):
        gen.generate(1, 0, difficulty="extreme")


def test_every_four_demo_sliding_window_identifies_the_rule() -> None:
    expected_suffixes = {
        "A_distinct",
        "B_same_background",
        "C_opposite_fg_trap",
        "D_shared_foreground",
    }
    for band in ("easy", "medium", "hard"):
        for start in range(4):
            grids = [
                gen.generate(8200 + start, start + offset, difficulty=band)
                for offset in range(5)
            ]
            profiles = [gen.observe_overrides(grid)["scene_profile"] for grid in grids[:4]]
            assert {profile.split("_", 1)[1] for profile in profiles} == expected_suffixes
            demos = [
                {"input": grid, "output": gen.rule_mirror(grid)}
                for grid in grids[:4]
            ]
            query = {
                "input": grids[4],
                "output": gen.rule_mirror(grids[4]),
            }
            assert gen.lesson_identifiable(demos, query) == []


def test_named_semantic_rivals_are_killed_by_the_scheduled_witnesses() -> None:
    grids = [gen.generate(9100, index, difficulty="hard") for index in range(4)]
    for witness_name, rival_names in gen.WITNESS_RIVALS.items():
        witness_grid = next(
            grid for grid in grids if gen.SEMANTIC_WITNESSES[witness_name](grid)
        )
        expected = gen.rule_mirror(witness_grid)
        for rival_name in rival_names:
            assert gen.SEMANTIC_RIVALS[rival_name](witness_grid) != expected


def test_rule_resets_panels_swaps_exact_masks_and_uses_source_backgrounds() -> None:
    grid = gen.generate(
        12345,
        2,
        difficulty="easy",
        scene_profile="easy_C_opposite_fg_trap",
    )
    scene = gen._validated_scene(grid)
    output = gen.rule_mirror(grid)

    for group in scene["groups"]:
        left, right = group["left"], group["right"]
        for rel_row in range(left["height"]):
            for rel_col in range(left["width"]):
                left_expected = (
                    right["background"]
                    if (rel_row, rel_col) in right["mask"]
                    else left["background"]
                )
                right_expected = (
                    left["background"]
                    if (rel_row, rel_col) in left["mask"]
                    else right["background"]
                )
                assert output[left["row_start"] + rel_row][left["col_start"] + rel_col] == left_expected
                assert output[right["row_start"] + rel_row][right["col_start"] + rel_col] == right_expected

    same_bg = gen.generate(
        12345,
        1,
        difficulty="easy",
        scene_profile="easy_B_same_background",
    )
    same_scene = gen._validated_scene(same_bg)
    same_output = gen.rule_mirror(same_bg)
    collapsed = next(
        group
        for group in same_scene["groups"]
        if group["left"]["background"] == group["right"]["background"]
    )
    background = collapsed["left"]["background"]
    for panel in (collapsed["left"], collapsed["right"]):
        assert {
            same_output[row][col]
            for row in range(panel["row_start"], panel["row_end"])
            for col in range(panel["col_start"], panel["col_end"])
        } == {background}


def test_self_check_rejects_five_targeted_structural_impostors() -> None:
    base = gen.generate(
        2222,
        0,
        difficulty="easy",
        scene_profile="easy_A_distinct",
    )
    scene = gen._validated_scene(base)
    first = scene["groups"][0]
    left, right = first["left"], first["right"]

    broken_separator = _copy(base)
    separator_col = scene["col_runs"][0][1]
    broken_separator[0][separator_col] = left["background"]
    assert gen.self_check(broken_separator)

    third_panel_color = _copy(base)
    panel_colors = {left["background"], left["foreground"]}
    extra = next(color for color in range(1, 10) if color not in panel_colors)
    third_panel_color[left["row_start"]][left["col_start"]] = extra
    assert gen.self_check(third_panel_color)

    border_touching_mask = _copy(base)
    border_touching_mask[left["row_start"]][left["col_start"]] = left["foreground"]
    assert gen.self_check(border_touching_mask)

    filled_bbox = _copy(base)
    r0, c0, r1, c1 = left["bbox"]
    for rel_row in range(r0, r1 + 1):
        for rel_col in range(c0, c1 + 1):
            filled_bbox[left["row_start"] + rel_row][left["col_start"] + rel_col] = left["foreground"]
    assert gen.self_check(filled_bbox)

    duplicate_masks = _copy(base)
    for rel_row in range(left["height"]):
        for rel_col in range(left["width"]):
            duplicate_masks[left["row_start"] + rel_row][left["col_start"] + rel_col] = left["background"]
    for rel_row, rel_col in right["mask"]:
        duplicate_masks[left["row_start"] + rel_row][left["col_start"] + rel_col] = left["foreground"]
    assert gen.self_check(duplicate_masks)


def test_replay_is_deterministic_fresh_and_global_rng_pure() -> None:
    random.seed(20260816)
    before = random.getstate()
    first = gen.generate(987654321, 27, difficulty="hard")
    after_first = random.getstate()
    second = gen.generate(987654321, 27, difficulty="hard")
    assert before == after_first == random.getstate()
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
