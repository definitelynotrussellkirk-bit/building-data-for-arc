from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path
import importlib.util

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location(
    "generator_edf83166c155", Path(__file__).resolve().parents[1] / "generator.py"
)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _paint(grid, top, left, shape, colour):
    for row, col in shape:
        grid[top + row][left + col] = colour


def test_rule_hash_and_all_canonical_pairs_are_pinned():
    authority = canonical_path(ROOT)
    rows = [json.loads(line) for line in authority.read_text().splitlines()
            if line.strip() and json.loads(line).get("task_id") == GEN.TASK_ID]
    assert rows
    normalized = " ".join(rows[0]["program_solution"].split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == GEN.RULE_HASH
    pairs = canonical_pairs(GEN.TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_generation_is_deterministic_fresh_and_rng_pure():
    random.seed(99117)
    state = random.getstate()
    first = GEN.generate(117, 9, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(117, 9, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == GEN.generate(117, 9, difficulty="hard")


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_four_profile_schedule_covers_semantic_rivals(difficulty):
    demos = []
    witness_hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for sample_index in range(4):
        grid = GEN.generate(42, sample_index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        output = GEN.rule_mirror(grid)
        demos.append({"input": grid, "output": output})
        for name, predicate in GEN.SEMANTIC_WITNESSES.items():
            witness_hits[name] += bool(predicate(grid))
    assert set(GEN.schedule_profile(42, i, difficulty) for i in range(4)) == set(
        GEN.SCHEDULE_PROFILES
    )
    assert all(count >= 1 for count in witness_hits.values())
    query_grid = GEN.generate(42, 4, difficulty=difficulty)
    assert GEN.lesson_identifiable(
        demos,
        {"input": query_grid, "output": GEN.rule_mirror(query_grid)},
    ) == []


def test_named_rival_regression_witnesses():
    first_conflict = GEN.generate(9, 0, difficulty="medium")
    size_conflict = GEN.generate(9, 1, difficulty="medium")
    last_conflict = GEN.generate(0, 0, difficulty="medium")
    axis_conflict = GEN.generate(9, 3, difficulty="medium")
    assert GEN._target_not_first(first_conflict)
    assert GEN._first_object_rule(first_conflict) != GEN.rule_mirror(first_conflict)
    assert GEN._target_not_largest(size_conflict)
    assert GEN._largest_object_rule(size_conflict) != GEN.rule_mirror(size_conflict)
    assert GEN._target_not_last(last_conflict)
    assert GEN._last_object_rule(last_conflict) != GEN.rule_mirror(last_conflict)
    assert GEN._has_earlier_non_lr_axis_symmetric_distractor(axis_conflict)
    assert GEN._any_axis_symmetry_rule(axis_conflict) != GEN.rule_mirror(axis_conflict)

    analyses = [GEN._analysis(GEN.generate(9, i, difficulty="medium")) for i in range(4)]
    target_ranks = {a["components"].index(a["target"]) for a in analyses}
    target_zones = {
        (
            "top" if a["target"]["top"] < a["height"] // 2 else "bottom",
            "left" if a["target"]["left"] < a["width"] // 2 else "right",
        )
        for a in analyses
    }
    assert len(target_ranks) >= 2
    assert len(target_zones) >= 3


def test_exact_axis_boundaries_and_unknown_override_rejection():
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (9, 15):
            for grid_w in (10, 17):
                overrides = {"grid_h": grid_h, "grid_w": grid_w}
                grid = GEN.generate(17, 7, difficulty=difficulty, **overrides)
                assert GEN.observe_overrides(grid) == overrides
                assert GEN.self_check(
                    grid,
                    difficulty=difficulty,
                    meta={"overrides": overrides},
                ) == []
    with pytest.raises(KeyError, match="unknown override"):
        GEN.generate(17, 2, palette_kind="warm")


def test_mutation_impostors_are_rejected():
    base = GEN.generate(51, 0, difficulty="medium")
    analysis = GEN._analysis(base)

    no_target = copy.deepcopy(base)
    for row, col in analysis["target"]["cells"]:
        no_target[row][col] = 0
    assert GEN.self_check(no_target)

    duplicate_target = [[0] * 12 for _ in range(10)]
    _paint(duplicate_target, 0, 0, GEN._U_TARGET, 1)
    _paint(duplicate_target, 6, 8, GEN._T_TARGET, 2)
    _paint(duplicate_target, 0, 8, GEN._L4_TALL, 3)
    assert GEN.self_check(duplicate_target)

    solid_target = [[0] * 12 for _ in range(10)]
    _paint(solid_target, 0, 0, ((0, 0), (0, 1), (0, 2)), 1)
    _paint(solid_target, 0, 8, GEN._L4_TALL, 2)
    _paint(solid_target, 6, 8, GEN._S4_WIDE, 3)
    assert any("solid" in reason for reason in GEN.self_check(solid_target))

    touching = [[0] * 12 for _ in range(10)]
    _paint(touching, 0, 0, GEN._U_TARGET, 1)
    _paint(touching, 2, 3, GEN._L4_TALL, 2)  # diagonal/edge-ring collision
    _paint(touching, 6, 8, GEN._S4_WIDE, 3)
    assert any("ring" in reason for reason in GEN.self_check(touching))


def test_negative_recombination_is_lawful_but_not_strict_canonical():
    # Exact canonical dimensions alone are insufficient: the size-conflict
    # morphology is a lawful generalized lesson but not an empirical-manifold
    # match.  This guards against weakening strict_canonical_like to marginals.
    grid = GEN.generate(
        73,
        1,
        difficulty="medium",
        grid_h=10,
        grid_w=12,
    )
    assert GEN.self_check(grid) == []
    reasons = GEN.strict_canonical_like(grid)
    assert reasons
    assert any("morphology" in reason for reason in reasons)


def _quadrant(component, height, width):
    vertical = "top" if component["top"] < height // 2 else "bottom"
    horizontal = "left" if component["left"] < width // 2 else "right"
    return {
        ("top", "left"): "tl",
        ("top", "right"): "tr",
        ("bottom", "left"): "bl",
        ("bottom", "right"): "br",
    }[(vertical, horizontal)]


def _retained_scaffold_rival(grid):
    analysis = GEN._analysis(grid)
    assert analysis["errors"] == []
    by_region = {
        _quadrant(component, analysis["height"], analysis["width"]): component
        for component in analysis["components"]
    }
    top_left = by_region["tl"]
    if top_left["bbox_w"] >= 4:
        chosen = by_region["br"]
    elif "tr" in by_region:
        chosen = by_region["tr"]
    else:
        chosen = by_region["bl"]
    return GEN._crop_component(grid, chosen)


def test_schedule_uses_all_quadrants_and_breaks_retained_scaffold_rival():
    grids = [GEN.generate(20261026, index, difficulty="medium") for index in range(4)]
    target_regions = {
        _quadrant(
            GEN._analysis(grid)["target"],
            len(grid),
            len(grid[0]),
        )
        for grid in grids
    }
    assert target_regions == {"tl", "tr", "bl", "br"}
    assert any(_retained_scaffold_rival(grid) != GEN.rule_mirror(grid) for grid in grids)
