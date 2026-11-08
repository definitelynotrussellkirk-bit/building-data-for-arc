from __future__ import annotations

import copy
import importlib.util
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "1409f5f7af2e"
ROOT = find_root(__file__)
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"


def _load():
    spec = importlib.util.spec_from_file_location(f"test_generator_{TASK_ID}", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pair(module, seed: int, sample_index: int, band: str):
    grid = module.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": module.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_inputs_are_accepted():
    module = _load()
    assert module.RULE_HASH == "f34e705e21f3"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert module.self_check(pair["input"]) == []
        assert module.strict_canonical_like(pair["input"]) == []
        assert module.rule_mirror(pair["input"]) == pair["output"]


def test_all_declared_overrides_are_exactly_observable():
    module = _load()
    cases = [
        {"grid_h": 9, "grid_w": 9, "n_pairs": 3, "scene_profile": "canonical_anchor"},
        {"grid_h": 11, "grid_w": 11, "n_pairs": 6, "scene_profile": "all_controls"},
        {"grid_h": 10, "grid_w": 9, "n_pairs": 5, "scene_profile": "all_controls"},
        {"grid_h": 11, "grid_w": 10, "n_pairs": 6, "scene_profile": "shared_chain"},
    ]
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = module.generate(9000 + index, index, difficulty=band, **overrides)
            assert module.observe_overrides(grid) == overrides
            assert module.self_check(grid) == []
    with pytest.raises(TypeError):
        module.generate(0, 0, unknown_axis=1)


def test_every_three_slot_window_is_identifiable():
    module = _load()
    for band in ("easy", "medium", "hard"):
        for start in range(6):
            episodes = [
                _pair(module, 12000 + start, start + offset, band)
                for offset in range(module.EXAMPLES_NEEDED + 1)
            ]
            assert module.lesson_identifiable(episodes[:-1], episodes[-1]) == []
            profiles = {
                module.observe_overrides(pair["input"])["scene_profile"]
                for pair in episodes[:-1]
            }
            assert profiles == {"canonical_anchor", "all_controls", "shared_chain"}



def test_shared_chain_profile_refutes_isolated_target_shortcut():
    module = _load()
    grid = module.generate(
        31415,
        2,
        difficulty="hard",
        grid_h=11,
        grid_w=10,
        n_pairs=6,
        scene_profile="shared_chain",
    )
    assert module.observe_overrides(grid)["scene_profile"] == "shared_chain"
    assert module._has_shared_target_endpoint(grid)
    assert module._rival_isolated_targets_only(grid) != module.rule_mirror(grid)
    assert module.self_check(grid) == []

def test_self_check_rejects_four_targeted_impostors():
    module = _load()

    horizontal_only = [[0] * 9 for _ in range(9)]
    for row in (1, 4, 7):
        horizontal_only[row][2] = 3
        horizontal_only[row][4] = 3
    assert module.self_check(horizontal_only)

    wrong_color = [[0] * 9 for _ in range(9)]
    for col in (1, 4, 7):
        wrong_color[2][col] = 4
        wrong_color[4][col] = 4
    wrong_color[0][0] = 3
    assert module.self_check(wrong_color)

    prefilled = module.generate(77, 0, difficulty="easy")
    row, col = module._target_cells(prefilled)[0]
    prefilled[row][col] = 2
    assert any("output-only" in reason for reason in module.self_check(prefilled))

    inverted = [[3] * 9 for _ in range(9)]
    for row in range(1, 8, 2):
        inverted[row][1] = 0
        inverted[row][4] = 0
        inverted[row][7] = 0
    assert module.self_check(inverted)


def test_replay_returns_fresh_objects_and_preserves_global_rng():
    module = _load()
    random.seed(123456)
    before = random.getstate()
    first = module.generate(314159, 2, difficulty="hard")
    after = random.getstate()
    second = module.generate(314159, 2, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_all_controls_profile_contains_each_decisive_negative_branch():
    module = _load()
    grid = module.generate(
        44,
        1,
        difficulty="medium",
        scene_profile="all_controls",
        n_pairs=4,
    )
    assert module._horizontal_only_green_gap(grid)
    assert module._blocked_vertical_green_gap(grid)
    assert module._other_color_vertical_gap(grid)
    assert module._harmless_green_count(grid) >= 1
    truth = module.rule_mirror(grid)
    for name in (
        "any_equal_color_vertical_gap",
        "horizontal_or_vertical_green_gap",
        "fill_even_when_middle_is_nonblack",
        "recolor_green_markers",
        "same_count_first_black_cells",
    ):
        assert module.SEMANTIC_RIVALS[name](grid) != truth


def test_schedule_metadata_matches_three_profile_cycle():
    module = _load()
    assert module.SCHEDULE_PROFILES == (
        "canonical_anchor",
        "all_controls",
        "shared_chain",
    )
    assert module.AXES["grid_h"]["default"] == "three-slot profile schedule"
    assert module.AXES["grid_w"]["default"] == "three-slot profile schedule"
    assert module.AXES["n_pairs"]["default"] == "difficulty-aware three-slot schedule"
    assert module.AXES["scene_profile"]["default"] == "anchor|all-controls|shared-chain schedule"
