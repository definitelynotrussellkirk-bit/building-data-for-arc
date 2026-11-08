from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random

TASK = "7e9fd4cf84a9"
HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[1]


def _module():
    spec = importlib.util.spec_from_file_location("_arc_7e9fd4cf84a9_generator", HERE / "generator.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical():
    for line in (REPO / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("content_hash") == TASK:
            return row
    raise AssertionError("canonical task not found")


def test_canonical_pairs_pass_self_check_and_exact_python_replay():
    g = _module()
    task = _canonical()
    for pair in task["train"] + task["test"]:
        assert g.self_check(pair["input"]) == []
        assert g.canonical_transform(pair["input"]) == pair["output"]


def test_minimum_grid_honors_six_rectangles_and_five_distractors():
    g = _module()
    grid = g.generate(
        901, 7,
        grid_h=13,
        grid_w=13,
        n_rectangles=6,
        distractor_count=5,
        layout_profile="balanced",
    )
    analysis = g.analyze_scene(grid)
    assert (len(grid), len(grid[0])) == (13, 13)
    assert analysis["green_rectangle_count"] == 6
    assert analysis["distractor_cell_count"] == 5
    assert g.self_check(grid) == []
    assert g.canonical_transform(grid) != grid


def test_profiles_are_observable_and_outputs_preserve_distractors():
    g = _module()
    scenes = {
        profile: g.generate(
            44, 3,
            grid_h=24,
            grid_w=24,
            n_rectangles=4,
            distractor_count=3,
            layout_profile=profile,
        )
        for profile in ("balanced", "wide", "tall")
    }
    analyses = {name: g.analyze_scene(grid) for name, grid in scenes.items()}
    assert scenes["wide"] != scenes["tall"]
    assert all(w >= h for h, w in analyses["wide"]["rectangle_shapes"])
    assert all(h >= w for h, w in analyses["tall"]["rectangle_shapes"])
    for name, grid in scenes.items():
        out = g.canonical_transform(grid)
        for r, c, color in analyses[name]["distractor_cells"]:
            assert out[r][c] == color
        assert g.self_check(grid) == []


def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    g = _module()
    before = random.getstate()
    a = g.generate(1234, 19, grid_h=20, grid_w=21, n_rectangles=5, distractor_count=4)
    after = random.getstate()
    b = g.generate(1234, 19, grid_h=20, grid_w=21, n_rectangles=5, distractor_count=4)
    assert before == after
    assert a == b
    assert a is not b and all(ar is not br for ar, br in zip(a, b))


def test_invalid_axis_values_are_rejected_strictly():
    g = _module()
    for kwargs in (
        {"grid_h": 12},
        {"grid_w": 31},
        {"n_rectangles": 0},
        {"distractor_count": 6},
        {"layout_profile": "inert"},
        {"grid_h": True},
    ):
        try:
            g.generate(1, 0, **kwargs)
        except (TypeError, ValueError):
            pass
        else:
            raise AssertionError(f"override should fail: {kwargs}")
