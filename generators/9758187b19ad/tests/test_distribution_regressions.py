"""Adversarial distribution regressions added during the 2026-10-02 review.

This file deliberately lives under ``tests/`` because that is the assignment's
patchable test location.  It can run from the repository source layout or from
the exported ``puzzle_generators`` runtime layout.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path


TASK_ID = "9758187b19ad"
HERE = Path(__file__).resolve()
TASK_HOME = HERE.parent.parent


def _prepare_import_path() -> None:
    """Expose puzzle_generators dependencies in source or exported layouts."""
    for parent in HERE.parents:
        source_runtime = parent / "shared" / "runtime"
        if (source_runtime / "puzzle_generators").is_dir():
            sys.path.insert(0, str(source_runtime))
            return
        if (parent / "puzzle_generators").is_dir():
            sys.path.insert(0, str(parent))
            return
    raise RuntimeError("could not locate puzzle_generators runtime")


def _load_generator():
    _prepare_import_path()
    path = TASK_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"review_generator_{TASK_ID}", path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _load_generator()


def _canonical_path() -> Path:
    for parent in HERE.parents:
        candidates = (
            parent / "shared" / "data" / "canonical" / "puzzles.jsonl",
            parent / "data" / "canonical" / "puzzles.jsonl",
        )
        for path in candidates:
            if path.is_file():
                return path
    raise RuntimeError("could not locate canonical puzzles.jsonl")


def _canonical_pairs():
    for line in _canonical_path().read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") != TASK_ID:
            continue
        yield from row["train"]
        test = row["test"] if isinstance(row["test"], list) else [row["test"]]
        yield from test


def test_every_semantic_witness_is_rival_backed_or_a_declared_branch():
    rival_backed = set(GEN.WITNESS_RIVALS)
    branches = set(GEN.BRANCH_WITNESSES)
    assert not rival_backed & branches
    assert set(GEN.SEMANTIC_WITNESSES) == rival_backed | branches


def test_default_curriculum_crosses_profile_side_and_marker_multiplicity():
    expected = {
        (profile, side, count)
        for profile in GEN.SCHEDULE_PROFILES
        for side in ("left", "middle", "right")
        for count in (4, 5, 6)
    }
    for difficulty in ("easy", "medium", "hard"):
        observed = {
            (
                GEN.schedule_profile(0, index, difficulty),
                GEN._source_side_for(index, difficulty),
                GEN._marker_count_for(index, difficulty),
            )
            for index in range(210)
        }
        assert observed == expected


def test_canonical_shortcuts_are_refuted_by_every_three_demo_window():
    pairs = list(_canonical_pairs())
    assert pairs
    assert all(
        GEN._solve_candidate(pair["input"], first_marker_per_code=True)
        == pair["output"]
        for pair in pairs
    )
    assert all(
        GEN._solve_candidate(pair["input"], template_left_strip_only=True)
        == pair["output"]
        for pair in pairs
    )

    period = math.lcm(
        len(GEN.SCHEDULE_PROFILES),
        len(GEN._SOURCE_SIDE_SCHEDULE),
        len(GEN._MARKER_COUNT_SCHEDULE),
    )
    for difficulty in ("easy", "medium", "hard"):
        for start in range(period):
            demos = [
                GEN.generate(707, start + offset, difficulty=difficulty)
                for offset in range(GEN.EXAMPLES_NEEDED)
            ]
            assert any(
                GEN._solve_candidate(grid)
                != GEN._solve_candidate(grid, first_marker_per_code=True)
                for grid in demos
            )
            assert any(
                GEN._solve_candidate(grid)
                != GEN._solve_candidate(grid, template_left_strip_only=True)
                for grid in demos
            )


def test_profile_constrained_morphology_is_not_a_six_mask_lookup_table():
    shapes = set()
    for seed in range(80):
        grid = GEN.generate(seed, 5, difficulty="easy")
        _, _, cells = GEN._template_shape(grid)
        shapes.add(tuple(sorted(cells)))
    assert len(shapes) >= 20


def test_general_rectangle_packer_stays_valid_across_layout_modes():
    source_sides = set()
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(18):
            grid = GEN.generate(911, sample_index, difficulty=difficulty)
            assert GEN.self_check(grid) == []
            source_sides.add(GEN._source_side_observation(grid))
    assert {"left", "middle", "right"} <= source_sides
