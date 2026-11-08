from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


TASK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "generator_9c50790b939c_under_test", TASK_DIR / "generator.py"
)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_row() -> dict:
    with (REPO_ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID:
                return row
    raise AssertionError("canonical task row not found")


def _canonical_pairs():
    row = _canonical_row()
    for split in ("train", "test"):
        pairs = row[split] if isinstance(row[split], list) else [row[split]]
        for pair in pairs:
            yield pair["input"], pair["output"]




def _object_count(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    count = 0
    for row in range(height):
        for column in range(width):
            if grid[row][column] == 7 or (row, column) in seen:
                continue
            count += 1
            color = grid[row][column]
            pending = [(row, column)]
            seen.add((row, column))
            while pending:
                rr, cc = pending.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        pending.append((nr, nc))
    return count


def test_contract_metadata_and_axes_are_truthful():
    assert GEN.RULE_HASH == "846ddca6645d"
    assert GEN.MIN_STRICT_FRAC == 1.0
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(GEN.AXES) == {
        "grid_h",
        "grid_w",
        "source_length",
        "block_position",
        "distractor_rails",
    }


def test_canonical_pairs_are_owned_and_match_the_python_rule_mirror():
    pairs = list(_canonical_pairs())
    assert len(pairs) == 4
    for grid, expected in pairs:
        before = [row[:] for row in grid]
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == expected
        assert grid == before


def test_exact_overrides_round_trip_and_unknown_controls_reject():
    overrides = {
        "grid_h": 16,
        "grid_w": 16,
        "source_length": 6,
        "block_position": "bottom",
        "distractor_rails": 10,
    }
    for band in ("easy", "medium", "hard"):
        grid = GEN.generate(109, 37, difficulty=band, **overrides)
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == overrides
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, not_an_axis=1)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, source_length="6")
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, block_position="middle")


def test_default_draws_are_canonical_rail_scenes_and_break_the_half_target_shortcut():
    witness_hits = {band: 0 for band in ("easy", "medium", "hard")}
    exact_16 = {band: 0 for band in witness_hits}
    object_counts = {band: [] for band in witness_hits}
    for band in witness_hits:
        for seed in range(80):
            grid = GEN.generate(seed, seed * 29 + 7, difficulty=band)
            assert GEN.self_check(grid) == []
            runs = GEN._vertical_runs(grid)
            # Canonical morphology is a field of vertical rails, never isolated noise.
            assert 10 <= len(runs) <= 15
            assert all(len(rows) >= 2 for _column, rows, _values in runs)
            assert {2, 4, 6, 8, 10} <= {len(rows) for _column, rows, _values in runs}
            object_counts[band].append(_object_count(grid))
            if len(grid) == 16 and len(grid[0]) == 16:
                exact_16[band] += 1
            if GEN.SEMANTIC_WITNESSES["half_target_shortcut_rebutted"](grid):
                witness_hits[band] += 1
                assert GEN.SEMANTIC_RIVALS["paint_half_target"](grid) != GEN.rule_mirror(grid)
    assert all(count >= 10 for count in witness_hits.values())
    assert all(count >= 10 for count in exact_16.values())
    assert all(max(counts) >= 14 for counts in object_counts.values())


def test_half_target_shortcut_fits_every_canonical_pair_but_has_generated_counterexamples():
    for grid, expected in _canonical_pairs():
        assert GEN.CANONICAL_SHORTCUTS["paint_half_target"](grid) == expected

    counterexample = GEN.generate(
        11,
        23,
        difficulty="medium",
        grid_h=12,
        grid_w=12,
        source_length=6,
        block_position="top",
        distractor_rails=8,
    )
    assert GEN.SEMANTIC_WITNESSES["half_target_shortcut_rebutted"](counterexample)
    assert GEN.rule_mirror(counterexample) != GEN.CANONICAL_SHORTCUTS["paint_half_target"](counterexample)


def test_selected_authority_text_is_exactly_the_canonical_rule():
    row = _canonical_row()
    authority_path = (
        REPO_ROOT
        / "shared/data/base/solutions/training/48634b99__9c50790b939c.json"
    )
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    assert authority["racket_target"]["target_code"] == row["program_solution"]
