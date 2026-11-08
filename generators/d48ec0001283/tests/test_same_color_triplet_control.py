"""Regression tests for the all-same-row shortcut found in review."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import sys

import pytest

TASK_ID = "d48ec0001283"
TASK_HOME = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_HOME / "generator.py"))
SPEC = spec_from_file_location(f"review_{TASK_ID}_triplet", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


COUNTEREXAMPLE_PATH = TASK_HOME / "counterexamples" / "same_color_triplet_shortcut.json"


def same_color_triplet_counterexample() -> dict[str, object]:
    return json.loads(COUNTEREXAMPLE_PATH.read_text())


def same_color_triplet_witness() -> list[list[int]]:
    return same_color_triplet_counterexample()["input"]


def test_same_color_triplet_is_lawful_and_refutes_declared_rival() -> None:
    grid = same_color_triplet_witness()
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid)["distractor_mode"] == "same_color_triplet"

    counterexample = same_color_triplet_counterexample()
    intended = GEN.rule_mirror(grid)
    rival = GEN.SEMANTIC_RIVALS["fill_same_color_extrema"]
    assert intended == counterexample["intended_output"]
    assert rival(grid) == counterexample["rival_output"]
    assert rival(grid) != intended
    assert intended[1] == grid[1]
    assert rival(grid)[1] == [0, 2, 2, 2, 2, 2, 0, 0]
    assert GEN.SEMANTIC_WITNESSES["same_color_triplet_distractor"](grid)
    assert "fill_same_color_extrema" in GEN.WITNESS_RIVALS["same_color_triplet_distractor"]


def test_same_color_triplet_override_round_trips_in_every_band() -> None:
    requested = {
        "grid_h": 6,
        "grid_w": 8,
        "span_count": 2,
        "gap_profile": "mixed",
        "edge_profile": "both",
        "color_mode": "distinct",
        "distractor_mode": "same_color_triplet",
    }
    for band in (None, "easy", "medium", "hard"):
        grid = GEN.generate(731, 9, difficulty=band, **requested)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == requested
        intended = GEN.rule_mirror(grid)
        assert GEN.SEMANTIC_RIVALS["fill_same_color_extrema"](grid) != intended


def _pair(seed: int, index: int, band: str) -> dict[str, list[list[int]]]:
    grid = GEN.generate(seed, index, difficulty=band)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _object_count(grid: list[list[int]]) -> int:
    seen: set[tuple[int, int]] = set()
    count = 0
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for column in range(width):
            color = grid[row][column]
            if color == 0 or (row, column) in seen:
                continue
            count += 1
            stack = [(row, column)]
            seen.add((row, column))
            while stack:
                current_row, current_column = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (current_row + dr, current_column + dc)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
    return count


def test_default_schedule_puts_all_three_controls_in_every_demo_window() -> None:
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    for band in ("easy", "medium", "hard"):
        modes = [
            GEN.observe_overrides(GEN.generate(8801, index, difficulty=band))["distractor_mode"]
            for index in range(8)
        ]
        assert modes[:4] == ["none", "all_controls", "all_controls", "none"]
        for start in range(4):
            assert "all_controls" in modes[start : start + GEN.EXAMPLES_NEEDED]
            demos = [_pair(8801, index, band) for index in range(start, start + 3)]
            query = _pair(8801, start + 3, band)
            assert GEN.lesson_identifiable(demos, query) == []

        for index in (1, 2, 5, 6):
            grid = GEN.generate(8801, index, difficulty=band)
            assert GEN.SEMANTIC_WITNESSES["same_color_triplet_distractor"](grid)
            intended = GEN.rule_mirror(grid)
            assert GEN.SEMANTIC_RIVALS["fill_same_color_extrema"](grid) != intended
            assert GEN.SEMANTIC_RIVALS["canonical_rows_only"](grid) != intended


def test_default_control_scenes_stay_within_canonical_object_count_scale() -> None:
    for band in ("easy", "medium", "hard"):
        for index in (1, 2, 5, 6):
            grid = GEN.generate(8801, index, difficulty=band)
            assert GEN.observe_overrides(grid)["span_count"] == 2
            assert _object_count(grid) <= 12


def test_partial_overrides_choose_compatible_unspecified_axes() -> None:
    assert {
        "grid_h": 5,
        "span_count": 3,
        "distractor_mode": "all_controls",
    } in GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS

    for band in ("easy", "medium", "hard"):
        for seed in range(30):
            short = GEN.generate(seed, 3, difficulty=band, grid_h=5)
            short_axes = GEN.observe_overrides(short)
            assert short_axes["grid_h"] == 5
            assert short_axes["span_count"] + {
                "none": 0,
                "mixed_endpoints": 1,
                "blocked_span": 1,
                "same_color_triplet": 1,
                "both_controls": 2,
                "all_controls": 3,
            }[short_axes["distractor_mode"]] <= 5

            triplet_scene = GEN.generate(
                seed,
                3,
                difficulty=band,
                grid_h=5,
                distractor_mode="all_controls",
            )
            assert GEN.observe_overrides(triplet_scene)["span_count"] == 2

            expanded = GEN.generate(
                seed,
                3,
                difficulty=band,
                span_count=3,
                distractor_mode="all_controls",
            )
            assert GEN.observe_overrides(expanded)["grid_h"] >= 6

    with pytest.raises(ValueError, match="grid_h.*span_count.*distractor_mode"):
        GEN.generate(
            0,
            3,
            difficulty="easy",
            grid_h=5,
            span_count=3,
            distractor_mode="all_controls",
        )


@pytest.mark.parametrize("bad_index", [True, False, 1.0, "1", -1])
def test_sample_index_rejects_non_integer_and_negative_scalars(bad_index: object) -> None:
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(17, bad_index, difficulty="medium")


def test_all_controls_scene_refutes_canonical_rows_only_for_recorded_census_seed() -> None:
    """Regression for easy lesson 58 from the 100-per-band census."""
    grid = GEN.generate(1755643977, 58, difficulty="easy")
    assert GEN.observe_overrides(grid)["distractor_mode"] == "all_controls"
    intended = GEN.rule_mirror(grid)
    assert GEN.SEMANTIC_RIVALS["canonical_rows_only"](grid) != intended
