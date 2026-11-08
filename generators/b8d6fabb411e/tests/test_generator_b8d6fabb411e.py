from __future__ import annotations

import importlib
import json
import random
from itertools import product
from pathlib import Path

import pytest

from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_hash


gen = importlib.import_module("puzzle_generators.per_puzzle.b8d6fabb411e.generator")
ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "b8d6fabb411e"
BASE_FILES = (
    ROOT / "data/base/solutions/training/d43fd935__b8d6fabb411e.json",
    ROOT / "data/base/solutions/augmented/d43fd935__43bde5b3b996.json",
)


def _canonical_rows() -> list[dict]:
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    return rows


def test_rule_pin_canonical_pairs_and_selected_sources_are_exact() -> None:
    assert gen.VERSION == "3.1.0"
    assert gen.RULE_HASH == "e88f12aefcff"
    assert canonical_rule_hash(TASK_ID) == gen.RULE_HASH

    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 8
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._expected_output(pair["input"]) == pair["output"]

    rows = _canonical_rows()
    assert len(rows) == 2
    selected = rows[0]["program_solution"]
    assert all(row["program_solution"] == selected for row in rows)
    for path in BASE_FILES:
        target = json.loads(path.read_text(encoding="utf-8"))["racket_target"]
        assert target["target_code"] == selected
        assert target["raw_code"] != selected


def test_every_exact_override_combination_is_observable_and_band_safe() -> None:
    case_index = 0
    for difficulty, layout, scene_profile in product(
        ("easy", "medium", "hard"),
        gen.AXES["layout"]["valid"],
        gen.AXES["scene_profile"]["valid"],
    ):
        requested = {"layout": layout, "scene_profile": scene_profile}
        for seed in (17, 29):
            grid = gen.generate(
                seed,
                1000 + case_index,
                difficulty=difficulty,
                **requested,
            )
            assert gen.self_check(grid, difficulty=difficulty) == []
            assert gen.observe_overrides(grid) == requested
            assert gen._expected_output(grid) != grid
            case_index += 1

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 2, bogus_axis="canonical_four")
    with pytest.raises(ValueError):
        gen.generate(1, 2, layout="not_a_layout")
    with pytest.raises(ValueError):
        gen.generate(1, 2, scene_profile="not_a_profile")


def test_every_four_demo_sliding_window_is_identifiable() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(16):
            grids = [
                gen.generate(90_000 + start, start + offset, difficulty=difficulty)
                for offset in range(5)
            ]
            demos = [
                {"input": grid, "output": gen._expected_output(grid)}
                for grid in grids[:4]
            ]
            query = {
                "input": grids[4],
                "output": gen._expected_output(grids[4]),
            }
            assert gen.lesson_identifiable(demos, query) == []
            assert {
                gen.observe_overrides(grid)["scene_profile"] for grid in grids[:4]
            } == set(gen.SCHEDULE_PROFILES)
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(grid) != gen._expected_output(grid)
                    for grid in grids[:4]
                ), (difficulty, start, name)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                assert any(witness(grid) for grid in grids[:4]), (
                    difficulty,
                    start,
                    name,
                )


def test_canonical_ambiguous_boundary_shortcut_gets_generated_killing_witness() -> None:
    shortcut = gen.CANONICAL_SHORTCUTS["boundary_rows_cols_only"]
    pairs = canonical_pairs(TASK_ID)
    assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs)

    for difficulty in ("easy", "medium", "hard"):
        killing = next(
            grid
            for index in range(16)
            if gen.SEMANTIC_WITNESSES["interior_span_alignment"](
                grid := gen.generate(700 + index, index, difficulty=difficulty)
            )
        )
        assert shortcut(killing) != gen._expected_output(killing)


def test_structural_mutation_impostors_are_rejected() -> None:
    valid = gen.generate(9, 6, difficulty="medium")
    impostors = gen.mutation_impostors(valid)
    assert len(impostors) >= 6
    for name, grid in impostors:
        assert gen.self_check(grid), name


def test_replay_is_fresh_deterministic_and_global_rng_pure() -> None:
    random.seed(20260817)
    state = random.getstate()
    first = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(123, 456, difficulty="hard")
    assert random.getstate() == state
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert first != second


def test_schedule_is_live_in_every_band_and_keeps_canonical_support() -> None:
    for difficulty in ("easy", "medium", "hard"):
        profiles = set()
        strict_hits = 0
        interior_hits = 0
        for sample_index in range(80):
            grid = gen.generate(1200 + sample_index, sample_index, difficulty=difficulty)
            profiles.add(gen.observe_overrides(grid)["scene_profile"])
            strict_hits += int(not gen.strict_canonical_like(grid))
            interior_hits += int(
                gen.SEMANTIC_WITNESSES["interior_span_alignment"](grid)
            )
        assert profiles == set(gen.SCHEDULE_PROFILES)
        assert strict_hits >= 32
        assert interior_hits >= 16


# Regressions from review-b459c1d5bf86ccc3.  These fail on version 3.0.0.
def test_every_default_lesson_teaches_interior_alignment_on_both_axes() -> None:
    for band in ("easy", "medium", "hard"):
        for start in range(16):
            axes = set()
            for index in range(start, start + gen.EXAMPLES_NEEDED):
                grid = gen.generate(100_000 + index, index, difficulty=band)
                for _r, _c, _color, direction in gen._analyze(grid)["interior_span"]:
                    axes.add("horizontal" if direction in {"left", "right"} else "vertical")
            assert axes == {"horizontal", "vertical"}, (band, start, axes)


def test_side_four_reaches_both_interior_offsets_in_every_direction() -> None:
    observed = set()
    for index in range(256):
        grid = gen.generate(100_000 + index, index, difficulty="hard")
        analysis = gen._analyze(grid)
        if analysis["square_side"] != 4:
            continue
        r1, c1, _r2, _c2 = analysis["square"]
        for r, c, _color, direction in analysis["interior_span"]:
            offset = r - r1 if direction in {"left", "right"} else c - c1
            observed.add((direction, offset))
    assert observed == set(product(("left", "right", "top", "bottom"), (1, 2)))


def test_four_side_color_pairing_is_not_pinned_to_direction() -> None:
    partitions = set()
    for index in range(128):
        grid = gen.generate(200_000 + index, index, scene_profile="canonical_four")
        groups = {}
        for _r, _c, color, direction in gen._analyze(grid)["aligned"]:
            groups.setdefault(color, []).append(direction)
        partitions.add(tuple(sorted(tuple(sorted(group)) for group in groups.values())))
    # All three unordered two-and-two color pairings of the four directions.
    assert len(partitions) == 3, partitions


def test_axis_specific_boundary_rivals_are_executable_and_killed_in_lessons() -> None:
    names = {"horizontal_boundary_only", "vertical_boundary_only"}
    assert names <= set(gen.SEMANTIC_RIVALS)
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(90_000 + index, index, difficulty=band) for index in range(4)]
        for name in names:
            rival = gen.SEMANTIC_RIVALS[name]
            assert any(rival(grid) != gen._expected_output(grid) for grid in grids), (band, name)


def _collinear_scene(far_color=2, near_color=1):
    grid = [[0] * 12 for _ in range(12)]
    for r in range(5, 8):
        for c in range(5, 8):
            grid[r][c] = 3
    grid[0][6], grid[3][6] = far_color, near_color
    return grid


def test_checker_rejects_ray_overlap_that_recolors_an_existing_marker() -> None:
    original = _collinear_scene()
    transforms = (original, original[::-1], [list(row) for row in zip(*original)],
                  [list(row) for row in zip(*original[::-1])])
    for grid in transforms:
        reasons = gen.self_check(grid)
        assert any("recolor" in reason or "conflict" in reason for reason in reasons), reasons


def test_checker_does_not_reject_safe_same_color_collinearity() -> None:
    grid = _collinear_scene(2, 2)
    assert gen.self_check(grid) == []
    output = gen._expected_output(grid)
    assert all(output[r][c] == color for r, row in enumerate(grid)
               for c, color in enumerate(row) if color != 0)


def test_unobservable_requested_axis_is_not_silently_accepted() -> None:
    grid = [[0] * 10 for _ in range(10)]
    for r in (4, 5):
        for c in (4, 5):
            grid[r][c] = 3
    grid[1][4] = 2
    # This is a valid rule input, but no generated profile has zero decoys.
    assert gen.self_check(grid) == []
    assert gen.self_check(grid, meta={"overrides": {"layout": "canonical_10"}}) == []
    assert gen.self_check(grid, meta={"overrides": {"scene_profile": "canonical_one"}})
    assert gen.self_check(grid, meta={"scene_profile": "canonical_one"})
    assert gen.self_check(grid, meta={"overrides": {"scene_profile": None}}) == []


@pytest.mark.parametrize("height,width", [(31, 10), (10, 31)])
def test_checker_rejects_grid_outside_arc_size_limits(height, width) -> None:
    grid = [[0] * width for _ in range(height)]
    for r in (4, 5):
        for c in (4, 5):
            grid[r][c] = 3
    grid[1][4] = 2
    assert gen.self_check(grid)
