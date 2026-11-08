"""Source-bound regressions for the vertical-domino teaching contract."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if runtime.is_dir():
        sys.path.insert(0, str(runtime))
        break

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "d59da25908ca"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("contract_generator_d59da25908ca", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

BANDS = (None, "easy", "medium", "hard")


def _canonical_rule_hash() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                normalized = " ".join(row["program_solution"].split())
                return hashlib.sha256(normalized.encode()).hexdigest()[:12]
    raise AssertionError(f"no canonical rule for {TASK_ID}")


def _vertical_runs(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    runs: list[tuple[int, int, int]] = []
    for col in range(len(grid[0])):
        row = 0
        while row < len(grid):
            if grid[row][col] != 3:
                row += 1
                continue
            start = row
            while row < len(grid) and grid[row][col] == 3:
                row += 1
            runs.append((col, start, row - start))
    return runs


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_canonical_authority_are_pinned():
    assert GEN.RULE_HASH == _canonical_rule_hash()
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_even_length_shortcut_fits_canonical_but_not_any_complete_lesson():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    rival = GEN.CANONICAL_SHORTCUTS["even_length_runs"]
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)
    for band in BANDS:
        for start in range(6):
            lesson = [_pair(GEN.generate(7103, index, difficulty=band))
                      for index in range(start, start + 4)]
            for query_index in range(4):
                query = lesson[query_index]
                demos = lesson[:query_index] + lesson[query_index + 1:]
                assert any(rival(pair["input"]) != pair["output"] for pair in demos)
                assert GEN.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("band", BANDS)
def test_default_draws_are_valid_reproducible_and_contain_positive_and_odd_controls(band):
    strict_hits = 0
    for index in range(20):
        grid = GEN.generate(9001 + index, index, difficulty=band)
        assert grid == GEN.generate(9001 + index, index, difficulty=band)
        assert GEN.self_check(grid) == []
        lengths = [length for _, _, length in _vertical_runs(grid)]
        assert lengths.count(2) in (1, 2)
        assert any(length in (1, 3, 5) for length in lengths)
        assert any(length != 2 for length in lengths)
        strict_hits += not GEN.strict_canonical_like(grid)
    assert strict_hits >= 10


def test_six_slot_schedule_breaks_length4_conditioning_in_every_four_pair_window():
    assert "requires_length4_context" in GEN.LESSON_COMPETITORS
    for start in range(12):
        seen_odd_controls: set[int] = set()
        length4_presence: list[bool] = []
        profiles: set[str] = set()
        for index in range(start, start + 4):
            grid = GEN.generate(431, index, difficulty="medium")
            lengths = [length for _, _, length in _vertical_runs(grid)]
            seen_odd_controls.update(length for length in lengths if length in (1, 3, 5))
            length4_presence.append(4 in lengths)
            profiles.add(GEN.schedule_profile(431, index, "medium"))
        assert seen_odd_controls == {1, 3, 5}
        assert length4_presence.count(True) == 2
        assert length4_presence.count(False) == 2
        assert len(profiles) == 4


@pytest.mark.parametrize("band", BANDS)
def test_all_exact_axis_boundary_combinations_are_constructive_and_observable(band):
    for height in (5, 10):
        for width in (7, 10):
            for n_targets in (1, 2):
                requested = {
                    "grid_h": height,
                    "grid_w": width,
                    "n_targets": n_targets,
                }
                grid = GEN.generate(1729, height * 100 + width * 10 + n_targets,
                                    difficulty=band, **requested)
                assert GEN.self_check(grid) == []
                assert GEN.observe_overrides(grid) == requested


def test_invalid_controls_fail_loudly_and_none_is_unset():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, bogus_axis=1)
    for options in (
        {"grid_h": 4}, {"grid_h": 11}, {"grid_w": 6}, {"grid_w": 11},
        {"n_targets": 0}, {"n_targets": 3}, {"grid_h": True},
        {"grid_w": 7.0}, {"n_targets": "2"},
    ):
        with pytest.raises(ValueError):
            GEN.generate(0, 0, **options)
    for difficulty in ("typo", "", True, 0.5):
        with pytest.raises(ValueError, match="difficulty"):
            GEN.generate(0, 0, difficulty=difficulty)
    for key in GEN.AXES:
        assert GEN.generate(23, 4, difficulty="hard", **{key: None}) == GEN.generate(
            23, 4, difficulty="hard"
        )


def test_self_check_rejects_minimal_impostors_and_missing_contrast():
    all_background = [[0] * 7 for _ in range(5)]
    only_target = [[0] * 7 for _ in range(5)]
    only_target[1][2] = only_target[2][2] = 3
    only_negative = [[0] * 7 for _ in range(5)]
    for row in range(4):
        only_negative[row][2] = 3
    solid_2x2 = [[0] * 7 for _ in range(5)]
    for row in (1, 2):
        for col in (2, 3):
            solid_2x2[row][col] = 3
    for name, grid in {
        "all_background": all_background,
        "only_target": only_target,
        "only_negative": only_negative,
        "solid_2x2": solid_2x2,
    }.items():
        assert GEN.self_check(grid), name


def test_every_four_pair_window_is_identifiable_under_every_query_rotation():
    for band in BANDS:
        for start in range(6):
            pairs = [_pair(GEN.generate(31337, index, difficulty=band))
                     for index in range(start, start + 4)]
            for query_index in range(4):
                query = pairs[query_index]
                demos = pairs[:query_index] + pairs[query_index + 1:]
                assert GEN.lesson_identifiable(demos, query) == []


def test_declared_witnesses_and_rivals_are_executable_and_source_bound():
    grids = [GEN.generate(991, index, difficulty="medium") for index in range(3)]
    assert set(GEN.SEMANTIC_WITNESSES) == {
        "length4_even_counterexample",
        "length4_absent_context",
        "singleton_control",
        "length3_control",
        "length5_control",
        "multiple_exact_targets",
    }
    for name, witness in GEN.SEMANTIC_WITNESSES.items():
        assert any(witness(grid) for grid in grids), name
    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(grid) != GEN.rule_mirror(grid) for grid in grids), name
