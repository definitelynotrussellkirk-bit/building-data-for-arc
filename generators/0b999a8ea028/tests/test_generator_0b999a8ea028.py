"""Focused contract and semantic tests for generator 0b999a8ea028."""
from __future__ import annotations

import copy
import importlib.util
import itertools
import json
import random
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("assigned_generator_0b999a8ea028", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def canonical_pairs():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != GEN.TASK_ID:
            continue
        pairs = list(row["train"])
        test = row["test"]
        pairs.extend(test if isinstance(test, list) else [test])
        return pairs
    raise AssertionError(f"canonical row missing for {GEN.TASK_ID}")


def as_pair(seed: int, sample_index: int, difficulty: str = "medium"):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def key(grid):
    return tuple(tuple(row) for row in grid)


def test_identity_and_contract_constants_are_pinned():
    assert GEN.GENERATOR_ID == GEN.TASK_ID == "0b999a8ea028"
    assert GEN.VERSION == "3.0.0"
    assert GEN.RULE_HASH == "d8a130fd2a56"
    assert GEN.EXAMPLES_NEEDED == 4
    assert set(GEN.AXES) == {"grid_h", "grid_w", "texture"}
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "canonical",
        "size_contest",
        "nonframe_blue",
        "no_frames",
    )


@pytest.mark.parametrize("pair", canonical_pairs())
def test_every_canonical_pair_is_accepted_and_mirrored_exactly(pair):
    original = copy.deepcopy(pair["input"])
    assert GEN.self_check(pair["input"]) == []
    assert GEN.strict_canonical_like(pair["input"]) == []
    assert GEN.rule_mirror(pair["input"]) == pair["output"]
    assert pair["input"] == original


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_each_four_example_window_covers_every_semantic_profile(difficulty):
    for start in range(8):
        grids = [GEN.generate(7001 + start, start + offset, difficulty=difficulty)
                 for offset in range(4)]
        signatures = [GEN.semantic_signature(grid) for grid in grids]
        assert {item["texture"] for item in signatures} == set(GEN.SCHEDULE_PROFILES)
        assert all(GEN.self_check(grid) == [] for grid in grids)
        assert all(GEN.rule_mirror(grid) != grid for grid in grids)
        assert all(any(cell for row in grid for cell in row) for grid in grids)


def test_generated_profiles_expose_the_intended_counterexamples():
    grids = {
        profile: GEN.generate(90210, index, difficulty="medium", texture=profile)
        for index, profile in enumerate(GEN.SCHEDULE_PROFILES)
    }
    answer = {name: GEN.rule_mirror(grid) for name, grid in grids.items()}

    assert GEN.SEMANTIC_WITNESSES["decoy_precedes_largest"](grids["size_contest"])
    assert GEN.SEMANTIC_RIVALS["first_nonblue"](grids["size_contest"]) != answer["size_contest"]

    assert GEN.SEMANTIC_WITNESSES["generalized_frame"](grids["size_contest"])
    assert GEN.SEMANTIC_RIVALS["fixed_5x5_frames"](grids["size_contest"]) != answer["size_contest"]

    assert GEN.SEMANTIC_WITNESSES["positive_center_offset"](grids["size_contest"])
    assert GEN.SEMANTIC_RIVALS["interior_top_left"](grids["size_contest"]) != answer["size_contest"]

    assert GEN.SEMANTIC_WITNESSES["nonframe_blue_component"](grids["nonframe_blue"])
    assert GEN.SEMANTIC_RIVALS["any_blue_bbox"](grids["nonframe_blue"]) != answer["nonframe_blue"]

    assert not any(cell for row in answer["no_frames"] for cell in row)


def test_declared_canonical_shortcuts_fit_public_pairs_but_generated_witnesses_refute_them():
    pairs = canonical_pairs()
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name

    generated = [GEN.generate(1701, index, difficulty="hard") for index in range(4)]
    for name, shortcut in GEN.CANONICAL_SHORTCUTS.items():
        assert any(shortcut(grid) != GEN.rule_mirror(grid) for grid in generated), name


def test_four_generated_demos_identify_the_lesson_against_all_declared_competitors():
    for start in range(8):
        demos = [as_pair(8100 + start, start + offset, difficulty="medium")
                 for offset in range(4)]
        query = as_pair(9100 + start, start + 4, difficulty="medium")
        assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_exact_override_cartesian_boundaries_are_honored_and_observable(difficulty):
    domains = ((11, 18), (11, 20), GEN.SCHEDULE_PROFILES)
    for index, (height, width, texture) in enumerate(itertools.product(*domains)):
        requested = {"grid_h": height, "grid_w": width, "texture": texture}
        grid = GEN.generate(12000 + index, index, difficulty=difficulty, **requested)
        assert GEN.self_check(grid, meta={"overrides": requested}) == []
        assert GEN.observe_overrides(grid) == requested
        assert len(grid) == height
        assert len(grid[0]) == width

    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 0, typo_axis="must-not-be-ignored")


def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    random.seed(8675309)
    state = random.getstate()
    first = GEN.generate(88, 2, difficulty="medium")
    assert random.getstate() == state
    second = GEN.generate(88, 2, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    pristine = copy.deepcopy(second)
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == pristine


def test_strict_anchor_has_nontrivial_support_in_every_band():
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(4300 + index, index, difficulty=difficulty)
                 for index in range(40)]
        strict = sum(GEN.strict_canonical_like(grid) == [] for grid in grids)
        assert strict >= 12
        assert len({key(grid) for grid in grids}) >= 32


def test_self_check_rejects_a_broken_frame_mutation():
    grid = GEN.generate(44, 0, texture="canonical", grid_h=11, grid_w=11)
    analysis = GEN.analyze_scene(grid)
    frame = analysis["frames"][0]
    mutated = copy.deepcopy(grid)
    mutated[frame["r1"]][frame["c1"] + 1] = 0
    assert GEN.self_check(mutated)
