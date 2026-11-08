"""Focused regressions for the cf4fdf474ad5 generator repair."""
from __future__ import annotations

import copy
import importlib.util
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "cf4fdf474ad5"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location(f"task_{TASK_ID}_reviewed", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(GEN)


def _pairs():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _labeled(seed: int, index: int, difficulty: str | None = None):
    grid = GEN.generate(seed, index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_metadata_pins_authority_and_exact_axes():
    assert GEN.GENERATOR_ID == GEN.TASK_ID == TASK_ID
    assert GEN.RULE_HASH == "9316ff1c04fa"
    assert GEN.VERSION == "3.0.0"
    assert GEN.EXAMPLES_NEEDED == 3
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_patches"}


@pytest.mark.parametrize("pair", _pairs(), ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_accepts_every_canonical_input_and_matches_label(pair):
    source = copy.deepcopy(pair["input"])
    assert GEN.self_check(source) == []
    assert GEN.strict_canonical_like(source) == []
    assert GEN.rule_mirror(source) == pair["output"]
    assert source == pair["input"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 22, "grid_w": 22, "n_patches": 3},
        {"grid_h": 28, "grid_w": 28, "n_patches": 4},
        {"grid_h": 23, "grid_w": 24, "n_patches": 4},
    ],
)
def test_exact_overrides_round_trip_from_pixels(difficulty, requested):
    grid = GEN.generate(71, 19, difficulty=difficulty, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 1},
        {"grid_h": 21},
        {"grid_h": 29},
        {"grid_w": True},
        {"grid_w": 24.0},
        {"n_patches": 2},
        {"n_patches": 5},
        {"n_patches": "4"},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("sample_index", [True, False, -1, 1.0, "1"])
def test_invalid_sample_indices_are_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_draws_are_deterministic_fresh_and_global_rng_pure(difficulty):
    state = random.getstate()
    first = GEN.generate(1234, 37, difficulty=difficulty)
    pristine = copy.deepcopy(first)
    first[0][0] = 9 if first[0][0] != 9 else 1
    second = GEN.generate(1234, 37, difficulty=difficulty)
    assert second == pristine
    assert second is not first
    assert all(a is not b for a, b in zip(second, first))
    assert random.getstate() == state


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_default_distribution_constructs_all_semantic_counterexamples(difficulty):
    profiles = set()
    shapes = set()
    mono_counts = []
    for index in range(96):
        grid = GEN.generate(10_000 + index, index, difficulty=difficulty)
        assert GEN.self_check(grid) == []
        facts = GEN.semantic_observables(grid)
        profiles.add(facts["profile"])
        shapes.add((facts["grid_h"], facts["grid_w"]))
        mono_counts.append(facts["monochrome_object_count"])
        assert facts["n_patches"] == 4
        assert facts["eligible_count"] >= 3
        assert facts["invalid_tall_count"] >= 1
        assert facts["invalid_max_green"] > facts["winner_green"]
        assert facts["largest_valid_area"] > facts["winner_area"]
        assert facts["highest_valid_density"] > facts["winner_density"]
        assert facts["winner_component_index"] not in (0, facts["n_patches"] - 1)
        for name in ("height_gate", "absolute_count", "area_not_size", "not_first_patch"):
            assert GEN.SEMANTIC_WITNESSES[name](grid)
    assert profiles == {"unique", "tie_area"}
    assert {(24, 24), (23, 23), (22, 22), (22, 24)} <= shapes
    assert min(mono_counts) >= 18
    assert max(mono_counts) >= 30


def test_tie_profile_breaks_canonical_fitting_top_left_shortcut():
    tie = GEN.generate(8, 1)
    facts = GEN.semantic_observables(tie)
    assert facts["profile"] == "tie_area"
    assert facts["winner_green"] == facts["max_valid_green"]
    assert facts["max_valid_green_tied"]
    assert GEN.rule_mirror(tie) != GEN.CANONICAL_SHORTCUTS["top_left_on_tie"](tie)
    assert GEN.SEMANTIC_WITNESSES["smaller_area_tie_break"](tie)


def test_declared_canonical_shortcut_really_fits_every_labeled_pair():
    shortcut = GEN.CANONICAL_SHORTCUTS["top_left_on_tie"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in _pairs())


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_consecutive_lesson_and_rotation_is_identifiable(difficulty):
    for start in range(12):
        pairs = [_labeled(700 + start, start + offset, difficulty) for offset in range(4)]
        assert GEN.lesson_identifiable(pairs[:3], pairs[3]) == []
        for query_index in range(4):
            demos = [pair for i, pair in enumerate(pairs) if i != query_index]
            assert GEN.lesson_identifiable(demos, pairs[query_index]) == []


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True for _ in range(22)] for _ in range(22)],
    ],
)
def test_malformed_inputs_are_diagnostic(grid):
    assert GEN.self_check(grid)


def test_validator_rejects_holes_unknown_colors_and_no_eligible_patch():
    grid = GEN.generate(5, 0)
    facts = GEN._analyze(grid)

    hole = copy.deepcopy(grid)
    cell = next(iter(facts["components"][0]["cells"]))
    hole[cell[0]][cell[1]] = 0
    assert GEN.self_check(hole)

    unknown = copy.deepcopy(grid)
    unknown[0][0] = 7
    assert GEN.self_check(unknown)

    no_eligible = [[0] * 24 for _ in range(24)]
    for top, left in ((0, 0), (0, 9), (11, 0)):
        for row in range(top, top + 9):
            for col in range(left, left + 7):
                no_eligible[row][col] = 8
        no_eligible[top][left] = 3
    assert GEN.self_check(no_eligible)


def test_rule_mirror_is_input_pure_and_returns_exact_crop():
    grid = GEN.generate(91, 3)
    original = copy.deepcopy(grid)
    output = GEN.rule_mirror(grid)
    assert grid == original
    winner = GEN._analyze(grid)["winner"]
    expected = [row[winner["c1"] : winner["c2"] + 1] for row in grid[winner["r1"] : winner["r2"] + 1]]
    assert output == expected
    assert (len(output), len(output[0])) == (winner["height"], winner["width"])


def test_retained_top_left_tie_counterexample_replays_exactly():
    import hashlib
    import json

    witness_dir = HOME / "counterexamples" / "top-left-on-tie"
    metadata = json.loads((witness_dir / "witness_metadata.json").read_text())
    racket = json.loads((witness_dir / "racket.json").read_text())
    source_sha = hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest()

    assert metadata["generator_sha256"] == source_sha
    assert metadata["rule_hash"] == GEN.RULE_HASH
    assert metadata["rival_name"] == "top_left_on_tie"
    grid = metadata["input"]
    assert GEN.generate(
        metadata["seed"],
        metadata["sample_index"],
        difficulty=metadata["difficulty"],
    ) == grid
    assert GEN.self_check(grid, difficulty=metadata["difficulty"]) == []
    intended = GEN.rule_mirror(grid)
    rival = GEN.CANONICAL_SHORTCUTS[metadata["rival_name"]](grid)
    assert intended == metadata["intended_python_mirror"]
    assert rival == metadata["rival_output"]
    assert intended != rival
    assert racket["executed_rule_hash"] == GEN.RULE_HASH
    assert racket["generator_sha256"] == source_sha
    assert racket["results"][0]["generator_domain"] == {"status": "valid", "errors": []}
    assert racket["results"][0]["output"] == intended
