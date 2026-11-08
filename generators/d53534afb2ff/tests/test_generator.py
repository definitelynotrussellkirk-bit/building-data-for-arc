"""Regression contract for the d53534afb2ff containment curriculum."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest

TASK_ID = "d53534afb2ff"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if RUNTIME.is_dir() and str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    source = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("review_d53534afb2ff", source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__))


def test_contract_metadata_and_hooks_are_complete():
    assert GEN.RULE_HASH == "372b08419c67"
    assert set(GEN.AXES) == {"scene_profile"}
    assert GEN.EXAMPLES_NEEDED == 4
    assert set(GEN.SCENE_PROFILES) == {
        "two_singletons",
        "outside_same_color",
        "multi_cell",
        "multiple_inside",
    }
    for name in (
        "observe_overrides",
        "rule_mirror",
        "self_check",
        "strict_canonical_like",
        "schedule_profile",
    ):
        assert callable(getattr(GEN, name))


@pytest.mark.parametrize("pair", PAIRS, ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_all_canonical_pairs_are_accepted_and_mirrored(pair):
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "profile",
    [
        "two_singletons",
        "outside_same_color",
        "multi_cell",
        "multiple_inside",
    ],
)
def test_every_scene_profile_is_exact_observable_and_lawful(difficulty, profile):
    grid = GEN.generate(431, 7, difficulty=difficulty, scene_profile=profile)
    assert GEN.self_check(grid, difficulty=difficulty) == []
    assert GEN.strict_canonical_like(grid) == []
    assert GEN.observe_overrides(grid) == {"scene_profile": profile}
    assert GEN.rule_mirror(grid) != grid


def test_default_schedule_puts_all_four_teaching_profiles_in_every_four_examples():
    expected = set(GEN.SCENE_PROFILES)
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            observed = {
                GEN.observe_overrides(
                    GEN.generate(9821, start + offset, difficulty=difficulty)
                )["scene_profile"]
                for offset in range(GEN.EXAMPLES_NEEDED)
            }
            assert observed == expected


def test_default_generation_is_deterministic_input_pure_and_globally_rng_pure():
    state = random.getstate()
    for difficulty in ("easy", "medium", "hard"):
        for index in range(24):
            first = GEN.generate(7712, index, difficulty=difficulty)
            second = GEN.generate(7712, index, difficulty=difficulty)
            assert first == second
            before = deepcopy(first)
            output = GEN.rule_mirror(first)
            assert first == before
            assert output != first
            assert GEN.self_check(first) == []
    assert random.getstate() == state


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo_axis": "multi_cell"},
        {"scene_profile": "not-a-profile"},
        {"scene_profile": 3},
    ],
)
def test_invalid_overrides_fail_loudly(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(1, 0, **kwargs)


def test_declared_color_three_shortcut_fits_every_canonical_pair():
    shortcut = GEN.CANONICAL_SHORTCUTS["color_three_only"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in PAIRS)


def test_generated_non_three_witness_refutes_color_three_shortcut():
    grid = GEN.generate(72, 3, scene_profile="multiple_inside")
    assert GEN.SEMANTIC_WITNESSES["non_three_inside"](grid)
    assert GEN.SEMANTIC_RIVALS["color_three_only"](grid) != GEN.rule_mirror(grid)


def test_generated_large_object_witness_refutes_at_most_two_cells_shortcut():
    grid = GEN.generate(73, 2, difficulty="hard", scene_profile="multi_cell")
    assert GEN.SEMANTIC_WITNESSES["large_inside_object"](grid)
    assert GEN.SEMANTIC_RIVALS["at_most_two_cells"](grid) != GEN.rule_mirror(grid)


def test_generated_multi_object_witness_refutes_first_object_only_shortcut():
    grid = GEN.generate(74, 3, scene_profile="multiple_inside")
    assert GEN.SEMANTIC_WITNESSES["multiple_objects_one_frame"](grid)
    assert GEN.SEMANTIC_RIVALS["first_object_only"](grid) != GEN.rule_mirror(grid)


def test_outside_same_color_object_is_left_unchanged():
    grid = GEN.generate(75, 1, scene_profile="outside_same_color")
    output = GEN.rule_mirror(grid)
    assert GEN.SEMANTIC_WITNESSES["outside_same_color"](grid)
    analysis = GEN.analyze_scene(grid)
    assert analysis["errors"] == []
    outside = analysis["outside_objects"]
    assert outside
    for obj in outside:
        for row, col in obj["cells"]:
            assert output[row][col] == grid[row][col]


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True, 0]]])
def test_malformed_inputs_return_diagnostics_not_exceptions(grid):
    assert GEN.self_check(grid)


def test_self_check_rejects_a_broken_frame_and_an_uncontained_profile():
    grid = GEN.generate(91, 0, scene_profile="two_singletons")
    analysis = GEN.analyze_scene(grid)
    frame_cell = analysis["frames"][0]["cells"][0]
    grid[frame_cell[0]][frame_cell[1]] = 0
    assert GEN.self_check(grid)


def test_examples_needed_is_a_literal_integer_for_solve_episode_builder():
    import ast

    source = (HOME / "generator.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    assignments = [
        node
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(
            isinstance(target, ast.Name) and target.id == "EXAMPLES_NEEDED"
            for target in (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
        )
    ]
    assert len(assignments) == 1
    value = ast.literal_eval(assignments[0].value)
    assert type(value) is int and value == 4


def test_each_profile_varies_role_colors_instead_of_encoding_a_fixed_palette():
    """A profile name/canvas shape must not imply one memorized color mapping."""
    for profile in GEN.SCENE_PROFILES:
        signatures = set()
        frame_colors = set()
        inside_colors = set()
        for seed in range(32):
            grid = GEN.generate(seed, 0, difficulty="medium", scene_profile=profile)
            analysis = GEN.analyze_scene(grid)
            assert analysis["errors"] == []
            frames = tuple(sorted(frame["color"] for frame in analysis["frames"]))
            targets = tuple(sorted(obj["color"] for obj in analysis["inside_objects"]))
            signatures.add((frames, targets))
            frame_colors.update(frames)
            inside_colors.update(targets)
        assert len(signatures) >= 8, (profile, signatures)
        assert len(frame_colors) >= 4, (profile, frame_colors)
        assert len(inside_colors) >= 4, (profile, inside_colors)
