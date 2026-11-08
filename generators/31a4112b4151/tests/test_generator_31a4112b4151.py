"""Focused regressions for the anchored-prototype stamping generator."""
from __future__ import annotations

import copy
import hashlib
import importlib
import json
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
TASK_ID = "31a4112b4151"
MODULE = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)


def _canonical_row() -> dict:
    with canonical_path(ROOT).open() as handle:
        return next(row for row in map(json.loads, handle) if row.get("task_id") == TASK_ID)


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *test]


def _freeze(grid):
    return tuple(map(tuple, grid))


def test_rule_hash_is_pinned_to_selected_canonical_program():
    source = " ".join(_canonical_row()["program_solution"].split())
    assert MODULE.RULE_HASH == hashlib.sha256(source.encode()).hexdigest()[:12]
    assert MODULE.RULE_HASH == "1c0487137cc2"


def test_all_canonical_inputs_are_accepted_and_solved_exactly():
    pairs = _canonical_pairs()
    assert len(pairs) == 3
    assert {len(MODULE.analyze_scene(pair["input"])["facts"]["offsets"]) for pair in pairs} == {3, 4}
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert MODULE.self_check(pair["input"]) == []
        assert MODULE.strict_canonical_like(pair["input"]) == []
        assert MODULE._official_output(pair["input"]) == pair["output"]
        assert pair["input"] == before


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_scenes_cover_both_structural_branches_and_shape_sizes(band):
    seen_touch = set()
    seen_clip = set()
    seen_sizes = set()
    for index in range(24):
        grid = MODULE.generate(2000 + index, index, difficulty=band)
        assert MODULE.self_check(grid, difficulty=band) == []
        facts = MODULE.analyze_scene(grid)["facts"]
        seen_touch.add(facts["touch_mode"])
        seen_clip.add(facts["clip_mode"])
        seen_sizes.add(facts["template_size"])
    assert seen_touch == {"isolated", "touching"}
    assert seen_clip == {"none", "partial"}
    assert any(size == 3 for size in seen_sizes)
    assert any(size >= 4 for size in seen_sizes)


def test_declared_override_axes_are_exact_observable_and_composable():
    cases = [
        {"grid_h": 7}, {"grid_h": 12}, {"grid_w": 7}, {"grid_w": 12},
        {"n_anchors": 2}, {"n_anchors": 4},
        {"template_color": 1}, {"template_color": 8},
        {"grid_h": 7, "grid_w": 7, "n_anchors": 4, "template_color": 8},
        {"grid_h": 12, "grid_w": 12, "n_anchors": 2, "template_color": 1},
    ]
    for band in ("easy", "medium", "hard"):
        for index, overrides in enumerate(cases):
            grid = MODULE.generate(5000 + index, index + 3, difficulty=band, **overrides)
            facts = MODULE.analyze_scene(grid)["facts"]
            observed = MODULE.observe_overrides(grid)
            assert facts["height"] == overrides.get("grid_h", facts["height"])
            assert facts["width"] == overrides.get("grid_w", facts["width"])
            for axis in ("n_anchors", "template_color"):
                if axis in overrides:
                    assert observed[axis] == overrides[axis]
            assert MODULE.self_check(
                grid, difficulty=band, meta={"overrides": overrides}
            ) == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"grid_h": 6}, {"grid_h": 13}, {"grid_w": 6}, {"grid_w": 13},
        {"n_anchors": 1}, {"n_anchors": 5},
        {"template_color": 0}, {"template_color": 9},
        {"unknown_axis": 1},
    ],
)
def test_invalid_override_values_fail_closed(overrides):
    with pytest.raises(ValueError):
        MODULE.generate(1, 2, difficulty="medium", **overrides)


def test_task_specific_mutations_are_all_rejected():
    fixtures = MODULE.mutation_fixtures()
    assert len(fixtures) >= 4
    for label, grid in fixtures:
        assert MODULE.self_check(grid), label


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(20260725)
    state = random.getstate()
    first = MODULE.generate(91, 17, difficulty="hard")
    second = MODULE.generate(91, 17, difficulty="hard")
    assert random.getstate() == state
    assert first == second and first is not second
    assert all(left is not right for left, right in zip(first, second))
    frozen = _freeze(second)
    first[0][0] = 8 if first[0][0] != 8 else 7
    assert _freeze(MODULE.generate(91, 17, difficulty="hard")) == frozen


def test_four_demo_curriculum_is_identifiable_against_pinned_rivals():
    grids = [MODULE.generate(800, index, difficulty="medium") for index in range(5)]
    pairs = [{"input": grid, "output": MODULE._official_output(grid)} for grid in grids]
    assert MODULE.lesson_identifiable(pairs[:4], pairs[4]) == []


def test_four_demo_schedule_refutes_first_extra_target_shortcut():
    """Every four-demo window must teach that all color-9 targets are stamped."""
    seed = 24057943068325
    grids = [MODULE.generate(seed, index, difficulty="medium") for index in range(5)]
    pairs = [{"input": grid, "output": MODULE._official_output(grid)} for grid in grids]

    assert MODULE.lesson_identifiable(pairs[:4], pairs[4]) == []


def test_every_semantic_witness_is_declared_as_branch_or_rival_evidence():
    rival_witnesses = set(getattr(MODULE, "WITNESS_RIVALS", {}))
    branch_witnesses = set(MODULE.BRANCH_WITNESSES)

    assert set(MODULE.SEMANTIC_WITNESSES) == rival_witnesses | branch_witnesses


def test_fixed_override_scene_distributes_prototype_origins_across_grid():
    """A capped layout bank must not collapse to its row-major prefix."""
    anchors = []
    for seed in range(32):
        grid = MODULE.generate(
            seed,
            0,
            difficulty="hard",
            grid_h=12,
            grid_w=12,
            n_anchors=4,
            template_color=3,
        )
        anchors.append(MODULE.analyze_scene(grid)["facts"]["anchor"])

    rows = {row for row, _ in anchors}
    cols = {col for _, col in anchors}
    assert len(set(anchors)) >= 20
    assert min(rows) == 0 and max(rows) >= 8
    assert min(cols) == 0 and max(cols) >= 8
