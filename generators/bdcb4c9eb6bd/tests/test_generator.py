"""Portable task-local regression suite for bdcb4c9eb6bd."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    canonical_pairs,
    components,
    four_by_four_only,
    intended_output,
    load_generator,
    non_four_by_four_witness,
    observed,
    witness_input,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "train2", "test0"])
def test_accepts_and_reproduces_every_canonical_pair(pair):
    original = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert intended_output(pair["input"]) == pair["output"]
    assert pair["input"] == original


def test_pins_authority_and_exposes_only_honest_axes():
    assert gen.RULE_HASH == "c507f6de75fe"
    assert set(gen.AXES) == {"scene_profile", "background"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("scene_profile", ["7x9", "11x9", "11x10", "11x15"])
@pytest.mark.parametrize("background", [0, 3, 9])
def test_exact_overrides_are_observable_in_every_band(band, scene_profile, background):
    grid = gen.generate(
        71,
        5,
        difficulty=band,
        scene_profile=scene_profile,
        background=background,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "scene_profile": scene_profile,
        "background": background,
    }
    assert observed(grid)["scene_profile"] == scene_profile
    assert observed(grid)["background"] == background


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"scene_profile": "8x8"},
        {"scene_profile": 79},
        {"background": 1},
        {"background": 2},
        {"background": 10},
        {"background": -1},
        {"background": True},
        {"background": "5"},
    ],
)
def test_rejects_unknown_or_invalid_overrides(overrides):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **overrides)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_three_demo_schedule_refutes_four_by_four_shortcut_for_every_cyclic_start(band):
    seed = 311
    pairs = []
    for index in range(15):
        grid = gen.generate(seed, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(seed, index, difficulty=band)
        pairs.append({"input": grid, "output": intended_output(grid)})
    for start in range(12):
        demos = pairs[start:start + 3]
        query = pairs[start + 3]
        assert any(four_by_four_only(pair["input"]) != pair["output"] for pair in demos)
        assert gen.lesson_identifiable(demos, query) == []


def test_declared_shortcut_fits_canonical_but_exact_witness_disagrees():
    rival = gen.CANONICAL_SHORTCUTS["four_by_four_only"]
    assert gen.SEMANTIC_RIVALS["four_by_four_only"] is rival
    assert gen.LESSON_COMPETITORS["four_by_four_only"] is rival
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())

    grid = witness_input()
    assert gen.self_check(grid) == []
    assert gen.SEMANTIC_WITNESSES["non_4x4_rectangle"](grid)
    assert non_four_by_four_witness(grid)
    assert rival(grid) == four_by_four_only(grid)
    assert rival(grid) != intended_output(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_covers_profiles_borders_multiple_objects_and_all_gap_sides(band):
    profiles = set()
    sides = set()
    saw_border = saw_multi = saw_non_four = False
    unique = set()
    for index in range(160):
        grid = gen.generate(9000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        info = observed(grid)
        profiles.add(info["scene_profile"])
        sides.update(info["sides"])
        saw_border |= any(info["touches_border"])
        saw_multi |= info["rectangle_count"] > 1
        saw_non_four |= non_four_by_four_witness(grid)
        unique.add(repr(grid))
        assert intended_output(grid) != grid
    assert profiles == {"7x9", "11x9", "11x10", "11x15"}
    assert sides == {"up", "down", "left", "right"}
    assert saw_border and saw_multi and saw_non_four
    assert len(unique) >= 150


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True, 1], [1, 1]],
        [[0, 0], [0, 0]],
        [[7, 7, 7], [7, 4, 7], [7, 7, 7]],
    ],
)
def test_malformed_grids_return_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)


def test_rule_mirror_and_rival_are_input_pure():
    grid = witness_input()
    before = deepcopy(grid)
    assert intended_output(grid) != four_by_four_only(grid)
    assert grid == before
    assert gen._apply_intended(grid) == intended_output(grid)
    assert grid == before
    assert gen._four_by_four_only(grid) == four_by_four_only(grid)
    assert grid == before


def test_schedule_profile_is_period_three_and_names_the_witness_geometry():
    assert gen.EXAMPLES_NEEDED == 3
    assert [gen.schedule_profile(0, i, "medium") for i in range(6)] == [
        "canonical_4x4",
        "wide_4x5",
        "tall_5x4",
        "canonical_4x4",
        "wide_4x5",
        "tall_5x4",
    ]
    for index, size in enumerate(((4, 4), (4, 5), (5, 4))):
        grid = gen.generate(51, index, scene_profile="7x9", background=5)
        assert size in observed(grid)["sizes"]


def test_axes_metadata_is_statically_literal_for_the_repository_linter():
    import ast

    tree = ast.parse((HOME / "generator.py").read_text())
    assignment = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AXES" for target in node.targets)
    )
    assert not any(isinstance(node, (ast.Call, ast.Name)) for node in ast.walk(assignment.value))
