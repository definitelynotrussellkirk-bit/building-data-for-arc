"""Focused regression tests for the ordered bottom-key recoloring generator."""
from __future__ import annotations

import copy
import importlib
import random

import pytest

from scripts.canonical_profile_gate import canonical_pairs

GEN = importlib.import_module(
    "puzzle_generators.per_puzzle.aa351fcbb853.generator"
)


def _pair(grid):
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_canonical_pairs_are_task_linked():
    assert GEN.RULE_HASH == "6369d6244c02"
    pairs = canonical_pairs(GEN.TASK_ID)
    assert len(pairs) == 3
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN.rule_mirror(source) == pair["output"]
        assert source == pair["input"]


def test_every_four_demo_window_identifies_every_start_residue():
    for band in ("easy", "medium", "hard"):
        for start in range(12):
            episode = []
            for sample_index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(1000 + start, sample_index, difficulty=band)
                episode.append(_pair(grid))
            assert GEN.lesson_identifiable(
                episode[: GEN.EXAMPLES_NEEDED], episode[-1]
            ) == []


def test_schedule_covers_canonical_repeated_tiebreak_and_key_spacing():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(2000, index, difficulty=band) for index in range(4)]
        signatures = [GEN.semantic_signature(grid) for grid in grids]
        assert sum(not GEN.strict_canonical_like(grid) for grid in grids) == 2
        assert {sig["object_palette"] for sig in signatures} == {
            "distinct",
            "repeated",
        }
        assert {sig["order_pattern"] for sig in signatures} == {
            "strict_columns",
            "shared_left_edge",
        }
        assert {sig["key_spacing"] for sig in signatures} == {
            "clustered",
            "spread",
        }
        assert any(GEN._row_order_differs(grid) for grid in grids)


def test_override_boundaries_are_exact_and_unknowns_reject():
    cases = (
        {
            "grid_h": 8,
            "grid_w": 9,
            "n_objects": 2,
            "object_palette": "repeated",
            "order_pattern": "shared_left_edge",
            "key_spacing": "clustered",
        },
        {
            "grid_h": 14,
            "grid_w": 16,
            "n_objects": 4,
            "object_palette": "distinct",
            "order_pattern": "strict_columns",
            "key_spacing": "spread",
        },
    )
    for band in ("easy", "medium", "hard"):
        for index, requested in enumerate(cases):
            grid = GEN.generate(3000 + index, 30 + index, difficulty=band, **requested)
            assert GEN.observe_overrides(grid) == requested
            assert GEN.self_check(grid, meta=requested) == []
    with pytest.raises(TypeError, match="unknown override axis"):
        GEN.generate(1, 0, typo_axis="ignored-before-repair")


def test_deterministic_fresh_returns_and_global_rng_isolation():
    random.seed(987654321)
    before = random.getstate()
    first = GEN.generate(77, 19, difficulty="hard")
    middle = GEN.generate(78, 20, difficulty="easy")
    second = GEN.generate(77, 19, difficulty="hard")
    assert random.getstate() == before
    assert first == second
    assert first != middle
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(77, 19, difficulty="hard") == second


def test_self_check_rejects_four_targeted_impostors():
    base = GEN.generate(4000, 0, difficulty="medium")
    analysis = GEN._analyze(base)
    assert analysis["errors"] == []

    missing_key = copy.deepcopy(base)
    missing_key[-1][analysis["key_cols"][0]] = 0
    assert any("object count" in error for error in GEN.self_check(missing_key))

    duplicate_key = copy.deepcopy(base)
    duplicate_key[-1][analysis["key_cols"][1]] = analysis["key_colors"][0]
    assert any("key colors must be distinct" in error for error in GEN.self_check(duplicate_key))

    palette_overlap = copy.deepcopy(base)
    object0 = analysis["objects"][0]
    for row, col in object0["cells"]:
        palette_overlap[row][col] = analysis["key_colors"][0]
    assert any("disjoint" in error or "connected" in error for error in GEN.self_check(palette_overlap))

    same_size = copy.deepcopy(base)
    # Replace every object by a two-cell vertical domino at the same anchor.
    for obj in analysis["objects"]:
        for row, col in obj["cells"]:
            same_size[row][col] = 0
        row, col = obj["bbox"][:2]
        same_size[row][col] = obj["color"]
        same_size[row + 1][col] = obj["color"]
    assert any("sizes must vary" in error for error in GEN.self_check(same_size))


def test_repeated_input_color_does_not_merge_output_roles():
    grid = GEN.generate(
        5000,
        2,
        difficulty="hard",
        n_objects=4,
        object_palette="repeated",
        order_pattern="strict_columns",
        key_spacing="spread",
    )
    analysis = GEN._analyze(grid)
    assert analysis["object_palette"] == "repeated"
    assert GEN._same_input_color_same_output(grid) != GEN.rule_mirror(grid)
    assert GEN.SEMANTIC_WITNESSES[
        "repeated_input_colors_still_get_sequential_keys"
    ](grid)
