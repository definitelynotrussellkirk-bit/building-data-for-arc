from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs


TASK_ID = "f16508733f0a"
gen = importlib.import_module(
    "puzzle_generators.per_puzzle.f16508733f0a.generator"
)


def _pair(seed: int, sample_index: int, band: str = "medium"):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_canonical_inputs_are_accepted_and_outputs_match_pinned_rule():
    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_all_exact_axis_boundaries_round_trip():
    cases = [
        {
            "grid_h": height,
            "grid_w": width,
            "target_count": targets,
            "color_count": colors,
            "layout_mode": layout,
            "corner_diversity": corners,
        }
        for height in (6, 14)
        for width in (8, 16)
        for targets in (4, 6)
        for colors in (1, 3)
        for layout in ("isolated", "connected")
        for corners in (2, 4)
    ]
    for index, overrides in enumerate(cases):
        grid = gen.generate(9100 + index, 1000 + index, difficulty="hard", **overrides)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.observe_overrides(grid) == overrides


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, unknown_axis=1)


def test_self_check_rejects_targeted_impostors():
    mixed_color_l = [[1, 1], [2, 0]]
    assert any("mixed-colour" in error for error in gen.self_check(mixed_color_l))

    conflicting_claims = [
        [1, 1, 0],
        [1, 0, 2],
        [0, 2, 2],
    ]
    assert any("multiple colours" in error for error in gen.self_check(conflicting_claims))

    unused_distractor = [
        [1, 1, 0, 0, 2],
        [1, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    assert any("without any local completion" in error for error in gen.self_check(unused_distractor))

    completed_block = [[1, 1], [1, 1]]
    assert any("at least one local" in error for error in gen.self_check(completed_block))


def test_decisive_witnesses_refute_every_named_canonical_shortcut():
    connected = gen.generate(
        100,
        0,
        difficulty="easy",
        grid_h=6,
        grid_w=8,
        target_count=4,
        color_count=3,
        layout_mode="connected",
        corner_diversity=3,
    )
    repeated = gen.generate(
        101,
        1,
        difficulty="easy",
        grid_h=6,
        grid_w=8,
        target_count=5,
        color_count=1,
        layout_mode="isolated",
        corner_diversity=4,
    )
    assert gen.SEMANTIC_WITNESSES["connected_component_counterexample"](connected)
    assert gen.SEMANTIC_RIVALS["component_bbox_completion"](connected) != gen.rule_mirror(connected)

    assert gen.SEMANTIC_WITNESSES["repeated_color_counterexample"](repeated)
    assert gen.SEMANTIC_RIVALS["one_completion_per_color"](repeated) != gen.rule_mirror(repeated)
    assert gen.SEMANTIC_RIVALS["require_exactly_three_cells_per_color"](repeated) != gen.rule_mirror(repeated)


def test_every_three_demo_sliding_window_identifies_the_rule():
    for band in ("easy", "medium", "hard"):
        for start in range(18):
            examples = [_pair(5000 + start * 10 + offset, start + offset, band) for offset in range(4)]
            assert gen.lesson_identifiable(examples[:3], examples[3]) == []


def test_deterministic_fresh_input_pure_and_global_rng_pure():
    kwargs = dict(
        difficulty="medium",
        grid_h=9,
        grid_w=12,
        target_count=6,
        color_count=2,
        layout_mode="connected",
        corner_diversity=4,
    )
    random.seed(20260726)
    state = random.getstate()
    first = gen.generate(123, 4, **kwargs)
    assert random.getstate() == state
    second = gen.generate(123, 4, **kwargs)
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))

    before = copy.deepcopy(first)
    output = gen.rule_mirror(first)
    assert first == before
    assert output != first
