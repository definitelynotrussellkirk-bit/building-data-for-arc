from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


TASK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

SPEC = importlib.util.spec_from_file_location("generator_331074b4dcbc", TASK_DIR / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _grid(rows: list[str]) -> list[list[int]]:
    return [[int(cell) for cell in row] for row in rows]


def _canonical_examples() -> list[tuple[list[list[int]], list[list[int]]]]:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        row = next(json.loads(line) for line in handle if '"task_id": "331074b4dcbc"' in line)
    return [(_grid(example["input"]), _grid(example["output"])) for example in row["train"] + row["test"]]


def test_rule_hash_and_mirror_match_every_canonical_example() -> None:
    assert GEN.RULE_HASH == "663523cb8af9"
    for puzzle_input, expected_output in _canonical_examples():
        assert GEN.self_check(puzzle_input) == []
        assert GEN.rule_mirror(puzzle_input) == expected_output

EXPECTED_PROFILES = (
    "short_left",
    "short_right",
    "short_bottom",
    "long_left",
    "long_center",
    "long_bottom",
    "marker_overlap_left",
    "marker_overlap_right",
)


def test_every_scene_profile_is_exact_observable_and_rule_lawful_in_every_band() -> None:
    assert GEN.SCENE_PROFILES == EXPECTED_PROFILES
    canonical_morphologies = {(6, 12, 4), (6, 12, 5), (5, 13, 4)}
    for difficulty in (None, "easy", "medium", "hard"):
        for index, profile in enumerate(EXPECTED_PROFILES):
            grid = GEN.generate(1000 + index, 2000 + index, difficulty=difficulty, scene_profile=profile)
            assert GEN.self_check(grid, difficulty=difficulty, meta={"overrides": {"scene_profile": profile}}) == []
            assert GEN.observe_overrides(grid) == {"scene_profile": profile}
            assert (len(grid), len(grid[0]), len({value for row in grid for value in row})) in canonical_morphologies
            assert GEN.rule_mirror(grid) != grid


def test_strict_canonical_like_accepts_canonical_and_all_declared_profiles() -> None:
    for puzzle_input, _ in _canonical_examples():
        assert GEN.strict_canonical_like(puzzle_input) == []
    for index, profile in enumerate(EXPECTED_PROFILES):
        grid = GEN.generate(3000 + index, 4000 + index, scene_profile=profile)
        assert GEN.strict_canonical_like(grid) == []


def test_declared_witnesses_are_verified_counterexamples_to_named_rivals() -> None:
    expected_rivals = {
        "rectangle_height_is_tile_period",
        "global_column_phase",
        "continuous_phase_across_rows",
    }
    assert set(GEN.SEMANTIC_RIVALS) == expected_rivals
    assert set(GEN.SEMANTIC_WITNESSES) == {
        "seed_length_decoupled_from_rectangle_height",
        "rectangle_phase_starts_at_its_left_edge",
        "each_rectangle_row_restarts_phase",
    }
    for index, profile in enumerate(EXPECTED_PROFILES):
        grid = GEN.generate(5000 + index, 6000 + index, scene_profile=profile)
        official = GEN.rule_mirror(grid)
        for witness_name, witness in GEN.SEMANTIC_WITNESSES.items():
            assert witness(grid), (profile, witness_name)
            claimed = GEN.WITNESS_RIVALS[witness_name]
            if isinstance(claimed, str):
                claimed = [claimed]
            assert any(GEN.SEMANTIC_RIVALS[name](grid) != official for name in claimed)
    for puzzle_input, expected_output in _canonical_examples():
        assert GEN.CANONICAL_SHORTCUTS["rectangle_height_is_tile_period"](puzzle_input) == expected_output


def test_every_two_demo_window_identifies_the_rule_against_all_declared_competitors() -> None:
    assert GEN.EXAMPLES_NEEDED == 2
    for difficulty in (None, "easy", "medium", "hard"):
        for start in range(12):
            grids = [
                GEN.generate(7000 + start, start * 11 + offset, difficulty=difficulty)
                for offset in range(3)
            ]
            demos = [{"input": grid, "output": GEN.rule_mirror(grid)} for grid in grids[:2]]
            query = {"input": grids[2], "output": GEN.rule_mirror(grids[2])}
            assert GEN.lesson_identifiable(demos, query) == []


def test_semantic_impostors_fail_closed_in_validator_and_rule_mirror() -> None:
    grid = GEN.generate(8080, 9090, scene_profile="long_center")
    facts = GEN._analysis(grid)["facts"]
    top, left, _, _ = facts["rect"]
    hollow = [row[:] for row in grid]
    hollow[top][left] = 0
    assert GEN.self_check(hollow)
    with pytest.raises(ValueError):
        GEN.rule_mirror(hollow)

    wrong_color = [row[:] for row in grid]
    wrong_color[top][left] = 4
    assert GEN.self_check(wrong_color)
    with pytest.raises(ValueError):
        GEN.rule_mirror(wrong_color)

    duplicate_seed = [row[:] for row in grid]
    duplicate_seed[0][1] = duplicate_seed[0][0]
    assert GEN.self_check(duplicate_seed)
    with pytest.raises(ValueError):
        GEN.rule_mirror(duplicate_seed)
