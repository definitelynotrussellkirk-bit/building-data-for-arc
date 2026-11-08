"""Focused regression and teaching-contract tests for 579f1e2dcb4a."""
from __future__ import annotations

from collections import deque
import ast
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
TASK_ID = "579f1e2dcb4a"
EXPECTED_PROFILES = {
    "canonical_8x13_p6": (8, 13, 6),
    "canonical_9x12_p6": (9, 12, 6),
    "canonical_9x14_p7": (9, 14, 7),
    "canonical_10x15_p6": (10, 15, 6),
    "canonical_11x16_p7": (11, 16, 7),
}


def _load_generator():
    spec = importlib.util.spec_from_file_location("generator_under_test", GEN_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _components(grid):
    """Return 4-connected components of all nonzero cells, ignoring color."""
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] != 0
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            rows = [r for r, _ in cells]
            cols = [c for _, c in cells]
            colors = {grid[r][c] for r, c in cells}
            result.append(
                {
                    "cells": tuple(sorted(cells)),
                    "colors": colors,
                    "top": min(rows),
                    "left": min(cols),
                    "bottom": max(rows),
                    "right": max(cols),
                }
            )
    return result


def test_rule_hash_and_profile_contract_are_pinned():
    assert gen.RULE_HASH == "29c3632de610"
    assert gen.PROFILE_SPECS == EXPECTED_PROFILES
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0


def test_axes_contract_is_ast_literal_for_repository_linter():
    tree = ast.parse(GEN_PATH.read_text())
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AXES" for target in node.targets)
    )
    axes = ast.literal_eval(assignment.value)
    assert axes == {
        "scene_profile": {
            "type": "str",
            "default": "five-profile deterministic canonical schedule",
            "valid": "|".join(EXPECTED_PROFILES),
        }
    }


@pytest.mark.parametrize("pair", canonical_pairs(TASK_ID, root=ROOT, labeled_only=True))
def test_canonical_inputs_are_lawful_and_python_mirror_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
def test_default_schedule_covers_every_canonical_profile_with_multicolor_components(band):
    seen = set()
    for sample_index in range(20):
        grid = gen.generate(20261008, sample_index, difficulty=band)
        assert gen.self_check(grid) == [], (band, sample_index)
        assert gen.strict_canonical_like(grid) == [], (band, sample_index)
        observed = gen.observe_overrides(grid)
        seen.add(observed["scene_profile"])
        height, width, palette_count = EXPECTED_PROFILES[observed["scene_profile"]]
        assert (len(grid), len(grid[0])) == (height, width)
        assert len({value for row in grid for value in row}) == palette_count

        components = _components(grid)
        expected_components = 4 if palette_count == 6 else 3
        assert len(components) == expected_components
        assert sum(len(component["colors"]) == 2 for component in components) == palette_count - 4
        assert all(1 <= len(component["colors"]) <= 2 for component in components)

        lefts = [component["left"] for component in components]
        if palette_count == 6:
            # Canonical palette-6 scenes contain two same-colour 4-components
            # tied on their left edge; the rule's secondary top-row key matters.
            assert len(set(lefts)) == 3
            tied_left = next(left for left in set(lefts) if lefts.count(left) == 2)
            tied = [component for component in components if component["left"] == tied_left]
            assert len({next(iter(component["colors"])) for component in tied}) == 1
            assert all(len(component["colors"]) == 1 for component in tied)
            assert len({component["top"] for component in tied}) == 2
        else:
            assert len(set(lefts)) == 3

    assert seen == set(EXPECTED_PROFILES)


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
def test_every_scene_profile_override_round_trips_exactly(band):
    for index, profile in enumerate(EXPECTED_PROFILES):
        grid = gen.generate(3000 + index, index, difficulty=band, scene_profile=profile)
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


def test_unknown_and_invalid_overrides_fail_closed():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, __override_contract_unknown_axis__="x")
    with pytest.raises((TypeError, ValueError), match="scene_profile"):
        gen.generate(1, 0, scene_profile=3)
    with pytest.raises(ValueError, match="scene_profile"):
        gen.generate(1, 0, scene_profile="not-a-profile")


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
def test_default_schedule_supplies_a_witness_for_each_declared_shortcut(band):
    witnessed = set()
    for sample_index in range(20):
        grid = gen.generate(4000 + sample_index, sample_index, difficulty=band)
        truth = gen.rule_mirror(grid)
        assert truth != grid
        for name, rival in gen.SEMANTIC_RIVALS.items():
            if rival(grid) != truth:
                witnessed.add(name)
    assert witnessed == set(gen.SEMANTIC_RIVALS)


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
def test_every_three_demo_window_is_identifiable_against_declared_rivals(band):
    for start in range(10):
        demos = []
        for sample_index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(5000 + start, sample_index, difficulty=band)
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(
            5000 + start, start + gen.EXAMPLES_NEEDED, difficulty=band
        )
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []


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
