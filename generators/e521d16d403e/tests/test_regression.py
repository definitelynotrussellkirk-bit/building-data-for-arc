"""Portable task regressions for the exact six-axis symmetry curriculum.

The component parser and crop oracle below read only pixels. They do not call
generator geometry helpers or use generation metadata to validate overrides.
Canonical authoring labels are read through the public portable helper.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import random

import pytest

from puzzle_generators.base import set_ctx_observer
from reviewer_support import canonical_pairs, find_root


TASK_ID = "e521d16d403e"
ROOT = find_root(__file__)
SOURCE = ROOT / "generators" / TASK_ID / "generator.py"
if not SOURCE.is_file():
    SOURCE = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
SPEC = importlib.util.spec_from_file_location("symmetry_regression_generator", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
AXIS_BOUNDS = {
    "grid_h": (10, 22), "grid_w": (10, 22),
    "sym_h": (2, 6), "sym_w": (2, 7),
    "n_asym": (1, 3), "n_sym_decoy": (0, 2),
}
BANDS = (None, "easy", "medium", "hard")


def _objects(grid):
    """Same-color four-connectivity, retaining row-major component order."""
    seen = set()
    objects = []
    h, w = len(grid), len(grid[0])
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            todo = [(r, c)]
            seen.add((r, c))
            cells = []
            while todo:
                rr, cc = todo.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
            c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
            crop = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
            objects.append({"cells": tuple(sorted(cells)), "size": len(cells),
                            "bbox": (r0, c0, r1, c1), "crop": crop,
                            "height": r1 - r0 + 1, "width": c1 - c0 + 1,
                            "eligible": c1 > c0 and all(row == row[::-1] for row in crop)})
    return objects


def _oracle(grid):
    """Reference behavior, including stable tie order and first-object fallback."""
    objects = _objects(grid)
    eligible = [obj for obj in objects if obj["eligible"]]
    selected = max(eligible, key=lambda obj: obj["size"]) if eligible else objects[0]
    return deepcopy(selected["crop"])


def _measure(grid):
    objects = _objects(grid)
    eligible = [obj for obj in objects if obj["eligible"]]
    assert eligible, "curriculum must supply an eligible object of width > 1"
    answer = max(eligible, key=lambda obj: obj["size"])
    assert sum(obj["size"] == answer["size"] for obj in eligible) == 1, "winner must be unique"
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "sym_h": answer["height"], "sym_w": answer["width"],
            "n_asym": len(objects) - len(eligible), "n_sym_decoy": len(eligible) - 1}


def _assert_draw(seed, index, band, overrides=None):
    overrides = dict(overrides or {})
    contexts = []
    set_ctx_observer(contexts.append)
    try:
        grid = GEN.generate(seed, index, difficulty=band, **overrides)
    finally:
        set_ctx_observer(None)
    assert grid and all(len(row) == len(grid[0]) for row in grid)
    assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    measured = _measure(grid)
    assert GEN.self_check(grid, difficulty=band) == []
    assert callable(getattr(GEN, "observe_overrides", None)), "exact axes require a pixel observer"
    observed = GEN.observe_overrides(deepcopy(grid))
    for key, bounds in AXIS_BOUNDS.items():
        assert bounds[0] <= measured[key] <= bounds[1], (key, measured)
        assert observed.get(key) == measured[key], (key, observed, measured)
    for key, value in overrides.items():
        assert measured[key] == value, (key, value, measured)
    assert contexts, "default and explicit axes must have keyed draw provenance"
    drawn = contexts[-1].recorded_draws()
    for key in AXIS_BOUNDS:
        assert drawn.get(key) == measured[key], (key, drawn, measured)
    assert contexts[-1].overrides_used() == overrides
    return grid, measured


def test_advertised_axes_are_the_six_supported_exact_controls():
    assert set(GEN.AXES) == set(AXIS_BOUNDS)
    for name, (lo, hi) in AXIS_BOUNDS.items():
        assert GEN.AXES[name]["type"] == "int"
        assert GEN.AXES[name]["valid"] == f"{lo}..{hi}"


def test_all_canonical_pairs_use_same_color_four_connectivity_and_raw_crops():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert len(pairs) == 8, "retain both canonical variants and every available label"
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert _oracle(original) == pair["output"], pair
        assert GEN.self_check(original) == [], pair
        assert original == pair["input"], "self_check must be pure"


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_bands_have_exact_provenance_and_ten_by_ten_support(band):
    shapes = set()
    for index in range(120):
        grid, measured = _assert_draw(20261004, index, band)
        shapes.add((measured["grid_h"], measured["grid_w"]))
        if index in (0, 3, 47, 119):
            assert grid == GEN.generate(20261004, index, difficulty=band)
    assert (10, 10) in shapes, (band, shapes)


@pytest.mark.parametrize("width", [2, 4, 6])
def test_even_widths_are_full_symmetric_selected_bboxes(width):
    for band in BANDS:
        for height in (2, 6):
            _assert_draw(0, 0, band, {"sym_h": height, "sym_w": width})


@pytest.mark.parametrize("values", [
    (10, 10, 6, 7, 3, 2),
    (22, 22, 2, 2, 1, 0),
    (10, 22, 6, 2, 3, 2),
    (22, 10, 2, 7, 3, 2),
])
def test_joint_boundaries_are_exact_in_every_difficulty(values):
    overrides = dict(zip(AXIS_BOUNDS, values))
    for band in BANDS:
        for seed in (0, 21, 47):
            _assert_draw(seed, 0, band, overrides)


def test_previous_crowded_placement_never_silently_drops_requested_objects():
    overrides = {"grid_h": 12, "grid_w": 12, "sym_h": 6, "sym_w": 7,
                 "n_asym": 3, "n_sym_decoy": 2}
    for seed in (0, 3, 5, 47, 126):
        grid, measured = _assert_draw(seed, 0, "easy", overrides)
        assert len(_objects(grid)) == 6
        assert measured == overrides


def test_removed_axes_and_unknown_keys_fail_loudly():
    bad = {"palette_kind": "warm", "palette_size": 3,
           "position_bias": "centered", "anchor_corner": True,
           "texture": "full_grid", "__override_contract_unknown_axis__": 1}
    for key, value in bad.items():
        with pytest.raises((TypeError, ValueError), match="(?i)unknown|unsupported|unexpected"):
            GEN.generate(1, 0, **{key: value})


def test_integer_axis_out_of_domain_values_fail_loudly():
    for key, (lo, hi) in AXIS_BOUNDS.items():
        for value in (lo - 1, hi + 1):
            with pytest.raises((TypeError, ValueError)):
                GEN.generate(1, 0, **{key: value})


def test_integer_axis_types_are_not_coerced_or_silently_ignored():
    for key, (lo, _hi) in AXIS_BOUNDS.items():
        for value in (True, float(lo), str(lo), None):
            with pytest.raises((TypeError, ValueError)):
                GEN.generate(1, 0, **{key: value})


def test_self_check_returns_errors_for_malformed_or_nondigit_grids():
    for grid in ([], [[]], [[1, 1], [1]], [[1.0, 1.0]], [[True, True]],
                 [[-1, -1]], [[10, 10]], [["1", "1"]]):
        errors = GEN.self_check(grid)
        assert isinstance(errors, list) and errors, grid


def test_curriculum_rejects_no_eligible_width_one_and_tied_winners():
    grids = [
        [[0, 0], [0, 0]],
        [[3, 0, 0, 0, 0], [3, 0, 2, 2, 0], [3, 0, 2, 0, 0]],
        [[1, 1, 0, 2, 2], [1, 1, 0, 2, 2]],
    ]
    for grid in grids:
        assert GEN.self_check(grid), grid


def test_lone_eligible_component_is_outside_the_selected_curriculum_domain():
    grids = [
        [[2, 2]],
        [[2, 2], [2, 2]],
        [[3, 3, 3], [3, 3, 3]],
    ]
    for grid in grids:
        assert GEN.self_check(grid), grid


def test_touching_colors_and_diagonal_fragments_with_distractors_are_lawful():
    grids = [
        [[0, 0, 0, 0, 0], [0, 1, 1, 2, 0], [0, 1, 1, 2, 0]],
        [[0, 0, 0, 0, 0], [0, 1, 1, 0, 0], [0, 1, 1, 0, 0],
         [0, 0, 0, 1, 0], [0, 0, 0, 0, 0]],
    ]
    for grid in grids:
        assert GEN.self_check(grid) == [], grid


def test_symmetry_uses_actual_bbox_pixels_instead_of_component_mask():
    grid = [[0, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 1, 2, 0, 0, 1, 0],
            [0, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 0]]
    assert not any(obj["eligible"] for obj in _objects(grid))
    assert GEN.self_check(grid)


def test_observer_measures_fresh_pixels_without_generation_metadata():
    grid = [[0] * 10 for _ in range(10)]
    for r in (1, 2):
        for c in (1, 2, 3, 4):
            grid[r][c] = 8
    grid[6][1:3] = [2, 2]
    for r in (5, 6, 7):
        grid[r][7] = 4
    expected = {"grid_h": 10, "grid_w": 10, "sym_h": 2, "sym_w": 4,
                "n_asym": 1, "n_sym_decoy": 1}
    assert _measure(grid) == expected
    assert GEN.observe_overrides(deepcopy(grid)) == expected
    recolored = [[0 if value == 0 else 10 - value for value in row[::-1]] for row in grid]
    assert GEN.observe_overrides(recolored) == expected


def test_draws_are_independent_of_global_rng_and_return_fresh_grids():
    state = random.getstate()
    first = GEN.generate(5, 7, difficulty="hard")
    assert random.getstate() == state
    GEN.generate(999, 26, difficulty="easy", sym_w=6)
    replay = GEN.generate(5, 7, difficulty="hard")
    assert first == replay and first is not replay
    first[0][0] = (first[0][0] + 1) % 10
    assert GEN.generate(5, 7, difficulty="hard") == replay
    assert random.getstate() == state


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75])
def test_seed_is_a_strict_integer(seed):
    with pytest.raises(TypeError):
        GEN.generate(seed, 0, difficulty="easy")


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75])
def test_sample_index_is_a_strict_integer(sample_index):
    with pytest.raises(TypeError):
        GEN.generate(991, sample_index, difficulty="easy")


def test_sample_index_must_be_nonnegative():
    with pytest.raises(ValueError):
        GEN.generate(991, -1, difficulty="easy")


def test_every_declared_canonical_shortcut_fits_all_usable_canonical_labels():
    shortcuts = getattr(GEN, "CANONICAL_SHORTCUTS", None)
    assert isinstance(shortcuts, dict) and shortcuts
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    for name, shortcut in shortcuts.items():
        assert callable(shortcut), name
        for pair in pairs:
            original = deepcopy(pair["input"])
            assert shortcut(original) == pair["output"], (name, pair)
            assert original == pair["input"], f"shortcut {name} mutated input"


def _second_largest_object(grid):
    """Independent shortcut: sort all components by occupied size, ignore symmetry."""
    components = sorted(_objects(grid), key=lambda component: component["size"], reverse=True)
    return deepcopy(components[min(1, len(components) - 1)]["crop"])


def test_default_answer_cell_rank_is_not_always_second():
    ranks = set()
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 17):
            for index in range(8):
                grid = GEN.generate(seed, index, difficulty=band)
                components = _objects(grid)
                winner = max((component for component in components if component["eligible"]),
                             key=lambda component: component["size"])
                ranks.add(1 + sum(component["size"] > winner["size"] for component in components))
    assert len(ranks) > 1 and any(rank != 2 for rank in ranks), (
        "fixed occupied-size rank is a shortcut that bypasses symmetry", ranks)


def test_every_default_window_retains_two_second_largest_counterexamples():
    for band in ("easy", "medium", "hard"):
        for seed in (0, 17, 37):
            for start in range(4):
                grids = [GEN.generate(seed, start + offset, difficulty=band) for offset in range(4)]
                refutations = [_second_largest_object(grid) != _oracle(grid) for grid in grids]
                assert sum(refutations) >= 2, (band, seed, start, refutations)
                # Two witnesses ensure every possible single-query holdout
                # retains at least one counterexample among its three demos.
                for held_out in range(4):
                    assert any(refuted for index, refuted in enumerate(refutations) if index != held_out)

def _bottommost_lr(grid):
    """Canonical-fitting shortcut from the retained audit finding."""
    eligible = [obj for obj in _objects(grid) if obj["eligible"]]
    selected = max(eligible, key=lambda obj: (obj["bbox"][2], obj["bbox"][0]))
    return deepcopy(selected["crop"])


def test_bottommost_lr_is_declared_canonical_shortcut():
    assert "bottommost_lr" in GEN.CANONICAL_SHORTCUTS
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert _bottommost_lr(pair["input"]) == pair["output"]
        assert GEN.CANONICAL_SHORTCUTS["bottommost_lr"](pair["input"]) == pair["output"]


def test_every_default_window_retains_two_bottommost_counterexamples():
    for band in ("easy", "medium", "hard"):
        for seed in (0, 1, 17, 37):
            for start in range(4):
                grids = [GEN.generate(seed, start + offset, difficulty=band) for offset in range(4)]
                refutations = [_bottommost_lr(grid) != _oracle(grid) for grid in grids]
                assert sum(refutations) >= 2, (band, seed, start, refutations)
                for held_out in range(4):
                    assert any(refuted for index, refuted in enumerate(refutations)
                               if index != held_out), (band, seed, start, held_out, refutations)

