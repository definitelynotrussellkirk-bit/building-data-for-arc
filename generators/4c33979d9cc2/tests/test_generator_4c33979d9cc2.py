from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "4c33979d9cc2"
HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[1]


def _bootstrap_runtime() -> None:
    for parent in HERE.parents:
        candidates = (parent, parent / "shared" / "runtime")
        for candidate in candidates:
            if (candidate / "puzzle_generators").is_dir():
                sys.path.insert(0, str(candidate))
                return
    raise RuntimeError("could not locate puzzle_generators runtime")


_bootstrap_runtime()
spec = importlib.util.spec_from_file_location(
    f"review_{TASK_ID}_generator", TASK_DIR / "generator.py"
)
assert spec and spec.loader
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)


def _canonical_path() -> Path:
    for parent in HERE.parents:
        for relative in (
            Path("shared/data/canonical/puzzles.jsonl"),
            Path("data/canonical/puzzles.jsonl"),
        ):
            candidate = parent / relative
            if candidate.is_file():
                return candidate
    raise RuntimeError("canonical puzzles.jsonl not found")


def _canonical_row() -> dict:
    with _canonical_path().open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _grid_with_components(
    h: int,
    w: int,
    components: list[list[tuple[int, int]]],
) -> list[list[int]]:
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for component in components:
        for row, col in component:
            grid[row][col] = 7
    return grid


def test_metadata_pins_rule_and_exposes_only_observable_axes():
    assert GEN.RULE_HASH == "4a8c0ad5c512"
    assert GEN.VERSION == "3.0.0"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_components"}
    assert GEN.EXAMPLES_NEEDED == 5
    assert GEN.MIN_STRICT_FRAC == 1.0


def test_all_canonical_inputs_are_accepted_and_rule_mirror_is_exact():
    row = _canonical_row()
    found = 0
    for split in ("train", "test"):
        pairs = row[split] if isinstance(row[split], list) else [row[split]]
        for pair in pairs:
            found += 1
            assert GEN.self_check(pair["input"]) == []
            assert GEN.strict_canonical_like(pair["input"]) == []
            assert GEN.rule_mirror(pair["input"]) == pair["output"]
    assert found == 3


def test_self_check_requires_a_unique_largest_but_allows_smaller_ties():
    smaller_tie = _grid_with_components(
        9,
        10,
        [
            [(1, 1), (1, 2)],
            [(4, 1), (5, 1)],
            [(3, 7), (4, 7), (4, 8), (5, 8)],
        ],
    )
    assert GEN.self_check(smaller_tie) == []

    tied_largest = _grid_with_components(
        9,
        10,
        [
            [(1, 1), (1, 2), (2, 1)],
            [(5, 7), (5, 8), (6, 8)],
        ],
    )
    assert any("unique largest" in problem for problem in GEN.self_check(tied_largest))


def test_self_check_rejects_palette_shape_and_component_count_impostors():
    valid = GEN.generate(101, 0, difficulty="medium")

    wrong_color = copy.deepcopy(valid)
    row, col = next(
        (r, c)
        for r, values in enumerate(wrong_color)
        for c, value in enumerate(values)
        if value == 7
    )
    wrong_color[row][col] = 2
    assert any("palette" in problem for problem in GEN.self_check(wrong_color))

    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    assert GEN.self_check(ragged) == ["grid must be rectangular"]

    single = [[0] * 9 for _ in range(7)]
    for row, col in ((2, 2), (2, 3), (3, 2), (3, 3)):
        single[row][col] = 7
    assert any("2..5" in problem for problem in GEN.self_check(single))


def test_full_override_boundaries_are_honored_in_every_band():
    cases = (
        {"grid_h": 6, "grid_w": 7, "n_components": 2},
        {"grid_h": 12, "grid_w": 14, "n_components": 5},
        {"grid_h": 6, "grid_w": 14, "n_components": 5},
        {"grid_h": 12, "grid_w": 7, "n_components": 2},
    )
    for difficulty in ("easy", "medium", "hard"):
        for sample_index, overrides in enumerate(cases):
            grid = GEN.generate(
                93811,
                sample_index,
                difficulty=difficulty,
                **overrides,
            )
            assert GEN.observe_overrides(grid) == overrides
            assert GEN.self_check(grid) == []


def test_every_five_example_schedule_realizes_the_shortcut_witnesses():
    required = {
        "largest_first",
        "largest_last",
        "bbox_area_decoy",
        "nonlargest_size_tie",
        "diagonal_only_contact",
        "edge_largest",
        "interior_largest",
        "two_components",
    }
    for difficulty in ("easy", "medium", "hard"):
        grids = [GEN.generate(317, index, difficulty=difficulty) for index in range(5)]
        for witness_name in required:
            assert any(
                GEN.SEMANTIC_WITNESSES[witness_name](grid) for grid in grids
            ), (difficulty, witness_name)
        assert {
            GEN.schedule_profile(317, index, difficulty=difficulty)
            for index in range(5)
        } == set(GEN.SCHEDULE_PROFILES)


def test_declared_rival_witnesses_really_disagree_with_the_rule():
    for sample_index in range(5):
        grid = GEN.generate(991, sample_index, difficulty="medium")
        expected = GEN.rule_mirror(grid)
        for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
            if not GEN.SEMANTIC_WITNESSES[witness_name](grid):
                continue
            for rival_name in rival_names:
                assert GEN.SEMANTIC_RIVALS[rival_name](grid) != expected, (
                    sample_index,
                    witness_name,
                    rival_name,
                )


def test_five_consecutive_demos_identify_each_scheduled_query():
    for start in range(5):
        pairs = []
        for offset in range(6):
            grid = GEN.generate(77, start + offset, difficulty="medium")
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        assert GEN.lesson_identifiable(pairs[:5], pairs[5]) == []


def test_determinism_fresh_returns_global_rng_and_unknown_axes():
    random.seed(20260929)
    state = random.getstate()
    first = GEN.generate(73, 109, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(73, 109, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(73, 109, difficulty="hard") == second

    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GEN.generate(1, 2, unknown_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 2, difficulty="nightmare")


def test_every_difficulty_window_contains_an_exact_canonical_size_profile():
    canonical_sizes = {(6, 7), (7, 8), (9, 9)}
    for difficulty in ("easy", "medium", "hard"):
        sizes = {
            (len(grid), len(grid[0]))
            for grid in (
                GEN.generate(317, index, difficulty=difficulty)
                for index in range(GEN.EXAMPLES_NEEDED)
            )
        }
        assert sizes & canonical_sizes, (difficulty, sorted(sizes))
