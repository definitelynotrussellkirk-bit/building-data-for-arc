from __future__ import annotations

import copy
import importlib
import json
import random
from pathlib import Path

import pytest


TASK_ID = "78da31e156b0"
GEN = importlib.import_module(
    f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
)
ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "data" / "canonical" / "puzzles.jsonl"


def _canonical_row():
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical task {TASK_ID} not found")


def test_canonical_inputs_are_accepted_and_python_mirror_matches_all_pairs():
    row = _canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 5
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_center_is_preserved_and_only_diagonal_arms_are_added():
    grid = [[0] * 7 for _ in range(7)]
    grid[3][3] = 6
    # This grid has an undeclared one-seed signature, so use the pure stencil
    # competitor/mirror primitive through a declared single-seed profile.
    declared = GEN.generate(17, 3, difficulty="easy")
    output = GEN.rule_mirror(declared)
    seeds = GEN._seed_cells(declared)
    assert len(seeds) == 1
    row, col, color = seeds[0]
    assert output[row][col] == color
    for delta_row, delta_col in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        next_row, next_col = row + delta_row, col + delta_col
        if 0 <= next_row < len(output) and 0 <= next_col < len(output[0]):
            assert output[next_row][next_col] == color
    for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        next_row, next_col = row + delta_row, col + delta_col
        if 0 <= next_row < len(output) and 0 <= next_col < len(output[0]):
            assert output[next_row][next_col] == 0


def test_every_scene_profile_override_is_exact_and_observable_in_every_band():
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(GEN.SCENE_PROFILES):
            grid = GEN.generate(
                1000 + index,
                2000 + index,
                difficulty=band,
                scene_profile=profile,
            )
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == {"scene_profile": profile}


def test_default_schedule_makes_every_four_demo_window_identifiable():
    for start in range(len(GEN.SCENE_PROFILES) * 2):
        demos = []
        for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
            grid = GEN.generate(31337, sample_index, difficulty="hard")
            demos.append({"input": grid, "output": GEN.rule_mirror(grid)})
        query_grid = GEN.generate(
            31337, start + GEN.EXAMPLES_NEEDED, difficulty="hard"
        )
        assert GEN.lesson_identifiable(
            demos, {"input": query_grid, "output": GEN.rule_mirror(query_grid)}
        ) == []


def test_self_check_rejects_targeted_impostors():
    valid = GEN.generate(
        44,
        0,
        difficulty="medium",
        scene_profile="canonical_7x7_two_interior",
    )
    assert GEN.self_check(valid) == []

    blank = [[0] * 7 for _ in range(7)]
    adjacent = [[0] * 7 for _ in range(7)]
    adjacent[2][2] = 3
    adjacent[2][3] = 4
    overlapping_xs = [[0] * 7 for _ in range(7)]
    overlapping_xs[2][2] = 3
    overlapping_xs[2][4] = 4
    wrong_palette_count = copy.deepcopy(valid)
    seed_cells = GEN._seed_cells(wrong_palette_count)
    for row, col, _ in seed_cells:
        wrong_palette_count[row][col] = 5
    ragged = [[0, 0, 0], [0, 1]]

    for impostor in (blank, adjacent, overlapping_xs, wrong_palette_count, ragged):
        assert GEN.self_check(impostor), impostor


def test_unknown_override_rejected_and_replay_is_fresh_and_rng_pure():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, difficulty="easy", typo_axis="bad")
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, difficulty="easy", palette_kind="warm")

    random.seed(991)
    state_before = random.getstate()
    first = GEN.generate(51, 7, difficulty="medium")
    state_after = random.getstate()
    second = GEN.generate(51, 7, difficulty="medium")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    assert state_before == state_after


def test_rule_hash_and_summary_match_the_selected_authority():
    assert GEN.RULE_HASH == "12c615886fb4"
    assert "center" in GEN.SUMMARY.lower()
    assert "preserv" in GEN.SUMMARY.lower() or "containing" in GEN.SUMMARY.lower()
    assert "diagonal" in GEN.SUMMARY.lower()
