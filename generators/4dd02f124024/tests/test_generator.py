"""Task-local regression tests for the frame/interior keep-or-erase generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = HOME.parents[1]
RUNTIME = REPO_ROOT / "shared" / "runtime"
if RUNTIME.exists():
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root

GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("task_4dd02f124024_generator", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _pairs():
    return canonical_pairs("4dd02f124024", root=find_root(__file__))


def _profile(grid):
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_palette_kind_override_changes_pixels_and_is_observable():
    warm = GEN.generate(0, 0, difficulty="medium", palette_kind="warm")
    cool = GEN.generate(0, 0, difficulty="medium", palette_kind="cool")
    assert warm != cool
    assert GEN.self_check(warm) == []
    assert GEN.self_check(cool) == []
    assert GEN.observe_overrides(warm)["palette_kind"] == "warm"
    assert GEN.observe_overrides(cool)["palette_kind"] == "cool"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("grid_h,grid_w", [(9, 14), (10, 16), (17, 20)])
@pytest.mark.parametrize("n_frames", [2, 3, 4])
@pytest.mark.parametrize("palette_kind", ["default", "warm", "cool", "varied"])
@pytest.mark.parametrize("interior_style", ["foreign_only", "sparse_mixed", "dense_mixed"])
def test_every_advertised_override_round_trips(
    band, grid_h, grid_w, n_frames, palette_kind, interior_style
):
    requested = {
        "grid_h": grid_h,
        "grid_w": grid_w,
        "n_frames": n_frames,
        "palette_kind": palette_kind,
        "interior_style": interior_style,
    }
    grid = GEN.generate(17, 9, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"grid_h": True},
        {"grid_w": 14.0},
        {"n_frames": "2"},
        {"palette_kind": 3},
        {"interior_style": "unknown"},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **kwargs)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_invalid_sample_indexes_are_rejected(sample_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, sample_index)


def test_canonical_inputs_are_owned_and_python_oracle_matches_labels():
    pairs = _pairs()
    assert len(pairs) == 4
    for pair in pairs:
        grid = deepcopy(pair["input"])
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.solve_reference_shape(grid) == pair["output"]
        assert grid == pair["input"]


def test_declared_canonical_shortcuts_really_fit_every_canonical_pair():
    pairs = _pairs()
    assert {"erase_only_foreign", "first_mismatch_only"} <= set(GEN.CANONICAL_SHORTCUTS)
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


def test_five_phase_default_schedule_is_rotation_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(len(GEN.SCHEDULE_PROFILES)):
            indices = range(start, start + len(GEN.SCHEDULE_PROFILES))
            grids = [GEN.generate(901, index, difficulty=band) for index in indices]
            expected = list(GEN.SCHEDULE_PROFILES[start:]) + list(GEN.SCHEDULE_PROFILES[:start])
            assert [GEN.schedule_profile(901, index, band) for index in indices] == expected
            assert sum(
                _profile(grid) in {(9, 14, 4), (9, 16, 5), (10, 15, 5), (10, 16, 5)}
                for grid in grids
            ) >= 3
            labeled = [
                {"input": grid, "output": GEN.solve_reference_shape(grid)} for grid in grids
            ]
            for query_index, query in enumerate(labeled):
                demos = [pair for index, pair in enumerate(labeled) if index != query_index]
                assert GEN.lesson_identifiable(demos, query) == []


def test_sparse_mixed_witness_erases_own_color_cells_with_foreign_trigger():
    grid = GEN.generate(
        13,
        1,
        grid_h=10,
        grid_w=15,
        n_frames=3,
        palette_kind="default",
        interior_style="sparse_mixed",
    )
    frames = GEN.find_frames(grid)
    mismatches = [frame for frame in frames if GEN.frame_kind(grid, frame) == "mismatch"]
    assert mismatches
    for frame in mismatches:
        color, r0, c0, r1, c1 = frame
        values = [grid[row][col] for row in range(r0 + 1, r1) for col in range(c0 + 1, c1)]
        assert color in values
        assert any(value not in (0, color) for value in values)
    expected = GEN.solve_reference_shape(grid)
    rival = GEN.CANONICAL_SHORTCUTS["erase_only_foreign"](grid)
    assert expected != rival


def test_multiple_mismatch_witness_refutes_first_only_shortcut():
    grid = GEN.generate(27, 1, n_frames=3, interior_style="sparse_mixed")
    assert sum(GEN.frame_kind(grid, frame) == "mismatch" for frame in GEN.find_frames(grid)) >= 2
    assert GEN.solve_reference_shape(grid) != GEN.CANONICAL_SHORTCUTS["first_mismatch_only"](grid)


def test_generation_is_deterministic_and_does_not_mutate_outputs():
    expected = GEN.generate(412, 111, difficulty="hard")
    snapshot = deepcopy(expected)
    for index in range(100):
        GEN.generate(index, index * 3, difficulty="easy")
    assert GEN.generate(412, 111, difficulty="hard") == expected
    assert expected == snapshot


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 14 for _ in range(9)]])
def test_malformed_grids_are_diagnostic(grid):
    assert GEN.self_check(grid)

@pytest.mark.parametrize("interior_style", ["sparse_mixed", "dense_mixed"])
def test_mixed_styles_never_create_nested_frame_shortcuts(interior_style):
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(40):
            grid = GEN.generate(
                seed,
                4,
                difficulty=difficulty,
                grid_h=17,
                grid_w=20,
                n_frames=4,
                interior_style=interior_style,
            )
            assert GEN.self_check(grid) == [], (difficulty, seed, interior_style)
            assert GEN.solve_reference_shape(grid) != GEN.CANONICAL_SHORTCUTS["erase_only_foreign"](grid), (
                difficulty,
                seed,
                interior_style,
            )
