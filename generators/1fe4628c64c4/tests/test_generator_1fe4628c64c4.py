"""Focused semantic and regression tests for the rectangular-truss generator."""
from __future__ import annotations

import copy
import importlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest


gen = importlib.import_module(
    "puzzle_generators.per_puzzle.1fe4628c64c4.generator"
)
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data/canonical/puzzles.jsonl"


def _canonical_pairs():
    with CANONICAL.open(encoding="utf-8") as handle:
        row = next(
            json.loads(line)
            for line in handle
            if json.loads(line).get("task_id") == gen.TASK_ID
        )
    return [pair for split in ("train", "test") for pair in row[split]]


def _key(grid):
    return tuple(tuple(row) for row in grid)


def _facts(grid):
    analysis = gen._analyze(grid)
    assert analysis["errors"] == []
    return analysis["facts"]


def test_identity_and_declared_contract():
    assert gen.GENERATOR_ID == gen.TASK_ID == "1fe4628c64c4"
    assert gen.VERSION == "4.0.0"
    assert gen.EXAMPLES_NEEDED == 4
    assert gen.MIN_STRICT_FRAC == 1.0
    assert tuple(gen.SCENE_PROFILES) == (
        "canonical_s1",
        "canonical_s2",
        "canonical_s3",
        "canonical_s4",
        "expanded_s1",
        "expanded_s2",
        "expanded_s3",
        "expanded_s4",
    )
    assert set(gen.AXES) == {
        "scene_profile",
        "palette_profile",
        "anchor_r",
        "anchor_c",
    }
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("pair", _canonical_pairs())
def test_all_canonical_pairs_are_accepted_and_match_the_rule(pair):
    original = copy.deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


def test_canonical_profile_inventory_covers_sizes_and_palettes_exactly():
    observed = [gen.observe_overrides(pair["input"]) for pair in _canonical_pairs()]
    assert {item["scene_profile"] for item in observed} == {
        "canonical_s1",
        "canonical_s2",
        "canonical_s3",
        "canonical_s4",
    }
    assert {item["palette_profile"] for item in observed} == {
        "canonical_train0",
        "canonical_train1",
        "canonical_test0",
        "canonical_test1",
    }
    assert {(_facts(pair["input"])["anchor_size"]) for pair in _canonical_pairs()} == {
        1,
        2,
        3,
        4,
    }


@pytest.mark.parametrize("difficulty", (None, "easy", "medium", "hard"))
def test_natural_schedule_is_valid_deterministic_diverse_and_balanced(difficulty):
    grids = [gen.generate(731, index, difficulty=difficulty) for index in range(64)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert all(gen.rule_mirror(grid) != grid for grid in grids)
    assert len({_key(grid) for grid in grids}) >= 56
    signatures = [gen.semantic_signature(grid) for grid in grids]
    assert Counter(sig["anchor_size"] for sig in signatures) == Counter(
        {1: 16, 2: 16, 3: 16, 4: 16}
    )
    assert Counter(sig["scene_profile"].split("_", 1)[0] for sig in signatures) == Counter(
        {"canonical": 32, "expanded": 32}
    )
    assert {sig["background_is_zero"] for sig in signatures} == {False, True}
    assert grids == [gen.generate(731, index, difficulty=difficulty) for index in range(64)]


def test_every_exact_override_is_observable_and_unknown_axes_are_rejected():
    cases = (
        {
            "scene_profile": "canonical_s1",
            "palette_profile": "canonical_test0",
            "anchor_r": 1,
            "anchor_c": 1,
        },
        {
            "scene_profile": "expanded_s4",
            "palette_profile": "aug_3",
            "anchor_r": 4,
            "anchor_c": 4,
        },
    )
    for index, overrides in enumerate(cases):
        grid = gen.generate(900 + index, index, difficulty="hard", **overrides)
        assert gen.self_check(grid, meta={"overrides": overrides}) == []
        assert gen.observe_overrides(grid) == overrides
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, nonexistent_axis=3)


def test_generation_returns_fresh_grids_without_touching_global_rng():
    random.seed(8192)
    state = random.getstate()
    first = gen.generate(91, 5)
    assert random.getstate() == state
    second = gen.generate(91, 5)
    assert first == second and first is not second
    before = copy.deepcopy(second)
    first[0][0] = 99
    assert second == before


def test_structural_analyzer_rejects_mutation_impostors():
    base = gen.generate(
        99,
        3,
        scene_profile="canonical_s4",
        palette_profile="canonical_test1",
        anchor_r=2,
        anchor_c=2,
    )
    f = _facts(base)
    impostors = []

    missing_anchor = copy.deepcopy(base)
    missing_anchor[f["second_anchor_r"]][f["second_anchor_c"]] = f["background"]
    impostors.append(missing_anchor)

    wrong_inner = copy.deepcopy(base)
    wrong_inner[f["anchor_r"] + f["anchor_size"] + 2][f["anchor_c"]] = f["top_color"]
    impostors.append(wrong_inner)

    stray_cell = copy.deepcopy(base)
    stray_cell[-1][0] = f["top_color"]
    impostors.append(stray_cell)

    broken_gap = copy.deepcopy(base)
    broken_gap[f["anchor_r"]][f["anchor_c"] + f["anchor_size"] + 1] = f["side_color"]
    impostors.append(broken_gap)

    shortened_top_bar = copy.deepcopy(base)
    shortened_top_bar[f["anchor_r"]][f["anchor_c"] + f["anchor_size"]] = f["background"]
    impostors.append(shortened_top_bar)

    for impostor in impostors:
        assert gen.self_check(impostor)
        assert gen.strict_canonical_like(impostor)
        assert gen.observe_overrides(impostor) == {}


def test_named_semantic_rivals_are_witnessed_by_generated_examples():
    examples = [gen.generate(1042, index) for index in range(16)]
    for name, rival in gen.SEMANTIC_RIVALS.items():
        assert any(rival(grid) != gen.rule_mirror(grid) for grid in examples), name
    for witness, predicate in gen.SEMANTIC_WITNESSES.items():
        assert any(predicate(grid) for grid in examples), witness


def test_four_demo_lesson_is_identifiable_against_named_competitors():
    demos = []
    for index in range(4):
        grid = gen.generate(500, index)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(501, 7)
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    assert gen.lesson_identifiable(demos, query) == []

    undercovered = demos[:3]
    errors = gen.lesson_identifiable(undercovered, query)
    assert any("sizes 1..4" in error for error in errors)
