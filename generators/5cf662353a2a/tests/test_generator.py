"""Focused regression contract for the repaired 5cf662353a2a generator.

The oracle is an independent Python transcription of the selected Racket rule.
Canonical answers are authoring data and are never used by generator.py.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "5cf662353a2a"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location(f"reviewed_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)
PAIRS = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
BANDS = (None, "easy", "medium", "hard")


def _components(grid, *, include_markers=False):
    """Return same-colour 4-connected components, independent of production."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (not include_markers and color == 1) or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append({"color": color, "cells": tuple(sorted(cells))})
    return result


def _normalized(component):
    rows = [r for r, _ in component["cells"]]
    cols = [c for _, c in component["cells"]]
    top, left = min(rows), min(cols)
    return tuple(sorted((r - top, c - left) for r, c in component["cells"]))


def _bbox_area(component):
    rows = [r for r, _ in component["cells"]]
    cols = [c for _, c in component["cells"]]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def oracle(grid, *, sort_key="cell_count"):
    """Clear objects, sort them, and bottom-align them over marker columns."""
    h, w = len(grid), len(grid[0])
    markers = [c for c, value in enumerate(grid[-1]) if value == 1]
    objects = _components(grid)
    if sort_key == "cell_count":
        objects.sort(key=lambda obj: (len(obj["cells"]), obj["color"]))
    elif sort_key == "bbox_area":
        objects.sort(key=lambda obj: (_bbox_area(obj), len(obj["cells"]), obj["color"]))
    else:  # pragma: no cover - test helper misuse
        raise ValueError(sort_key)

    out = [[0 for _ in range(w)] for _ in range(h)]
    for col in markers:
        out[h - 1][col] = 1
    for marker_col, obj in zip(markers, objects):
        shape = _normalized(obj)
        shape_h = max(r for r, _ in shape) + 1
        top = h - 1 - shape_h
        for dr, dc in shape:
            out[top + dr][marker_col + dc] = obj["color"]
    return out


def profile(grid):
    return len(grid), len(grid[0]), len({cell for row in grid for cell in row})


def competitor_rules():
    result = {}
    for namespace in ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS", "LESSON_COMPETITORS"):
        table = getattr(gen, namespace)
        assert isinstance(table, dict) and table
        for name, rule in table.items():
            assert isinstance(name, str) and callable(rule)
            result.setdefault(name, rule)
    return result


def test_canonical_pairs_match_independent_oracle_and_checker():
    assert len(PAIRS) == 3
    for pair in PAIRS:
        assert oracle(pair["input"]) == pair["output"]
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []


def test_rule_hash_and_semantic_contract_are_pinned():
    assert gen.RULE_HASH == "da86a7976cec"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.AXES) == {"layout_profile", "palette_start"}
    assert set(gen.SEMANTIC_WITNESSES) == {"cell_count_vs_bbox_area"}
    assert set(gen.WITNESS_RIVALS) == {"cell_count_vs_bbox_area"}
    assert set(gen.WITNESS_RIVALS["cell_count_vs_bbox_area"]) == {"bbox_area_sort"}
    assert competitor_rules()


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("layout_profile", [
    "canonical_10x12_3",
    "canonical_11x13_3",
    "wide_12x17_3",
    "wide_13x18_4",
    "tall_15x14_3",
    "large_15x20_4",
])
@pytest.mark.parametrize("palette_start", [2, 5])
def test_joint_exact_overrides_are_observable(difficulty, layout_profile, palette_start):
    requested = {"layout_profile": layout_profile, "palette_start": palette_start}
    grid = gen.generate(711, 19, difficulty=difficulty, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert oracle(grid) != grid
    assert gen.SEMANTIC_WITNESSES["cell_count_vs_bbox_area"](grid)
    assert gen.SEMANTIC_RIVALS["bbox_area_sort"](grid) == oracle(grid, sort_key="bbox_area")
    assert gen.SEMANTIC_RIVALS["bbox_area_sort"](grid) != oracle(grid)


@pytest.mark.parametrize("kwargs", [
    {"typo_axis": 1},
    {"layout_profile": "unknown"},
    {"layout_profile": 3},
    {"palette_start": 1},
    {"palette_start": 6},
    {"palette_start": True},
    {"palette_start": "2"},
])
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 0, **kwargs)


def test_unknown_difficulty_is_rejected():
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")


@pytest.mark.parametrize("difficulty", BANDS)
def test_default_twenty_draw_schedule_hits_both_canonical_profiles(difficulty):
    profiles = []
    for index in range(20):
        grid = gen.generate(2026, index, difficulty=difficulty)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert oracle(grid) != grid
        profiles.append(profile(grid))
    assert (10, 12, 5) in profiles
    assert (11, 13, 5) in profiles


@pytest.mark.parametrize("difficulty", BANDS)
def test_defaults_are_deterministic_fresh_and_all_refute_bbox_shortcut(difficulty):
    seen = set()
    for index in range(36):
        first = gen.generate(90210, index, difficulty=difficulty)
        second = gen.generate(90210, index, difficulty=difficulty)
        assert first == second
        assert first is not second
        assert gen.self_check(first) == []
        expected = oracle(first)
        assert competitor_rules()["bbox_area_sort"](first) != expected
        seen.add(repr(first))
        first[0][0] = (first[0][0] + 1) % 10
        assert first != second
    assert len(seen) >= 24


def test_bbox_shortcut_fits_every_canonical_pair_but_generated_witness_refutes_it():
    rival = gen.CANONICAL_SHORTCUTS["bbox_area_sort"]
    for pair in PAIRS:
        assert rival(pair["input"]) == pair["output"]
    witness = gen.generate(31337, 4, layout_profile="canonical_10x12_3", palette_start=2)
    assert gen.SEMANTIC_WITNESSES["cell_count_vs_bbox_area"](witness)
    assert rival(witness) != oracle(witness)


@pytest.mark.parametrize("difficulty", BANDS)
def test_every_four_pair_window_is_identifiable_under_all_query_rotations(difficulty):
    pairs = []
    for index in range(12):
        grid = gen.generate(919, index, difficulty=difficulty)
        pairs.append({"input": grid, "output": oracle(grid)})
    for start in range(9):
        window = pairs[start:start + 4]
        for query_index in range(4):
            query = window[query_index]
            demos = [pair for i, pair in enumerate(window) if i != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in competitor_rules().items():
                if all(rival(pair["input"]) == pair["output"] for pair in demos):
                    assert rival(query["input"]) == query["output"], (
                        difficulty, start, query_index, name
                    )


@pytest.mark.parametrize("bad", [
    None,
    [],
    [[]],
    [[0, 0], [0]],
    [[0, True], [0, 1]],
    [[0, 10], [0, 1]],
    [[0, 0], [0, 0]],
    [[0, 1], [0, 0]],
])
def test_self_check_rejects_malformed_or_degenerate_inputs(bad):
    assert gen.self_check(bad)


def test_checker_rejects_output_clipping_and_nonunique_sizes():
    lawful = gen.generate(77, 3, layout_profile="canonical_10x12_3")
    clipped = deepcopy(lawful)
    clipped[-1] = [0] * len(clipped[-1])
    clipped[-1][-1] = 1
    assert gen.self_check(clipped)

    duplicate = deepcopy(lawful)
    objects = _components(duplicate)
    largest = max(objects, key=lambda obj: len(obj["cells"]))
    r, c = largest["cells"][-1]
    duplicate[r][c] = 0
    assert gen.self_check(duplicate)
