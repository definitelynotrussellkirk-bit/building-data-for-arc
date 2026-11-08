"""Independent regressions for the E82 sampler, portable across both layouts."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root


TASK = "249b59452da6"
ROOT = find_root(__file__)
HOME = next(path for path in (
    ROOT / "generators" / TASK,
    ROOT / "puzzle_generators" / "per_puzzle" / TASK,
) if (path / "generator.py").is_file())
SPEC = importlib.util.spec_from_file_location("reviewed_e82", HOME / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def eligible_windows(grid):
    """Identify windows via unordered neighboring red-cell pairs, not generator code."""
    red = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    result = set()
    for r, c in red:
        for dc in (-1, 1):
            other = (r + 1, c + dc)
            if other in red and grid[r][c + dc] == 0 and grid[r + 1][c] == 0:
                result.add((r, min(c, c + dc)))
    return result


def oracle(grid):
    result = copy.deepcopy(grid)
    for r, c in eligible_windows(grid):
        for rr in (r, r + 1):
            for cc in (c, c + 1):
                if grid[rr][cc] == 0:
                    result[rr][cc] = 3
    return result


@pytest.mark.parametrize("bad", [
    [], [[]], [[0], [0, 2]], [[11]], [[-1]], [[True]], [["2"]], [[None]],
    [[0] * 8 for _ in range(8)], [[2] * 8 for _ in range(8)],
])
def test_validator_rejects_malformed_or_uninformative_inputs(bad):
    assert GEN.self_check(bad), f"accepted invalid/no-active-pair grid: {bad!r}"


@pytest.mark.parametrize("overrides", [
    {"grid_h": 4}, {"grid_w": 18}, {"n_pairs": 1}, {"n_pairs": 10},
    {"palette_size": 2}, {"palette_size": 3}, {"palette_size": 4}, {"palette_size": 5},
])
def test_single_exact_controls_are_honored(overrides):
    for band in ("easy", "medium", "hard"):
        grid = GEN.generate(0, 0, difficulty=band, **overrides)
        actual = {
            "grid_h": len(grid), "grid_w": len(grid[0]),
            "n_pairs": len(eligible_windows(grid)),
            "palette_size": len({v for row in grid for v in row}),
        }
        assert not GEN.self_check(grid, difficulty=band)
        assert all(actual[k] == v for k, v in overrides.items()), (band, overrides, actual)


def test_infeasible_joint_control_never_silently_underfills():
    requested = {"grid_h": 7, "grid_w": 7, "n_pairs": 5}
    try:
        grid = GEN.generate(0, 0, **requested)
    except ValueError as exc:
        assert set(getattr(exc, "incompatible_axes", ())) >= {"grid_h", "grid_w", "n_pairs"}
    else:
        assert (len(grid), len(grid[0])) == (7, 7)
        assert len(eligible_windows(grid)) == 5


@pytest.mark.parametrize("overrides", [
    {"misspelled_axis": 1}, {"grid_h": True}, {"grid_w": 10.0},
    {"n_pairs": "3"}, {"n_pairs": 0}, {"palette_size": 11},
])
def test_invalid_overrides_fail_loudly(overrides):
    with pytest.raises((ValueError, TypeError)):
        GEN.generate(0, 0, **overrides)


def test_canonical_inputs_are_accepted_and_independent_oracle_matches():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert pairs
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_inputs_retain_canonical_distractors_and_are_deterministic(band):
    for seed in range(8):
        grid = GEN.generate(seed, seed * 17 + 3, difficulty=band)
        assert grid == GEN.generate(seed, seed * 17 + 3, difficulty=band)
        assert GEN.self_check(grid, difficulty=band) == []
        assert any(v not in (0, 2) for row in grid for v in row), "canonical distractors absent"
        assert oracle(grid) != grid


def test_authority_pin_matches_actual_canonical_program():
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    programs = {row["program_solution"] for row in rows if row.get("task_id") == TASK}
    assert len(programs) == 1
    expected = hashlib.sha256(" ".join(next(iter(programs)).split()).encode()).hexdigest()[:12]
    assert getattr(GEN, "RULE_HASH", None) == expected


def test_declared_canonical_shortcuts_really_fit_all_canonical_pairs():
    shortcuts = getattr(GEN, "CANONICAL_SHORTCUTS", {})
    assert shortcuts, "canonical-fitting shortcut contract is missing"
    for name, rival in shortcuts.items():
        for pair in canonical_pairs(TASK, root=ROOT):
            original = copy.deepcopy(pair["input"])
            assert rival(pair["input"]) == pair["output"], name
            assert pair["input"] == original, f"{name} mutates its input"


def test_default_demonstrations_refute_declared_shortcuts_in_every_rotation():
    rivals = {}
    for namespace in ("SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        rivals.update({f"{namespace}.{name}": fn for name, fn in getattr(GEN, namespace, {}).items()})
    assert rivals, "no executable rivals"
    n_train = getattr(GEN, "EXAMPLES_NEEDED", 3)
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 17):
            for start in range(8):
                grids = [GEN.generate(seed, start + j, difficulty=band) for j in range(n_train + 1)]
                labels = [oracle(g) for g in grids]
                for name, rival in rivals.items():
                    predictions = [rival(copy.deepcopy(g)) for g in grids]
                    for query_index in range(len(grids)):
                        fits_demos = all(predictions[j] == labels[j] for j in range(len(grids)) if j != query_index)
                        assert not (fits_demos and predictions[query_index] != labels[query_index]), (
                            band, seed, start, query_index, name,
                        )
