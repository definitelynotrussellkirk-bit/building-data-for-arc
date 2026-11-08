from __future__ import annotations

import copy
import importlib
import random
from collections import Counter

import pytest

from puzzle_generators.base import set_ctx_observer
from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from scripts.canonical_profile_gate import canonical_pairs

GEN = importlib.import_module("puzzle_generators.per_puzzle.a9f315ca9cc7.generator")
BANDS = ("easy", "medium", "hard")


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_metadata_and_all_canonical_pairs_are_exact_and_input_pure():
    assert GEN.TASK_ID == "a9f315ca9cc7"
    assert GEN.GENERATOR_ID == GEN.TASK_ID
    assert GEN.VERSION == "2.1.0"
    assert GEN.RULE_HASH == "813a5290113c"

    pairs = canonical_pairs(GEN.TASK_ID)
    assert len(pairs) == 6
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        before = copy.deepcopy(source)
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == before


def test_exact_overrides_are_observable_for_30_seeds_per_band():
    for band in BANDS:
        for seed in range(30):
            for profile in GEN.SCHEDULE_PROFILES:
                for fg_color in (1, 5, 9):
                    grid = GEN.generate(
                        10_000 + seed,
                        seed * 17 + 3,
                        difficulty=band,
                        scene_profile=profile,
                        fg_color=fg_color,
                    )
                    assert GEN.observe_overrides(grid) == {
                        "scene_profile": profile,
                        "fg_color": fg_color,
                    }
                    assert GEN.self_check(
                        grid,
                        meta={
                            "overrides": {
                                "scene_profile": profile,
                                "fg_color": fg_color,
                            }
                        },
                    ) == []


def test_unknown_invalid_overrides_and_difficulty_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis="canonical")
    with pytest.raises(ValueError):
        GEN.generate(1, 0, scene_profile="memorized")
    with pytest.raises(ValueError):
        GEN.generate(1, 0, fg_color=0)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 0, difficulty="extreme")


def test_self_check_rejects_targeted_impostors():
    impostors = {
        "all_background": [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
        "full_one_color": [[4, 4, 4], [4, 4, 4], [4, 4, 4]],
        "singleton": [[0, 0, 0], [0, 4, 0], [0, 0, 0]],
        "short_line": [[0, 0, 0], [4, 4, 4], [0, 0, 0]],
        "solid_2x2": [[4, 4, 0], [4, 4, 0], [0, 0, 0]],
        "inverted_2x2_hole": [[0, 0, 4], [0, 0, 4], [4, 4, 4]],
        "two_foreground_colours": [[1, 1, 0], [1, 2, 0], [0, 2, 2]],
        "ragged": [[1, 0, 1], [1, 0], [0, 1, 1]],
    }
    for name, grid in impostors.items():
        assert GEN.self_check(grid), name


def test_generation_is_deterministic_fresh_global_rng_neutral_and_provenance_exact():
    random.seed(987654321)
    state = random.getstate()
    first = GEN.generate(88, 5, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(88, 5, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == GEN.generate(88, 5, difficulty="hard")

    for band in BANDS:
        for index in range(30):
            captured = []
            set_ctx_observer(captured.append)
            try:
                grid = GEN.generate(50_000 + index, index * 13 + 2, difficulty=band)
            finally:
                set_ctx_observer(None)
            assert len(captured) == 1
            observed = GEN.observe_overrides(grid)
            assert observed["scene_profile"] == captured[0].axis_value("scene_profile")
            assert observed["fg_color"] == captured[0].axis_value("fg_color")


def test_strict_and_stability_censuses_are_anchored_and_varied():
    for seed_offset in (0, 1_000_000):
        for band_index, band in enumerate(BANDS):
            strict = 0
            inputs = set()
            profiles = Counter()
            counts = Counter()
            for index in range(200):
                grid = GEN.generate(seed_offset + band_index * 10_000 + index, index, difficulty=band)
                frozen = tuple(map(tuple, grid))
                inputs.add(frozen)
                strict += GEN.strict_canonical_like(grid) == []
                facts = GEN._analyze(grid)
                profiles[facts["scene_profile"]] += 1
                counts[facts["fg_count"]] += 1
            assert strict >= 50
            assert len(inputs) >= 100
            assert profiles["canonical"] >= 50
            assert profiles["generalized"] >= 50
            assert len(counts) >= 3


def test_named_rivals_are_refuted_and_every_sliding_lesson_is_identifiable():
    for band in BANDS:
        for start in range(20):
            episode = [
                _pair(GEN.generate(700_000 + start, start + offset, difficulty=band))
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            demos, query = episode[:-1], episode[-1]
            profiles = {GEN.observe_overrides(pair["input"])["scene_profile"] for pair in demos}
            assert profiles == {"canonical", "generalized"}
            assert GEN.lesson_identifiable(demos, query) == []
            for competitor in GEN.LESSON_COMPETITORS.values():
                assert any(competitor(pair["input"]) != pair["output"] for pair in demos)

    generalized = GEN.generate(19, 7, difficulty="medium", scene_profile="generalized")
    assert GEN.strict_canonical_like(generalized)
    assert (
        GEN.SEMANTIC_RIVALS["memorize_public_masks_else_pixel_scale"](generalized)
        != GEN.rule_mirror(generalized)
    )


def test_negative_recombination_rejected_by_distribution_but_racket_executes():
    impostor = [[4, 4, 0], [4, 4, 0], [0, 0, 0]]
    assert GEN.self_check(impostor)

    bundle = _load_bundle(GEN.TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        output = _apply_rule(bridge, fn_name, copy.deepcopy(impostor))
    finally:
        bridge.shutdown()
    assert len(output) == 9 and all(len(row) == 9 for row in output)
