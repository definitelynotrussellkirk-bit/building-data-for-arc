from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


TASK_ID = "0491e1a49389"
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    path = REPO / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_pairs() -> list[dict]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
                return [*row["train"], *tests]
    raise AssertionError(f"canonical task {TASK_ID} is missing")


gen = _load_generator()


def test_rule_identity_is_pinned_and_python_mirror_matches_canonical_pairs():
    assert gen.RULE_HASH == "d6db986b56c9"
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_declared_overrides_are_global_exact_and_unknown_keys_reject():
    grid = gen.generate(
        8128,
        17,
        difficulty="easy",
        grid_h=19,
        grid_w=18,
        n_objects=4,
        texture="off_center",
    )
    assert gen.observe_overrides(grid) == {
        "grid_h": 19,
        "grid_w": 18,
        "n_objects": 4,
        "texture": "off_center",
    }
    assert gen.self_check(grid) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __override_contract_unknown_axis__=1)


def _facts(grid):
    h, w = len(grid), len(grid[0])
    guide = next(r for r, row in enumerate(grid) if all(value == 9 for value in row))
    colors = {value for row in grid for value in row if value not in (0, 9)}
    cells = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
             if value not in (0, 9)]
    partial_clip = False
    for color in colors:
        own = [(r, c) for r, c, value in cells if value == color]
        visible = [0 <= 2 * guide - r < h for r, _ in own]
        partial_clip |= any(visible) and not all(visible)
    return {
        "shape": (h, w),
        "palette": len(colors) + 2,
        "guide": guide,
        "both_sides": any(r < guide for r, _, _ in cells)
        and any(r > guide for r, _, _ in cells),
        "partial_clip": partial_clip,
    }


def test_every_three_example_window_teaches_canonical_prior_axis_and_clipping():
    canonical_profiles = {(8, 9, 4), (9, 10, 4), (9, 11, 4)}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(6):
            grids = [
                gen.generate(9000 + band_index, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            facts = [_facts(grid) for grid in grids]
            assert all(item["both_sides"] for item in facts)
            assert any(
                (*item["shape"], item["palette"]) in canonical_profiles
                for item in facts
            )
            assert any(
                item["guide"] != (item["shape"][0] - 1) // 2
                for item in facts
            )
            assert any(item["partial_clip"] for item in facts)


@pytest.mark.parametrize("texture", tuple(gen.HELPFUL_TEXTURES))
@pytest.mark.parametrize("grid_h,grid_w", ((8, 8), (8, 18), (19, 8), (19, 18)))
@pytest.mark.parametrize("n_objects", (2, 4))
def test_helpful_texture_boundary_product_is_exact_and_rule_valid(
    texture, grid_h, grid_w, n_objects
):
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_objects": n_objects,
        "texture": texture,
    }
    grid = gen.generate(2200 + grid_h + grid_w, n_objects, difficulty="easy", **requested)
    assert gen.observe_overrides(grid) == requested
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) != grid


def test_canonical_middle_axis_shortcut_fits_real_demos_but_generated_off_center_refutes_it():
    rival = gen.CANONICAL_SHORTCUTS["fixed_middle_axis"]
    assert all(rival(pair["input"]) == pair["output"] for pair in _canonical_pairs())
    grid = gen.generate(771, 1, difficulty="medium")
    assert gen.SEMANTIC_WITNESSES["off_center_guide"](grid)
    assert rival(grid) != gen.rule_mirror(grid)


def test_three_demo_sliding_lessons_falsify_every_named_competitor():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(8):
            grids = [
                gen.generate(12000 + band_index, start + offset, difficulty=band)
                for offset in range(gen.EXAMPLES_NEEDED + 1)
            ]
            pairs = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]
            assert gen.lesson_identifiable(pairs[:-1], pairs[-1]) == []


def test_no_objects_is_a_negative_fixture_and_touching_guide_is_lawful():
    empty = gen.generate(17, 0, difficulty="medium", texture="no_objects")
    assert any("2-4 source objects" in reason for reason in gen.self_check(empty))

    touching = gen.generate(
        18,
        0,
        difficulty="medium",
        grid_h=8,
        grid_w=8,
        n_objects=4,
        texture="touching_guide",
    )
    assert gen.self_check(touching) == []
    assert gen.observe_overrides(touching)["texture"] == "touching_guide"


def test_replay_is_fresh_and_does_not_touch_global_random_state():
    random.seed(321)
    before = random.getstate()
    first = gen.generate(404, 5, difficulty="hard")
    after = random.getstate()
    second = gen.generate(404, 5, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert first[0] is not second[0]
    first[0][0] = 8 if first[0][0] != 8 else 7
    assert first != second
