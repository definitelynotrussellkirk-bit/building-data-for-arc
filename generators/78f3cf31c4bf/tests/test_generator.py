"""Focused regressions for the 78f3cf31c4bf local 2x2-completion curriculum."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "78f3cf31c4bf"
ROOT = find_root(__file__)


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=ROOT)


def _canonical_rule_hash():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row["program_solution"]
                normalized = " ".join(source.split())
                return hashlib.sha256(normalized.encode()).hexdigest()[:12]
    raise AssertionError(f"missing canonical task {TASK_ID}")
def _load_generator():
    path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _pair(seed: int, sample_index: int, band: str = "medium"):
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_hash_and_canonical_pairs_are_bound_to_authority():
    assert gen.RULE_HASH == _canonical_rule_hash()
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_unknown_override_is_rejected_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, unknown_axis=1)


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
        assert gen.observe_overrides(grid) == overrides
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        assert gen.strict_canonical_like(grid) == []


def test_smallest_grid_supports_every_count_layout_corner_combination():
    for targets in (4, 5, 6):
        for colors in (1, 2, 3):
            for layout in ("isolated", "connected"):
                for corners in (2, 3, 4):
                    overrides = {
                        "grid_h": 6,
                        "grid_w": 8,
                        "target_count": targets,
                        "color_count": colors,
                        "layout_mode": layout,
                        "corner_diversity": corners,
                    }
                    for seed in (0, 17):
                        grid = gen.generate(seed, 200 + seed, difficulty="hard", **overrides)
                        assert gen.observe_overrides(grid) == overrides
                        assert gen.self_check(grid, meta={"overrides": overrides}) == []


def test_default_schedule_reaches_canonical_target_count_neighbourhood():
    for band in ("easy", "medium", "hard"):
        counts = {
            gen.observe_overrides(gen.generate(2718, index, difficulty=band))["target_count"]
            for index in range(6)
        }
        assert min(counts) == 3
        assert max(counts) == 6


def test_schedule_anchors_all_selected_canonical_profiles_in_every_band():
    canonical_profiles = {_profile(pair["input"]) for pair in _canonical_pairs()}
    for band in ("easy", "medium", "hard"):
        generated_profiles = {
            _profile(gen.generate(300 + index, index, difficulty=band))
            for index in range(6)
        }
        assert len(canonical_profiles & generated_profiles) >= 3


def test_connected_and_repeated_colour_controls_refute_named_shortcuts():
    connected = gen.generate(
        100,
        0,
        difficulty="easy",
        grid_h=6,
        grid_w=8,
        target_count=4,
        color_count=2,
        layout_mode="connected",
        corner_diversity=3,
    )
    repeated = gen.generate(
        101,
        1,
        difficulty="easy",
        grid_h=7,
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


def test_connected_multicolour_scene_teaches_colour_agreement_and_one_pass():
    for seed in range(8):
        grid = gen.generate(
            seed,
            0,
            difficulty="medium",
            grid_h=6,
            grid_w=8,
            target_count=4,
            color_count=2,
            layout_mode="connected",
            corner_diversity=3,
        )
        intended = gen.rule_mirror(grid)
        assert gen.SEMANTIC_RIVALS["ignore_colour_agreement"](grid) != intended
        assert gen.SEMANTIC_RIVALS["repeat_until_stable"](grid) != intended
        assert gen.rule_mirror(intended) != intended


def test_named_shortcuts_fit_every_canonical_pair():
    pairs = _canonical_pairs()
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


def test_every_three_demo_sliding_window_identifies_the_rule():
    for band in ("easy", "medium", "hard"):
        examples = [_pair(7000, index, band) for index in range(12)]
        for start in range(9):
            assert gen.lesson_identifiable(examples[start:start + 3], examples[start + 3]) == []


def test_rule_mirror_is_pure_and_generation_does_not_touch_global_rng():
    kwargs = {
        "difficulty": "medium",
        "grid_h": 9,
        "grid_w": 12,
        "target_count": 6,
        "color_count": 2,
        "layout_mode": "connected",
        "corner_diversity": 4,
    }
    random.seed(20261003)
    state = random.getstate()
    first = gen.generate(123, 4, **kwargs)
    assert random.getstate() == state
    second = gen.generate(123, 4, **kwargs)
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    before = copy.deepcopy(first)
    output = gen.rule_mirror(first)
    assert first == before
    assert output != first
