"""Task-local regression tests for the size-to-color legend generator."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
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
SPEC = importlib.util.spec_from_file_location("task_a7e26e20850c_generator", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _pairs():
    return canonical_pairs("a7e26e20850c", root=find_root(__file__))


def _legend_runs(grid):
    runs = []
    c = 0
    while c < len(grid[0]):
        color = grid[0][c]
        if color == 0:
            c += 1
            continue
        start = c
        while c < len(grid[0]) and grid[0][c] == color:
            c += 1
        runs.append((c - start, color))
    return runs


def _gray_components(grid):
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5 and r >= 2
    }
    components = []
    while remaining:
        seed = remaining.pop()
        stack = [seed]
        component = {seed}
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    stack.append(point)
        components.append(component)
    return components


def _solve(grid, *, legend_limit=None):
    out = deepcopy(grid)
    runs = _legend_runs(grid)
    if legend_limit is not None:
        runs = runs[:legend_limit]
    by_size = dict(runs)
    for component in _gray_components(grid):
        color = by_size.get(len(component), 5)
        for r, c in component:
            out[r][c] = color
    return out


def test_metadata_pins_canonical_rule_and_declares_semantic_contract():
    assert GEN.RULE_HASH == "704fe040d74c"
    assert GEN.EXAMPLES_NEEDED == 4
    assert GEN.LESSON_SCHEDULE_PERIOD == 4
    assert tuple(GEN.SCHEDULE_PROFILES) == (
        "two_sizes", "four_sizes_a", "three_sizes", "four_sizes_b"
    )
    assert "fourth_legend_used" in GEN.SEMANTIC_WITNESSES
    assert "first_three_legend_entries" in GEN.CANONICAL_SHORTCUTS


def test_canonical_inputs_are_accepted_and_independent_oracle_matches_labels():
    pairs = _pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert GEN.self_check(original) == []
        assert GEN.strict_canonical_like(original) == []
        assert _solve(original) == pair["output"]
        assert original == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 7, "grid_w": 12, "n_sizes": 2},
        {"grid_h": 10, "grid_w": 16, "n_sizes": 3},
        {"grid_h": 13, "grid_w": 18, "n_sizes": 4},
        {"grid_h": 9, "grid_w": 17, "n_sizes": 4},
        {"grid_h": 12, "grid_w": 14, "n_sizes": 2},
    ],
)
def test_every_compatible_exact_override_round_trips(band, requested):
    grid = GEN.generate(71, 8, difficulty=band, **requested)
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == requested
    assert len(_gray_components(grid)) == 3


@pytest.mark.parametrize("grid_w", [12, 13, 14, 15, 16])
def test_incompatible_four_entry_legend_width_is_rejected(grid_w):
    with pytest.raises(ValueError, match="incompatible|fit|width|legend"):
        GEN.generate(0, 0, n_sizes=4, grid_w=grid_w)


@pytest.mark.parametrize(
    "args,kwargs",
    [
        ((True, 0), {}),
        ((1.0, 0), {}),
        (("1", 0), {}),
        ((0, True), {}),
        ((0, -1), {}),
        ((0, 1.0), {}),
        ((0, 0), {"difficulty": "expert"}),
        ((0, 0), {"typo_axis": 3}),
        ((0, 0), {"grid_h": True}),
        ((0, 0), {"grid_w": 15.0}),
        ((0, 0), {"n_sizes": "3"}),
        ((0, 0), {"grid_h": 6}),
        ((0, 0), {"grid_w": 19}),
        ((0, 0), {"n_sizes": 5}),
    ],
)
def test_invalid_public_inputs_are_rejected(args, kwargs):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(*args, **kwargs)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_schedule_rotations_cover_all_size_counts_and_counterexample(band):
    profiles = tuple(GEN.SCHEDULE_PROFILES)
    for start in range(6):
        indices = range(start, start + len(profiles))
        grids = [GEN.generate(901, i, difficulty=band) for i in indices]
        expected = [profiles[i % len(profiles)] for i in indices]
        assert [GEN.schedule_profile(901, i, band) for i in indices] == expected
        observed = [GEN.observe_overrides(grid)["n_sizes"] for grid in grids]
        expected_counts = [2 if p == "two_sizes" else 3 if p == "three_sizes" else 4 for p in expected]
        assert observed == expected_counts
        witness_positions = [
            i for i, grid in enumerate(grids)
            if GEN.SEMANTIC_WITNESSES["fourth_legend_used"](grid)
        ]
        assert len(witness_positions) == 2
        for held_out in range(len(grids)):
            assert any(i != held_out for i in witness_positions)
        for i in witness_positions:
            assert GEN.SEMANTIC_RIVALS["first_three_legend_entries"](grids[i]) != _solve(grids[i])


def test_declared_shortcut_fits_all_canonical_pairs_but_generated_witness_refutes_it():
    rival = GEN.CANONICAL_SHORTCUTS["first_three_legend_entries"]
    assert all(rival(pair["input"]) == pair["output"] for pair in _pairs())
    witness = GEN.generate(712, 2, n_sizes=4, grid_w=18)
    assert GEN.SEMANTIC_WITNESSES["fourth_legend_used"](witness)
    assert rival(witness) == _solve(witness, legend_limit=3)
    assert rival(witness) != _solve(witness)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_generation_is_deterministic_lawful_and_diverse(band):
    seen = set()
    dimensions = set()
    size_counts = set()
    used_sizes = set()
    for index in range(90):
        grid = GEN.generate(2000 + index, index * 7 + 1, difficulty=band)
        assert grid == GEN.generate(2000 + index, index * 7 + 1, difficulty=band)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert len(_gray_components(grid)) == 3
        observed = GEN.observe_overrides(grid)
        assert 7 <= observed["grid_h"] <= 13
        assert 12 <= observed["grid_w"] <= 18
        assert 2 <= observed["n_sizes"] <= 4
        seen.add(tuple(map(tuple, grid)))
        dimensions.add((observed["grid_h"], observed["grid_w"]))
        size_counts.add(observed["n_sizes"])
        used_sizes.update(len(component) for component in _gray_components(grid))
    assert len(seen) >= 80
    assert len(dimensions) >= 15
    assert size_counts == {2, 3, 4}
    assert used_sizes == {2, 3, 4, 5}


def test_minimum_canvas_constructively_places_every_compatible_profile():
    for n_sizes, width in ((2, 12), (3, 12), (4, 17)):
        for index in range(128):
            grid = GEN.generate(40 + index, index, grid_h=7, grid_w=width, n_sizes=n_sizes)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == {
                "grid_h": 7,
                "grid_w": width,
                "n_sizes": n_sizes,
            }


def test_validator_rejects_structural_and_semantic_mutations():
    base = GEN.generate(4, 2, grid_h=10, grid_w=18, n_sizes=4)
    mutations = []

    duplicated_separator = deepcopy(base)
    duplicated_separator[1] = duplicated_separator[0][:]
    mutations.append(duplicated_separator)

    unknown_body_color = deepcopy(base)
    r, c = next(iter(_gray_components(unknown_body_color)[0]))
    unknown_body_color[r][c] = 9
    mutations.append(unknown_body_color)

    duplicate_legend_color = deepcopy(base)
    runs = _legend_runs(duplicate_legend_color)
    first_color = runs[0][1]
    seen_run = 0
    in_run = False
    for c, value in enumerate(duplicate_legend_color[0]):
        if value and not in_run:
            seen_run += 1
            in_run = True
        elif value == 0:
            in_run = False
        if seen_run == 2 and value:
            duplicate_legend_color[0][c] = first_color
    mutations.append(duplicate_legend_color)

    extra_object = deepcopy(base)
    placed = False
    for r in range(2, len(extra_object)):
        for c in range(len(extra_object[0])):
            if extra_object[r][c] != 0:
                continue
            if all(
                not (0 <= rr < len(extra_object) and 0 <= cc < len(extra_object[0]))
                or extra_object[rr][cc] == 0
                for rr in range(r - 1, r + 2)
                for cc in range(c - 1, c + 2)
            ):
                extra_object[r][c] = 5
                placed = True
                break
        if placed:
            break
    assert placed
    mutations.append(extra_object)

    mutations.extend([None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(7)]])
    for mutated in mutations:
        assert GEN.self_check(mutated), mutated


def test_solver_and_rival_do_not_mutate_inputs():
    grid = GEN.generate(19, 2, grid_w=18, n_sizes=4)
    original = deepcopy(grid)
    assert _solve(grid) != GEN.SEMANTIC_RIVALS["first_three_legend_entries"](grid)
    assert grid == original


def test_retained_first_three_counterexample_is_minimal_and_executable():
    path = HOME / "counterexamples" / "first-three-legend.json"
    record = json.loads(path.read_text())
    grid = record["input"]
    intended = record["intended_output"]
    rival = record["first_three_rival_output"]
    assert GEN.self_check(grid) == []
    assert GEN.SEMANTIC_WITNESSES["fourth_legend_used"](grid)
    assert _solve(grid) == intended
    assert GEN.SEMANTIC_RIVALS["first_three_legend_entries"](grid) == rival
    assert intended != rival
    differing = [
        [r, c] for r in range(len(grid)) for c in range(len(grid[0]))
        if intended[r][c] != rival[r][c]
    ]
    assert differing == record["differing_cells"]
