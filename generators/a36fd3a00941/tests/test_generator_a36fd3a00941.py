"""Task-local regression and teaching-contract tests for a36fd3a00941."""
from __future__ import annotations

from collections import deque
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
try:
    from reviewer_support import canonical_pairs, canonical_path, find_root
except ModuleNotFoundError:
    sys.path.insert(0, str(HOME.parents[1] / "shared" / "runtime"))
    from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)
CANONICAL_LEDGER = canonical_path(ROOT)
GEN_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
TASK_ID = "a36fd3a00941"
CANONICAL_DIMS = {(8, 12), (9, 11), (8, 13), (9, 12)}


def _load_generator():
    spec = importlib.util.spec_from_file_location("generator_under_test", GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _objects(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            todo = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while todo:
                r, c = todo.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            r1, r2 = min(rows), max(rows)
            c1, c2 = min(cols), max(cols)
            result.append(
                {
                    "color": color,
                    "cells": cells,
                    "bbox": (r1, c1, r2, c2),
                    "height": r2 - r1 + 1,
                    "width": c2 - c1 + 1,
                }
            )
    return result


def _teaching_signature(grid):
    objects = sorted(
        _objects(grid),
        key=lambda obj: (2 * (obj["height"] + obj["width"]), obj["bbox"][1], obj["bbox"][0]),
    )
    return {
        "perimeters": [2 * (obj["height"] + obj["width"]) for obj in objects],
        "areas": [obj["height"] * obj["width"] for obj in objects],
        "counts": [len(obj["cells"]) for obj in objects],
        "lefts": [obj["bbox"][1] for obj in objects],
    }


def test_rule_hash_is_bound_to_selected_authority():
    assert gen.RULE_HASH == "d0dcd1dd1256"


@pytest.mark.parametrize("pair", canonical_pairs(TASK_ID, root=ROOT, labeled_only=True))
def test_canonical_inputs_are_lawful_and_python_mirror_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
def test_every_default_draw_is_canonical_scale_and_contains_the_teaching_counterexample(band):
    for index in range(40):
        grid = gen.generate(1000 + index, index, difficulty=band)
        assert gen.self_check(grid) == [], (band, index)
        assert gen.strict_canonical_like(grid) == [], (band, index)
        assert (len(grid), len(grid[0])) in CANONICAL_DIMS
        output = gen.rule_mirror(grid)
        assert output != grid
        assert len(output) < len(grid)
        assert len(output[0]) <= len(grid[0])

        signature = _teaching_signature(grid)
        assert signature["perimeters"] == [8, 10, 12]
        assert signature["areas"] == [4, 6, 5]
        assert signature["counts"] == [4, 5, 5]
        # The largest-perimeter five-cell line has smaller bbox area than the
        # middle-perimeter five-cell crop, so area/count shortcuts reverse them.
        assert signature["lefts"][2] < signature["lefts"][1]

        for rival in gen.SEMANTIC_RIVALS.values():
            assert rival(grid) != gen.rule_mirror(grid)


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
def test_every_scene_profile_override_round_trips_exactly(band):
    for index, profile in enumerate(gen.PROFILE_NAMES):
        grid = gen.generate(3000 + index, index, difficulty=band, scene_profile=profile)
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


def test_unknown_override_fails_closed():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __override_contract_unknown_axis__="x")


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
def test_every_three_demo_window_refutes_all_declared_shortcuts(band):
    for start in range(8):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(5000 + start, sample_index, difficulty=band)
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(5000 + start, start + gen.EXAMPLES_NEEDED, difficulty=band)
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []
        for rival in gen.LESSON_COMPETITORS.values():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos)



def test_difficulty_bands_change_the_realized_scene_for_same_seed_and_index():
    realized = {
        repr(gen.generate(777, 9, difficulty=band))
        for band in ("easy", "medium", "hard")
    }
    assert len(realized) == 3

def test_replay_is_deterministic_fresh_and_does_not_touch_global_rng():
    before = random.getstate()
    first = gen.generate(424242, 17, difficulty="hard")
    after = random.getstate()
    second = gen.generate(424242, 17, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert second == gen.generate(424242, 17, difficulty="hard")
