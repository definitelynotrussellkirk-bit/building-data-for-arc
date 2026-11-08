"""Focused regressions for the 11c53dabb028 input and exact-control contract.

These tests exercise observable legality and control semantics, without fixing a
particular seed's drawing, texture realization, or sampling frequency.  They run
from the source library and from the public task-tests stage's copied runtime.
"""
from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


TASK_ID = "11c53dabb028"


def _load_generator():
    try:
        from reviewer_support import find_root
    except ModuleNotFoundError as exc:
        if exc.name != "reviewer_support":
            raise
        # Bootstrap only the helper in this test's own source tree.  Runtime
        # execution already exposes reviewer_support and puzzle_generators.
        for ancestor in Path(__file__).resolve().parents:
            runtime = ancestor / "shared" / "runtime"
            if (runtime / "reviewer_support.py").is_file():
                sys.path.insert(0, str(runtime))
                break
        else:
            raise
        from reviewer_support import find_root

    root = find_root(__file__)
    module_name = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        # A library stores selected generators outside puzzle_generators.
        # Other import failures must remain visible instead of being hidden.
        if exc.name not in {
            "puzzle_generators.per_puzzle",
            f"puzzle_generators.per_puzzle.{TASK_ID}",
            module_name,
        }:
            raise
        source = root / "generators" / TASK_ID / "generator.py"
        spec = importlib.util.spec_from_file_location("review_contract_generator", source)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


GEN = _load_generator()

from reviewer_support import find_root


def _load_lawful_mutations():
    root = find_root(__file__)
    relative = Path("generators") / TASK_ID / "workspace" / "lawful_mutations.json"
    # The public task-tests copier mirrors this library path.  If a portable
    # snapshot relocates it, prefer the file recorded under the same identity.
    manifest = root / "RUNTIME_MANIFEST.json"
    candidates = []
    if manifest.is_file():
        for item in json.loads(manifest.read_text()).get("files", []):
            if item.get("library_path") == relative.as_posix():
                candidates.append(root / item["runtime_path"])
    candidates.extend([
        root / relative,
        root / "notes" / TASK_ID / "workspace" / relative.name,
        Path(GEN.__file__).resolve().parent / "workspace" / relative.name,
    ])
    for candidate in candidates:
        # Never fall back to the original checkout or another source tree.
        if candidate.resolve().is_relative_to(root) and candidate.is_file():
            fixture = json.loads(candidate.read_text())
            assert fixture["task_id"] == TASK_ID
            return fixture["cases"]
    raise FileNotFoundError(f"Missing {relative.name} in the selected task snapshot: {root}")


LAWFUL_MUTATIONS = _load_lawful_mutations()


def _flat(grid):
    return [cell for row in grid for cell in row]


def _assert_lawful(grid):
    assert isinstance(grid, list) and 1 <= len(grid) <= 15
    assert all(isinstance(row, list) for row in grid)
    assert 1 <= len(grid[0]) <= 15
    assert all(len(row) == len(grid[0]) for row in grid)
    cells = _flat(grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for cell in cells)
    assert 0 in cells and any(cell != 0 for cell in cells)
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize(
    "grid",
    [
        [[1, 0]],
        [[0], [9]],
        [[0] * 14 + [3]],
        [[8]] + [[0] for _ in range(14)],
        [[0] * 15 for _ in range(14)] + [[9] * 15],
        [[0, 2, 9], [4, 0, 2]],
    ],
    ids=["minimum-row", "minimum-column", "max-width", "max-height", "max-area", "multicolor"],
)
def test_self_check_accepts_legal_boundary_inputs(grid):
    assert GEN.self_check(grid) == []


@pytest.mark.parametrize("case", LAWFUL_MUTATIONS, ids=lambda case: case["name"])
def test_self_check_preserves_lawful_generic_mutation_shapes(case):
    # The companion authoring probe checks each fixture against real Racket.
    # This protects their acceptance from generic-linter-induced restrictions.
    _assert_lawful(case["input"])


@pytest.mark.parametrize(
    "grid",
    [
        None,
        [],
        [[]],
        [0, [1, 0]],
        [[1, 0], [0]],
        [[[1], 0]],
        [["1", 0]],
        [[1.0, 0]],
        [[True, 0]],
        [[10, 0]],
        [[-1, 0]],
        [[1, 0] for _ in range(16)],
        [[1] + [0] * 15],
        [[0, 0]],
        [[1, 2]],
        [[0]],
        [[1]],
    ],
    ids=[
        "none", "empty", "empty-row", "non-row", "ragged", "nested-cell",
        "string-cell", "float-cell", "bool-cell", "high-color", "negative-color",
        "height-16", "width-16", "all-zero", "all-nonzero", "singleton-zero", "singleton-color",
    ],
)
def test_self_check_rejects_malformed_or_out_of_domain_inputs_without_raising(grid):
    reasons = GEN.self_check(grid)
    assert isinstance(reasons, list) and reasons
    assert all(isinstance(reason, str) and reason for reason in reasons)


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_default_draws_are_lawful_and_replayable(difficulty):
    for seed in range(4):
        for index in range(3):
            grid = GEN.generate(seed, index, difficulty=difficulty)
            _assert_lawful(grid)
            assert GEN.generate(seed, index, difficulty=difficulty) == grid


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(1, 2), (2, 1), (1, 15), (15, 1), (8, 9), (15, 15)])
def test_exact_dimensions_cover_declared_domain_independent_of_difficulty(difficulty, height, width):
    grid = GEN.generate(
        19, 4, difficulty=difficulty, grid_h=height, grid_w=width,
        fg_color=7, fg_density=0.5, multi_color=False,
    )
    assert (len(grid), len(grid[0])) == (height, width)
    _assert_lawful(grid)


@pytest.mark.parametrize("density", [0.0, 0.05, 0.3, 0.5, 0.8, 1.0])
def test_exact_foreground_density_sets_final_occupancy(density):
    height, width = 4, 5
    expected = min(height * width - 1, max(1, round(density * height * width)))
    for index in range(12):
        grid = GEN.generate(
            23, index, grid_h=height, grid_w=width, texture="noise",
            fg_color=6, fg_density=density, multi_color=False,
        )
        _assert_lawful(grid)
        assert sum(cell != 0 for cell in _flat(grid)) == expected


@pytest.mark.parametrize("multi_color", [False, True])
@pytest.mark.parametrize("foreground", [1, 9])
def test_exact_foreground_is_first_nonzero_in_row_major_order(foreground, multi_color):
    for index in range(24):
        grid = GEN.generate(
            31, index, grid_h=4, grid_w=5, texture="noise",
            fg_color=foreground, fg_density=0.5, multi_color=multi_color,
        )
        _assert_lawful(grid)
        assert next(cell for cell in _flat(grid) if cell != 0) == foreground
        colors = set(_flat(grid)) - {0}
        assert (len(colors) >= 2) if multi_color else (colors == {foreground})


@pytest.mark.parametrize("height,width,density", [(2, 2, 0.0), (2, 2, 0.25), (1, 2, 0.5), (2, 1, 1.0)])
def test_multicolor_rejects_insufficient_exact_occupancy(height, width, density):
    with pytest.raises(ValueError):
        GEN.generate(
            37, 0, grid_h=height, grid_w=width,
            fg_density=density, multi_color=True,
        )


@pytest.mark.parametrize("texture", ["all_zero", "all_filled", "monochrome"])
def test_degenerate_texture_names_are_rejected(texture):
    with pytest.raises(ValueError):
        GEN.generate(41, 0, grid_h=3, grid_w=4, texture=texture)


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown_control": 1},
        {"bg_density": 0.4},
        {"noise_overlay": 0.2},
        {"grid_h": 0},
        {"grid_h": 16},
        {"grid_w": 0},
        {"grid_w": 16},
        {"grid_h": 2.5},
        {"grid_w": True},
        {"grid_h": "3"},
        {"grid_h": 1, "grid_w": 1},
        {"fg_color": 0},
        {"fg_color": 10},
        {"fg_color": 2.5},
        {"fg_color": True},
        {"fg_color": "3"},
        {"fg_density": -0.01},
        {"fg_density": 1.01},
        {"fg_density": float("nan")},
        {"fg_density": float("inf")},
        {"fg_density": True},
        {"fg_density": "0.5"},
        {"multi_color": "false"},
        {"multi_color": 1},
        {"texture": "unknown"},
        {"texture": 1},
    ],
    ids=[
        "unknown-key", "removed-background-density", "removed-noise-overlay",
        "height-zero", "height-16", "width-zero", "width-16", "float-height",
        "bool-width", "string-height", "singleton-area", "zero-foreground",
        "foreground-10", "float-foreground", "bool-foreground", "string-foreground",
        "negative-density", "density-above-one", "nan-density", "infinite-density",
        "bool-density", "string-density", "string-multicolor", "int-multicolor",
        "unknown-texture", "nonstring-texture",
    ],
)
def test_unknown_removed_malformed_or_out_of_range_controls_are_rejected(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(43, 0, **overrides)
