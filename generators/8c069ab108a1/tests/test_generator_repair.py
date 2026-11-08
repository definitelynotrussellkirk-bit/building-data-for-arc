from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


TASK_ID = "8c069ab108a1"
ROOT = find_root(__file__)
SOURCE = Path(
    os.environ.get(
        "CURRICULUM_TEST_SOURCE",
        ROOT / f"generators/{TASK_ID}/generator.py",
    )
)
if not SOURCE.exists():
    SOURCE = ROOT / f"puzzle_generators/{TASK_ID}.py"
SPEC = importlib.util.spec_from_file_location("orbit_scaffold_generator", SOURCE)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _rule_oracle(grid: list[list[int]]) -> list[list[int]]:
    height = len(grid)
    width = len(grid[0])
    anchors = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    assert len(anchors) == 1
    anchor_row, anchor_col = anchors[0]
    output = [[0] * width for _ in range(height)]
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in (0, 9):
                continue
            delta_row, delta_col = row - anchor_row, col - anchor_col
            for _ in range(4):
                out_row = anchor_row + delta_row
                out_col = anchor_col + delta_col
                if 0 <= out_row < height and 0 <= out_col < width:
                    output[out_row][out_col] = value
                delta_row, delta_col = delta_col, -delta_row
    return output


def _observed(grid: list[list[int]]) -> dict[str, int]:
    colors = {value for row in grid for value in row if value not in (0, 9)}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_cells": sum(value not in (0, 9) for row in grid for value in row),
        "n_colors": len(colors),
    }


def _orbit_errors(grid: list[list[int]]) -> list[str]:
    height = len(grid)
    width = len(grid[0])
    anchors = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 9
    ]
    if len(anchors) != 1:
        return [f"expected one anchor, found {len(anchors)}"]
    anchor_row, anchor_col = anchors[0]
    owners: dict[tuple[tuple[int, int], ...], int] = {}
    errors: list[str] = []
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value in (0, 9):
                continue
            delta_row, delta_col = row - anchor_row, col - anchor_col
            orbit: list[tuple[int, int]] = []
            for _ in range(4):
                out_row = anchor_row + delta_row
                out_col = anchor_col + delta_col
                if not (0 <= out_row < height and 0 <= out_col < width):
                    errors.append(f"clipped orbit from {(row, col)}")
                    break
                orbit.append((out_row, out_col))
                delta_row, delta_col = delta_col, -delta_row
            else:
                key = tuple(sorted(orbit))
                if key in owners:
                    errors.append(
                        f"duplicate orbit for colors {owners[key]} and {value}: {key}"
                    )
                owners[key] = value
    return errors


def test_public_contract_is_pinned_and_truthful() -> None:
    assert getattr(GEN, "RULE_HASH", None) == "9bb2dc983950"
    assert set(GEN.AXES) == {"grid_h", "grid_w", "n_cells", "n_colors"}
    assert callable(getattr(GEN, "strict_canonical_like", None))
    assert callable(getattr(GEN, "observe_overrides", None))
    assert callable(getattr(GEN, "rule_mirror", None))
    assert callable(getattr(GEN, "lesson_identifiable", None))
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.LESSON_SCHEDULE_PERIOD == 4


def test_all_canonical_pairs_are_accepted_and_mirrored_exactly() -> None:
    mirror = getattr(GEN, "rule_mirror", None)
    strict = getattr(GEN, "strict_canonical_like", None)
    assert callable(mirror)
    assert callable(strict)
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert strict(pair["input"]) == []
        assert mirror(pair["input"]) == pair["output"]
        assert _rule_oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_curriculum_has_canonical_profiles_and_clear_complete_orbits(band: str) -> None:
    grids = [GEN.generate(1701, index, difficulty=band) for index in range(40)]
    failures = [
        (index, _orbit_errors(grid))
        for index, grid in enumerate(grids)
        if _orbit_errors(grid)
    ]
    assert failures == []
    assert any(
        len(grid) == 7
        and len(grid[0]) == 7
        and len({value for row in grid for value in row}) == 3
        for grid in grids
    )
    assert all(GEN.self_check(grid) == [] for grid in grids)
    assert all(_rule_oracle(grid) != grid for grid in grids)


def test_exact_override_contract_and_unknown_keys() -> None:
    observer = getattr(GEN, "observe_overrides", None)
    assert callable(observer)
    for band in ("easy", "medium", "hard"):
        for requested in (
            {"grid_h": 7, "grid_w": 7, "n_cells": 2, "n_colors": 1},
            {"grid_h": 14, "grid_w": 14, "n_cells": 6, "n_colors": 4},
            {"grid_h": 9, "grid_w": 12, "n_cells": 5, "n_colors": 3},
        ):
            grid = GEN.generate(991, 7, difficulty=band, **requested)
            assert observer(grid) == requested
            assert _observed(grid) == requested
    with pytest.raises(ValueError, match="unknown"):
        GEN.generate(0, 0, __unknown_axis=1)
    with pytest.raises(ValueError):
        GEN.generate(0, 0, n_cells=2, n_colors=4)


def test_declared_canonical_shortcuts_are_real_and_generated_counterexamples_exist() -> None:
    shortcuts = getattr(GEN, "CANONICAL_SHORTCUTS", None)
    witnesses = getattr(GEN, "SEMANTIC_WITNESSES", None)
    rivals = getattr(GEN, "SEMANTIC_RIVALS", None)
    assert isinstance(shortcuts, dict) and shortcuts
    assert isinstance(witnesses, dict) and witnesses
    assert isinstance(rivals, dict) and rivals

    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    for name in ("first_color_only", "monochrome_first_color"):
        assert name in shortcuts
        assert all(shortcuts[name](pair["input"]) == pair["output"] for pair in pairs)

    grids = [GEN.generate(72, index, difficulty="medium") for index in range(4)]
    official = [GEN.rule_mirror(grid) for grid in grids]
    for name in ("first_color_only", "monochrome_first_color"):
        assert any(shortcuts[name](grid) != answer for grid, answer in zip(grids, official))
    for name, predicate in witnesses.items():
        assert any(predicate(grid) for grid in grids), name


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_four_sample_window_survives_all_query_rotations(band: str) -> None:
    competitors = getattr(GEN, "LESSON_COMPETITORS", None)
    assert isinstance(competitors, dict) and competitors
    pairs = [
        {"input": grid, "output": GEN.rule_mirror(grid)}
        for index in range(28)
        for grid in [GEN.generate(811, index, difficulty=band)]
    ]
    failures: list[object] = []
    for start in range(25):
        window = pairs[start : start + 4]
        for query_index, query in enumerate(window):
            demos = [pair for index, pair in enumerate(window) if index != query_index]
            reasons = GEN.lesson_identifiable(demos, query)
            if reasons:
                failures.append((start, query_index, reasons))
            for name, rival in competitors.items():
                if all(rival(pair["input"]) == pair["output"] for pair in demos):
                    if rival(query["input"]) != query["output"]:
                        failures.append((start, query_index, name))
    assert failures == []

@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_partial_count_overrides_adapt_the_unspecified_dependent_axis(band: str) -> None:
    for sample_index in range(4):
        few_cells = GEN.generate(314, sample_index, difficulty=band, n_cells=2)
        observed = GEN.observe_overrides(few_cells)
        assert observed["n_cells"] == 2
        assert 1 <= observed["n_colors"] <= 2

        many_colors = GEN.generate(271, sample_index, difficulty=band, n_colors=4)
        observed = GEN.observe_overrides(many_colors)
        assert observed["n_colors"] == 4
        assert 4 <= observed["n_cells"] <= 6

def test_orbit_probe_classifies_clipping_collisions_and_clear_scaffolds() -> None:
    probe_path = ROOT / f"generators/{TASK_ID}/workspace/orbit_integrity_probe.py"
    probe_spec = importlib.util.spec_from_file_location("orbit_integrity_probe", probe_path)
    assert probe_spec is not None and probe_spec.loader is not None
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)

    clipped = [[0] * 7 for _ in range(7)]
    clipped[1][1] = 9
    clipped[6][6] = 2
    assert probe.analyze_grid(clipped)["clipped_orbits"] == 1

    collision = [[0] * 7 for _ in range(7)]
    collision[3][3] = 9
    collision[1][3] = 2
    collision[3][5] = 4
    result = probe.analyze_grid(collision)
    assert result["duplicate_orbits"] == 1
    assert result["cross_color_duplicate_orbits"] == 1

    clear = GEN.generate(19, 2, difficulty="hard")
    result = probe.analyze_grid(clear)
    assert result["clipped_orbits"] == 0
    assert result["duplicate_orbits"] == 0
    assert result["clear_complete_orbits"] is True

def test_retained_baseline_counterexample_exercises_clipping_and_cross_color_collision() -> None:
    import json

    fixture_path = (
        ROOT
        / f"generators/{TASK_ID}/counterexamples/review-34f601b1f83910ae-v0001/clipped_cross_color_orbit.json"
    )
    fixture = json.loads(fixture_path.read_text())
    probe_path = ROOT / f"generators/{TASK_ID}/workspace/orbit_integrity_probe.py"
    probe_spec = importlib.util.spec_from_file_location("orbit_integrity_probe_fixture", probe_path)
    assert probe_spec is not None and probe_spec.loader is not None
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)
    measurement = probe.analyze_grid(fixture["replay"]["grid"])
    assert measurement["clipped_orbits"] == 5
    assert measurement["cross_color_duplicate_orbits"] == 2
    assert measurement["clear_complete_orbits"] is False
