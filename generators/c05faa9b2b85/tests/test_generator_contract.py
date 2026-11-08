"""Focused contract tests for the c05faa9b2b85 chamber-fill generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "c05faa9b2b85"
HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
_SPEC = importlib.util.spec_from_file_location(f"test_generator_{TASK_ID}", GENERATOR_PATH)
assert _SPEC and _SPEC.loader
GEN = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(GEN)


def _pairs():
    return canonical_pairs(TASK_ID, root=find_root(__file__))


def _lesson(seed: int, start: int, difficulty: str = "medium"):
    grids = [GEN.generate(seed, start + offset, difficulty=difficulty) for offset in range(4)]
    pairs = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids]
    return pairs[:3], pairs[3]


def test_rule_pin_and_python_mirror_match_every_canonical_pair():
    assert GEN.RULE_HASH == "080731f15c8c"
    for pair in _pairs():
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(deepcopy(pair["input"])) == pair["output"]


@pytest.mark.parametrize("scene_profile", ["canonical_rectangles", "single_notch", "double_notch"])
@pytest.mark.parametrize("canvas_profile", ["canonical_10x14", "canonical_11x15", "canonical_12x16"])
@pytest.mark.parametrize("n_rooms", [2, 3, 4])
def test_every_advertised_override_combination_is_constructive_and_observable(
    scene_profile, canvas_profile, n_rooms
):
    grid = GEN.generate(
        1701,
        23,
        difficulty="hard",
        scene_profile=scene_profile,
        canvas_profile=canvas_profile,
        n_rooms=n_rooms,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "scene_profile": scene_profile,
        "canvas_profile": canvas_profile,
        "n_rooms": n_rooms,
    }
    assert GEN.rule_mirror(grid) != grid


def test_semantic_profiles_supply_both_declared_counterexamples():
    for profile in ("single_notch", "double_notch"):
        grid = GEN.generate(712, 9, scene_profile=profile, n_rooms=4)
        truth = GEN.rule_mirror(grid)
        assert GEN.strict_canonical_like(grid)
        assert GEN.SEMANTIC_WITNESSES["irregular_active_region"](grid)
        assert GEN.SEMANTIC_WITNESSES["multi_color_region"](grid)
        assert GEN.SEMANTIC_RIVALS["rectangular_regions_only"](deepcopy(grid)) != truth
        assert GEN.SEMANTIC_RIVALS["first_color_wins"](deepcopy(grid)) != truth


def test_semantic_profiles_refute_exactly_one_marker_cell_shortcut():
    for profile in ("single_notch", "double_notch"):
        grid = GEN.generate(19_337, 5, scene_profile=profile, n_rooms=2)
        truth = GEN.rule_mirror(grid)
        assert GEN.SEMANTIC_WITNESSES["repeated_same_color_markers"](grid)
        assert GEN.SEMANTIC_RIVALS["exactly_one_marker_cell"](deepcopy(grid)) != truth


def test_declared_shortcuts_fit_all_canonical_pairs():
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(deepcopy(pair["input"])) == pair["output"] for pair in _pairs()), name


def test_every_consecutive_three_demo_lesson_refutes_all_competitors():
    for start in range(12):
        demos, query = _lesson(44_000 + start, start)
        assert GEN.lesson_identifiable(demos, query) == []
        for name, rival in GEN.LESSON_COMPETITORS.items():
            assert not all(rival(deepcopy(pair["input"])) == pair["output"] for pair in demos), name


def test_default_distribution_is_deterministic_nonidentity_and_noncollapsed():
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(9100 + i, i, difficulty=band) for i in range(60)]
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert all(GEN.rule_mirror(grid) != grid for grid in grids)
        assert all(grid == GEN.generate(9100 + i, i, difficulty=band) for i, grid in enumerate(grids))
        assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) >= 55
        assert {GEN.observe_overrides(grid)["scene_profile"] for grid in grids} == set(GEN.SCENE_PROFILES)


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo_axis": 1},
        {"scene_profile": "unknown"},
        {"canvas_profile": "unknown"},
        {"n_rooms": 1},
        {"n_rooms": 5},
        {"n_rooms": 2.5},
        {"n_rooms": True},
    ],
)
def test_invalid_overrides_fail_loudly(overrides):
    with pytest.raises((TypeError, ValueError, KeyError)):
        GEN.generate(1, 1, **overrides)


def test_difficulty_bands_have_observable_default_canvas_profiles():
    for sample_index in range(9):
        observed = {
            band: GEN.observe_overrides(
                GEN.generate(81_000 + sample_index, sample_index, difficulty=band)
            )["canvas_profile"]
            for band in ("easy", "medium", "hard")
        }
        assert observed == {
            "easy": "canonical_10x14",
            "medium": "canonical_11x15",
            "hard": "canonical_12x16",
        }
