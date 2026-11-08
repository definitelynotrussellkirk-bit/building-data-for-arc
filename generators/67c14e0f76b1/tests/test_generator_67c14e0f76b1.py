from __future__ import annotations

import copy
import importlib
import random

from reviewer_support import canonical_pairs, find_root

TASK_ID = "67c14e0f76b1"
ROOT = find_root(__file__)
GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.67c14e0f76b1.generator"
)


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_canonical_pairs_are_accepted_and_match_rule_mirror():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_declared_overrides_are_exact_at_boundaries():
    cases = [
        (7, 10, "isolated", "single_3"),
        (7, 16, "overlap", "dual_4_7"),
        (14, 10, "edges", "dual_5_6"),
        (14, 16, "mixed", "dual_6_9"),
    ]
    for index, (h, w, scene, palette) in enumerate(cases):
        grid = GEN.generate(
            seed=1000 + index,
            sample_index=index,
            difficulty="hard",
            grid_h=h,
            grid_w=w,
            scene_profile=scene,
            palette_profile=palette,
        )
        assert GEN.observe_overrides(grid) == {
            "grid_h": h,
            "grid_w": w,
            "scene_profile": scene,
            "palette_profile": palette,
        }
        assert GEN.strict_canonical_like(grid) == []


def test_four_consecutive_samples_identify_every_named_rival():
    for start in range(8):
        demos = [
            _pair(GEN.generate(seed=77, sample_index=start + offset, difficulty="medium"))
            for offset in range(GEN.EXAMPLES_NEEDED)
        ]
        query = _pair(
            GEN.generate(
                seed=77,
                sample_index=start + GEN.EXAMPLES_NEEDED,
                difficulty="medium",
            )
        )
        assert GEN.lesson_identifiable(demos, query) == []
        for rival in GEN.LESSON_COMPETITORS.values():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_self_check_rejects_four_targeted_impostors():
    grid = GEN.generate(seed=123, sample_index=0, difficulty="easy")

    ragged = copy.deepcopy(grid)
    ragged[0].pop()
    assert GEN.self_check(ragged)

    output_leak = copy.deepcopy(grid)
    output_leak[0][0] = 2
    assert any("output color 2" in error for error in GEN.self_check(output_leak))

    invalid_palette = copy.deepcopy(grid)
    invalid_palette[0][0] = 10
    assert any("outside ARC palette" in error for error in GEN.self_check(invalid_palette))

    no_target = [[0 for _ in row] for row in grid]
    no_target[0][0] = 1
    assert any("no immediate horizontal" in error for error in GEN.self_check(no_target))


def test_determinism_fresh_returns_and_global_rng_purity():
    random.seed(987654321)
    before = random.getstate()
    first = GEN.generate(seed=321, sample_index=5, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(seed=321, sample_index=5, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    first[0][0] = 9 if first[0][0] != 9 else 8
    replay = GEN.generate(seed=321, sample_index=5, difficulty="hard")
    assert replay == second


def test_unknown_override_rejected_loudly():
    try:
        GEN.generate(seed=1, sample_index=0, unknown_axis="typo")
    except ValueError as exc:
        assert "unknown override" in str(exc)
    else:
        raise AssertionError("unknown override was silently accepted")


def test_regression_every_four_example_window_varies_distractor_palette():
    for seed in range(64):
        for start in range(4):
            palettes = {
                GEN.observe_overrides(
                    GEN.generate(seed, start + offset, difficulty="medium")
                )["palette_profile"]
                for offset in range(GEN.EXAMPLES_NEEDED)
            }
            assert len(palettes) >= 2, (seed, start, palettes)
