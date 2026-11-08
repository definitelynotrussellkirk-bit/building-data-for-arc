"""Focused regression tests for generator d5d9fdb01bdd."""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import sys
from pathlib import Path

from reviewer_support import canonical_pairs, find_root

TASK_ID = "d5d9fdb01bdd"
try:
    GENERATOR = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )
except ModuleNotFoundError:
    generator_path = Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"task_generator_{TASK_ID}", generator_path
    )
    assert spec is not None and spec.loader is not None
    GENERATOR = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = GENERATOR
    spec.loader.exec_module(GENERATOR)
ROOT = find_root(__file__)


def _canonical_program() -> str:
    path = Path(ROOT) / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError(f"canonical task {TASK_ID} not found")


def test_rule_hash_canonical_acceptance_and_python_oracle():
    digest = hashlib.sha256(
        " ".join(_canonical_program().split()).encode("utf-8")
    ).hexdigest()[:12]
    assert GENERATOR.RULE_HASH == digest == "1b9c6046c883"

    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 4
    for pair in pairs:
        source = pair["input"]
        snapshot = [row[:] for row in source]
        assert GENERATOR.self_check(source) == []
        assert GENERATOR.rule_mirror(source) == pair["output"]
        assert source == snapshot


def test_boundary_overrides_are_exact_in_every_band_and_unknowns_fail():
    assert tuple(GENERATOR.AXES) == (
        "grid_h",
        "grid_w",
        "n_distinct_colors",
    )
    case = 0
    for band in ("easy", "medium", "hard"):
        for grid_h in (5, 11):
            for grid_w in (6, 12):
                for n_colors in (1, 3):
                    overrides = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "n_distinct_colors": n_colors,
                    }
                    grid = GENERATOR.generate(
                        20_000 + case,
                        case,
                        difficulty=band,
                        **overrides,
                    )
                    assert GENERATOR.self_check(grid) == []
                    assert GENERATOR.observe_overrides(grid) == overrides
                    case += 1

    import pytest

    with pytest.raises((TypeError, ValueError), match="unknown override"):
        GENERATOR.generate(1, 2, unknown_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GENERATOR.generate(1, 2, difficulty="nightmare")


def _lesson_pair(grid):
    return {"input": grid, "output": GENERATOR.rule_mirror(grid)}


def test_semantic_rivals_are_refuted_by_every_three_demo_window():
    expected_rivals = {
        "transpose_only_tall_or_square",
        "largest_component_only",
    }
    assert set(GENERATOR.SEMANTIC_RIVALS) == expected_rivals
    assert set(GENERATOR.LESSON_COMPETITORS) == expected_rivals
    assert set(GENERATOR.SEMANTIC_WITNESSES) == {
        "wide_crop_requires_transpose",
        "disconnected_content_uses_all_cells",
    }

    pairs = canonical_pairs(TASK_ID, root=ROOT)
    tall_shortcut = GENERATOR.SEMANTIC_RIVALS[
        "transpose_only_tall_or_square"
    ]
    assert all(tall_shortcut(pair["input"]) == pair["output"] for pair in pairs)
    assert all(GENERATOR.strict_canonical_like(pair["input"]) == [] for pair in pairs)

    canonical_profiles = {(5, 8, 2), (6, 6, 3), (6, 7, 3), (6, 8, 3)}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [
            GENERATOR.generate(
                100_000 + band_index * 10_000 + index,
                index,
                difficulty=band,
            )
            for index in range(60)
        ]
        assert all(GENERATOR.self_check(grid) == [] for grid in grids)
        profiles = {
            (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            for grid in grids
        }
        assert profiles & canonical_profiles
        assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) >= 55
        for name, witness in GENERATOR.SEMANTIC_WITNESSES.items():
            assert sum(bool(witness(grid)) for grid in grids) >= 15, name

    for start in range(18):
        grids = [
            GENERATOR.generate(700_000 + start, start + offset, difficulty="medium")
            for offset in range(4)
        ]
        demos = [_lesson_pair(grid) for grid in grids[:3]]
        query = _lesson_pair(grids[3])
        assert GENERATOR.lesson_identifiable(demos, query) == []
        for name, rival in GENERATOR.LESSON_COMPETITORS.items():
            assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_wide_generated_input_is_exact_counterexample_to_canonical_shortcut():
    grid = GENERATOR.generate(424_242, 2, difficulty="medium")
    analysis, errors = GENERATOR._analyze(grid)
    assert errors == []
    assert analysis["bbox_w"] > analysis["bbox_h"]
    intended = GENERATOR.rule_mirror(grid)
    rival = GENERATOR.SEMANTIC_RIVALS["transpose_only_tall_or_square"](grid)
    assert rival != intended
    assert (len(rival), len(rival[0])) == (
        analysis["bbox_h"],
        analysis["bbox_w"],
    )
    assert (len(intended), len(intended[0])) == (
        analysis["bbox_w"],
        analysis["bbox_h"],
    )


def test_every_four_example_lesson_is_identifiable_under_each_query_rotation():
    """A lesson must not depend on always hiding the fourth scheduled role."""
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(9):
            seed = 900_000 + band_index * 10_000 + start
            pairs = [
                _lesson_pair(GENERATOR.generate(seed, start + offset, difficulty=band))
                for offset in range(4)
            ]
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                query = pairs[query_index]
                assert GENERATOR.lesson_identifiable(demos, query) == [], (
                    band,
                    start,
                    query_index,
                )
