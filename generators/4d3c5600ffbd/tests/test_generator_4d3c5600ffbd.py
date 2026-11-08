"""Behavioral regressions for the exact-two-border yellow-component task.

These tests deliberately use an independent component oracle instead of the
production helpers.  Set GENERATOR_UNDER_TEST to replay them against a copied
candidate during the final fresh-packet handoff check.
"""
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "4d3c5600ffbd"
ROOT = find_root(__file__)
DEFAULT_SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_SOURCE.is_file():
    DEFAULT_SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_SOURCE)).resolve()
SPEC = importlib.util.spec_from_file_location(f"review_regressions_{TASK_ID}", SOURCE)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
PAIRS = canonical_pairs(TASK_ID, root=ROOT)


def components(grid):
    """Independent 4-connected nonzero component reader."""
    height, width = len(grid), len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                r, c = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (r + dr, c + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            sides = set()
            if any(r == 0 for r, _ in cells):
                sides.add("top")
            if any(r == height - 1 for r, _ in cells):
                sides.add("bottom")
            if any(c == 0 for _, c in cells):
                sides.add("left")
            if any(c == width - 1 for _, c in cells):
                sides.add("right")
            found.append({"color": color, "cells": tuple(sorted(cells)), "sides": frozenset(sides)})
    return found


def reference_output(grid):
    output = copy.deepcopy(grid)
    for obj in components(grid):
        if obj["color"] == 4 and len(obj["sides"]) == 2:
            for row, col in obj["cells"]:
                output[row][col] = 8
    return output


def pair(grid):
    return {"input": copy.deepcopy(grid), "output": reference_output(grid)}


def rot90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def d4(grid):
    out = []
    current = copy.deepcopy(grid)
    for _ in range(4):
        out.append(copy.deepcopy(current))
        out.append([row[::-1] for row in current])
        current = rot90(current)
    return out


def has_opposite_two_border_target(grid):
    opposite = {frozenset(("top", "bottom")), frozenset(("left", "right"))}
    return any(obj["color"] == 4 and obj["sides"] in opposite for obj in components(grid))


def has_adjacent_two_border_target(grid):
    opposite = {frozenset(("top", "bottom")), frozenset(("left", "right"))}
    return any(
        obj["color"] == 4 and len(obj["sides"]) == 2 and obj["sides"] not in opposite
        for obj in components(grid)
    )


def touch_counts(grid):
    return sorted(len(obj["sides"]) for obj in components(grid) if obj["color"] == 4)


def test_rule_pin_axes_and_canonical_authority():
    from arcpuzzles import Catalog

    assert GEN.RULE_HASH == Catalog(ROOT).describe(TASK_ID)["rule_hash"]
    assert GEN.RULE_HASH == "af5bd9f68ba9"
    assert set(GEN.AXES) == {"scene_profile", "transform"}
    assert tuple(GEN.SCENE_PROFILES) == ("canonical_anchor", "opposite_span", "three_side")
    assert GEN.EXAMPLES_NEEDED == 4


@pytest.mark.parametrize(
    "canonical",
    PAIRS,
    ids=[f"variant{p['variant']}-{p['split']}{p['pair_index']}" for p in PAIRS],
)
def test_all_canonical_inputs_are_strict_and_python_mirror_matches(canonical):
    original = copy.deepcopy(canonical["input"])
    assert GEN.self_check(canonical["input"]) == []
    assert GEN.strict_canonical_like(canonical["input"]) == []
    assert GEN.solve_python(canonical["input"]) == canonical["output"]
    assert reference_output(canonical["input"]) == canonical["output"]
    assert canonical["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", ["canonical_anchor", "opposite_span", "three_side"])
@pytest.mark.parametrize("transform", [0, 7])
def test_every_exact_override_round_trips_from_returned_pixels(band, profile, transform):
    grid = GEN.generate(
        20261004,
        9,
        difficulty=band,
        scene_profile=profile,
        transform=transform,
    )
    assert GEN.self_check(grid, difficulty=band) == []
    assert GEN.observe_overrides(grid) == {"scene_profile": profile, "transform": transform}
    assert GEN.solve_python(grid) == reference_output(grid)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"scene_profile": "unknown"},
        {"scene_profile": 7},
        {"transform": -1},
        {"transform": 8},
        {"transform": True},
        {"transform": 1.5},
        {"transform": "2"},
    ],
)
def test_invalid_and_unknown_overrides_are_rejected_loudly(overrides):
    with pytest.raises(ValueError):
        GEN.generate(1, 2, **overrides)


def test_default_schedule_has_rotation_safe_decisive_support():
    expected = ("opposite_span", "three_side", "opposite_span", "three_side", "canonical_anchor")
    assert tuple(GEN.SCHEDULE_PROFILES) == tuple(GEN.SCENE_PROFILES)
    for band in (None, "easy", "medium", "hard"):
        observed = tuple(GEN.schedule_profile(13, index, difficulty=band) for index in range(5))
        assert observed == expected
        for start in range(15):
            window = [GEN.schedule_profile(13, start + offset, difficulty=band) for offset in range(5)]
            assert window.count("opposite_span") == 2
            assert window.count("three_side") == 2
            assert window.count("canonical_anchor") == 1


def test_profile_geometry_is_genuinely_distinct_and_rule_relevant():
    canonical_keys = {
        tuple(tuple(row) for row in transformed)
        for canonical in PAIRS
        for transformed in d4(canonical["input"])
    }
    anchor = GEN.generate(41, 0, scene_profile="canonical_anchor", transform=3)
    opposite = GEN.generate(41, 0, scene_profile="opposite_span", transform=3)
    three = GEN.generate(41, 0, scene_profile="three_side", transform=3)

    assert tuple(tuple(row) for row in anchor) in canonical_keys
    assert has_opposite_two_border_target(opposite)
    assert has_adjacent_two_border_target(opposite)
    assert {0, 1, 2} <= set(touch_counts(opposite))
    assert 3 in touch_counts(three)
    assert has_adjacent_two_border_target(three)
    assert {0, 1, 2, 3} <= set(touch_counts(three))


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[]],
        [[0] * 9 for _ in range(9)],
        [[4] * 9 for _ in range(9)],
        [[0] * 9 for _ in range(8)] + [[0] * 8],
        [[True] + [0] * 8 for _ in range(9)],
        [[0] * 9 for _ in range(9)],
    ],
)
def test_self_check_rejects_malformed_or_degenerate_grids(grid):
    assert GEN.self_check(grid)


def test_self_check_rejects_task_specific_shortcuts_and_answer_leakage():
    fixtures = {}

    one_cell = [[0] * 9 for _ in range(9)]
    one_cell[0][0] = 4
    fixtures["single corner cell"] = one_cell

    short_line = [[0] * 9 for _ in range(9)]
    short_line[0][2:5] = [4, 4, 4]
    fixtures["one-border line"] = short_line

    solid_interior = [[0] * 9 for _ in range(9)]
    for row in (4, 5):
        for col in (4, 5):
            solid_interior[row][col] = 4
    fixtures["interior square"] = solid_interior

    only_target = [[0] * 9 for _ in range(9)]
    for row in (0, 1):
        for col in (0, 1):
            only_target[row][col] = 4
    fixtures["target without retained contrast"] = only_target

    answer_leak = GEN.generate(99, 0, scene_profile="opposite_span", transform=0)
    answer_leak[4][4] = 8
    fixtures["cyan answer leakage"] = answer_leak

    for name, grid in fixtures.items():
        assert GEN.self_check(grid), name


def test_generated_distribution_is_strict_deterministic_fresh_and_diverse():
    random.seed(8675309)
    state = random.getstate()
    keys = set()
    profiles = set()
    for band in ("easy", "medium", "hard"):
        for index in range(30):
            first = GEN.generate(31000 + index, index, difficulty=band)
            second = GEN.generate(31000 + index, index, difficulty=band)
            assert first == second
            assert first is not second
            assert all(a is not b for a, b in zip(first, second))
            assert GEN.self_check(first, difficulty=band) == []
            assert GEN.strict_canonical_like(first) == []
            assert reference_output(first) != first
            observation = GEN.observe_overrides(first)
            profiles.add(observation["scene_profile"])
            keys.add(tuple(tuple(row) for row in first))
    assert random.getstate() == state
    assert profiles == set(GEN.SCENE_PROFILES)
    assert len(keys) >= 70


def test_declared_canonical_shortcuts_really_fit_every_canonical_pair():
    assert {"adjacent_two_only", "at_least_two"} <= set(GEN.CANONICAL_SHORTCUTS)
    assert set(GEN.CANONICAL_SHORTCUTS) <= set(GEN.LESSON_COMPETITORS)
    assert set(GEN.CANONICAL_SHORTCUTS) <= set(GEN.SEMANTIC_RIVALS)
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(item["input"]) == item["output"] for item in PAIRS), name


def test_each_semantic_witness_is_a_real_counterexample_to_its_claimed_rivals():
    examples = {
        "opposite_two_border": GEN.generate(712, 0, scene_profile="opposite_span", transform=0),
        "three_border_retained": GEN.generate(712, 0, scene_profile="three_side", transform=0),
        "one_border_retained": GEN.generate(712, 0, scene_profile="opposite_span", transform=0),
        "interior_retained": GEN.generate(712, 0, scene_profile="opposite_span", transform=0),
        "adjacent_two_border": GEN.generate(712, 0, scene_profile="three_side", transform=0),
    }
    for witness_name, grid in examples.items():
        assert GEN.SEMANTIC_WITNESSES[witness_name](grid), witness_name
        expected = reference_output(grid)
        claimed = GEN.WITNESS_RIVALS[witness_name]
        assert claimed
        assert any(GEN.SEMANTIC_RIVALS[name](copy.deepcopy(grid)) != expected for name in claimed)


def test_every_cyclic_five_pair_window_and_query_rotation_refutes_all_rivals():
    for band in ("easy", "medium", "hard"):
        for start in range(10):
            lesson = [pair(GEN.generate(8801, start + offset, difficulty=band)) for offset in range(5)]
            for query_index in range(5):
                query = lesson[query_index]
                demos = lesson[:query_index] + lesson[query_index + 1 :]
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(rival(item["input"]) != item["output"] for item in demos), (
                        band,
                        start,
                        query_index,
                        name,
                    )


def test_real_racket_rule_matches_independent_oracle_when_available():
    try:
        from arc_repl.racket_bridge import racket_runtime_status
        from arcpuzzles import Catalog
    except ImportError as exc:
        pytest.skip(str(exc))
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [item["input"] for item in PAIRS]
    grids += [GEN.generate(9301, index, difficulty="hard") for index in range(15)]
    result = Catalog(ROOT).apply(TASK_ID, grids, timeout=180)
    assert result["rule_hash_matches_catalog"]
    assert [item["output"] for item in result["results"]] == [reference_output(grid) for grid in grids]
