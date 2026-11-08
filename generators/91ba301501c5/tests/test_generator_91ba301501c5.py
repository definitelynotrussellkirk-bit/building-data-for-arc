from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

SPEC = importlib.util.spec_from_file_location(
    "generator_91ba301501c5",
    REPO / "generators" / "91ba301501c5" / "generator.py",
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_inputs():
    result = []
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                result.extend(example["input"] for example in row.get("train", []))
                result.extend(example["input"] for example in row.get("test", []))
    return result


def _line_row(grid):
    return next(r for r, row in enumerate(grid) if all(value == 5 for value in row))


def test_self_check_accepts_every_canonical_input():
    inputs = _canonical_inputs()
    assert inputs
    for grid in inputs:
        assert GEN.self_check(grid) == []


def test_unknown_override_is_rejected_instead_of_silently_ignored():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, difficulty="easy", typo_axis=1)


def test_default_curriculum_exercises_every_color_side_branch():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = GEN.generate(17, sample_index, difficulty=difficulty)
            line = _line_row(grid)
            present = {
                (value, "above" if r < line else "below")
                for r, row in enumerate(grid)
                for value in row
                if value in (1, 2)
            }
            assert present == {
                (1, "above"), (1, "below"),
                (2, "above"), (2, "below"),
            }


def test_pinned_profile_floor_keeps_at_least_one_quarter_canonical():
    hits = 0
    total = 0
    for difficulty in ("easy", "medium", "hard"):
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{GEN.TASK_ID}:{difficulty}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=difficulty)
            total += 1
            hits += (len(grid), len(grid[0]), len({c for row in grid for c in row})) == (10, 10, 4)
    assert hits / total >= 0.25


def test_canonical_profile_and_semantic_contract_are_reachable():
    assert GEN.RULE_HASH == "c850a30c9e63"
    assert GEN.SEMANTIC_WITNESSES
    assert GEN.SEMANTIC_RIVALS
    assert GEN.WITNESS_RIVALS
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(23, i, difficulty=difficulty) for i in range(30)]
        assert any(len(g) == 10 and len(g[0]) == 10 for g in grids)
        for witness in GEN.SEMANTIC_WITNESSES.values():
            assert any(witness(g) for g in grids)

def test_all_canonical_divider_rows_are_exact_override_profiles():
    expected_rows = {"upper": 3, "mid": 4, "center": 5}
    for line_position, expected_row in expected_rows.items():
        grid = GEN.generate(
            101,
            0,
            difficulty="medium",
            grid_profile="canonical",
            line_position=line_position,
            n_blue=3,
            n_red=2,
            edge_blue=False,
        )
        assert _line_row(grid) == expected_row
        assert GEN.observe_overrides(grid)["line_position"] == line_position


def test_lesson_identifiable_names_a_rival_that_fits_demos_but_changes_query():
    demo_input = [
        [2, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
        [5, 5, 5, 5, 5],
        [0, 0, 0, 0, 0],
        [0, 2, 0, 0, 0],
    ]
    query_input = [
        [0, 0, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [5, 5, 5, 5, 5],
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0],
    ]
    demo = {
        "input": demo_input,
        "output": GEN._apply_variant(demo_input, blue_mode="away", red_mode="toward"),
    }
    query = {
        "input": query_input,
        "output": GEN._apply_variant(query_input, blue_mode="away", red_mode="toward"),
    }
    reasons = GEN.lesson_identifiable([demo], query)
    assert any("blue_toward" in reason for reason in reasons)


def test_two_generated_demos_identify_the_query_against_declared_rivals():
    grids = [GEN.generate(303, index, difficulty="hard") for index in range(3)]
    pairs = [
        {
            "input": grid,
            "output": GEN._apply_variant(grid, blue_mode="away", red_mode="toward"),
        }
        for grid in grids
    ]
    assert GEN.EXAMPLES_NEEDED == 2
    assert GEN.lesson_identifiable(pairs[:2], pairs[2]) == []

