"""Behavioral regression tests for the task-local rank-and-stack repair.

Canonical labels come from this checkout's selected task record. Component
geometry below is an independent observer, not a replacement label authority.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root

TASK_ID = "595eebab5aea"
HERE = Path(__file__).resolve()
SOURCE = HERE.parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("rank_stack_repaired_sampler", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)
PAIRS = canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)
BANDS = (None, "easy", "medium", "hard")


def body_objects(grid):
    """Observe same-color four-neighbor components below the rank row."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(1, h):
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
                for nr, nc in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (1 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            top = min(rr for rr, cc in cells)
            left = min(cc for rr, cc in cells)
            bottom = max(rr for rr, cc in cells)
            right = max(cc for rr, cc in cells)
            result.append({
                "color": color, "area": len(cells), "top": top, "left": left,
                "bottom": bottom, "height": bottom - top + 1,
                "width": right - left + 1,
                "shape": tuple(sorted((rr - top, cc - left) for rr, cc in cells)),
            })
    return result


def area_pattern(objects):
    return {1: "all_tied", 2: "pair_tie", 3: "distinct"}[len({obj["area"] for obj in objects})]


def alignment_profile(objects):
    widths = [obj["width"] for obj in objects]
    return "wide_gap" if max(widths) - min(widths) >= 2 else "narrow_gap"


def position_bias(objects):
    return {1: "same_top", 2: "paired_top", 3: "staggered"}[len({obj["top"] for obj in objects})]


def same_top_tie(objects):
    return any(a["area"] == b["area"] and a["top"] == b["top"]
               for i, a in enumerate(objects) for b in objects[i + 1:])


def taller_left_tie(objects):
    return any(a["area"] == b["area"] and a["top"] == b["top"]
               and a["left"] < b["left"] and a["height"] > b["height"]
               for a in objects for b in objects)


def smallest_largest_middle(objects):
    if area_pattern(objects) != "distinct":
        return False
    raster = [obj["area"] for obj in sorted(objects, key=lambda obj: (obj["top"], obj["left"]))]
    small, middle, large = sorted(raster)
    return raster == [small, large, middle]


@pytest.mark.parametrize("pair_index", range(5))
def test_all_canonical_inputs_are_accepted(pair_index):
    assert len(PAIRS) == 5
    grid = deepcopy(PAIRS[pair_index]["input"])
    assert GEN.self_check(grid) == []
    assert GEN.strict_canonical_like(grid) in ([], True)


@pytest.mark.parametrize("grid", [
    None, [], [[]], [[0]], [[0, 1], [0]], [[0, True], [0, 0]],
    [[0, 1.0], [0, 0]], [[0, "1"], [0, 0]], [[0, 10], [0, 0]],
])
def test_self_check_reports_malformed_grids_without_crashing(grid):
    errors = GEN.self_check(grid)
    assert isinstance(errors, list)
    assert errors and all(isinstance(error, str) for error in errors)


def test_unknown_and_retired_controls_are_rejected():
    retired = {
        "unknown_axis": "typo", "texture": "warm", "palette_kind": "warm",
        "palette_size": 6, "n_distinct_colors": 6, "density": "sparse",
    }
    for name, value in retired.items():
        with pytest.raises((TypeError, ValueError), match=".+"):
            GEN.generate(17, 0, **{name: value})


@pytest.mark.parametrize("name", ("sample_index", "grid_h", "grid_w"))
def test_indices_and_dimensions_reject_non_integer_or_invalid_values(name):
    valid = 13 if name == "grid_w" else 12
    for bad in (True, False, float(valid), str(valid), -1):
        with pytest.raises((TypeError, ValueError), match=".+"):
            if name == "sample_index":
                GEN.generate(17, bad)
            else:
                GEN.generate(17, 0, **{name: bad})


@pytest.mark.parametrize("band", BANDS)
def test_dimension_overrides_are_exact_in_every_band(band):
    for h in range(11, 19):
        for w in (12, 18):
            grid = GEN.generate(34, h, difficulty=band, grid_h=h, grid_w=w)
            assert (len(grid), len(grid[0])) == (h, w)
            assert GEN.self_check(grid) == []
    for w in range(12, 19):
        for h in (11, 18):
            grid = GEN.generate(35, w, difficulty=band, grid_h=h, grid_w=w)
            assert (len(grid), len(grid[0])) == (h, w)
            assert GEN.self_check(grid) == []


@pytest.mark.parametrize("band", BANDS)
def test_default_draws_have_three_complete_bodies_and_live_variation(band):
    patterns = set()
    observed_alignment = set()
    tied_at_same_top = False
    for seed in (7, 29, 83):
        for index in range(18):
            grid = GEN.generate(seed, index, difficulty=band)
            assert GEN.self_check(grid) == []
            objects = body_objects(grid)
            assert len(objects) == 3
            assert all(2 <= obj["area"] <= 10 for obj in objects)
            assert len({obj["color"] for obj in objects}) == 3
            ranks = [value for value in grid[0] if value]
            assert len(ranks) == len(set(ranks)) == 3
            assert not set(ranks) & {obj["color"] for obj in objects}
            patterns.add(area_pattern(objects))
            observed_alignment.add(alignment_profile(objects))
            tied_at_same_top |= same_top_tie(objects)
    assert {"distinct", "pair_tie", "all_tied"} <= patterns
    assert "wide_gap" in observed_alignment
    assert tied_at_same_top


def test_shape_area_is_not_a_fixed_template_lookup():
    geometries = {}
    for seed in (13, 41, 79):
        for index in range(45):
            for obj in body_objects(GEN.generate(seed, index)):
                geometries.setdefault(obj["area"], set()).add(obj["shape"])
    assert len([area for area, shapes in geometries.items() if len(shapes) > 1]) >= 3


def test_curriculum_declares_five_demonstrations_and_three_profiles():
    assert GEN.EXAMPLES_NEEDED == 5
    assert GEN.LESSON_SCHEDULE_PERIOD == 3
    assert callable(GEN.schedule_profile)


@pytest.mark.parametrize("band", BANDS)
def test_every_cyclic_six_pair_window_keeps_witnesses_after_rotation(band):
    for seed in (19, 53):
        rows = [body_objects(GEN.generate(seed, index, difficulty=band)) for index in range(11)]
        for start in range(6):
            window = rows[start:start + 6]
            for held_out in range(6):
                demos = [objects for i, objects in enumerate(window) if i != held_out]
                assert any(alignment_profile(objects) == "wide_gap" for objects in demos)
                assert any(taller_left_tie(objects) for objects in demos)
                assert any(smallest_largest_middle(objects) for objects in demos)


def test_exact_semantic_controls_match_independent_grid_observations():
    assert set(GEN.AXES) == {"grid_h", "grid_w", "area_pattern", "alignment_profile", "position_bias"}
    index = 0
    for areas in ("distinct", "pair_tie", "all_tied"):
        for alignment in ("narrow_gap", "wide_gap"):
            for position in ("staggered", "paired_top", "same_top"):
                requested = {"grid_h": 11, "grid_w": 12, "area_pattern": areas,
                             "alignment_profile": alignment, "position_bias": position}
                grid = GEN.generate(131, index, difficulty="hard", **requested)
                assert GEN.self_check(grid) == []
                objects = body_objects(grid)
                realized = {"grid_h": len(grid), "grid_w": len(grid[0]),
                            "area_pattern": area_pattern(objects),
                            "alignment_profile": alignment_profile(objects),
                            "position_bias": position_bias(objects)}
                assert realized == requested
                reported = GEN.observe_overrides(grid)
                assert {key: reported[key] for key in requested} == realized
                index += 1


def test_declared_canonical_shortcuts_are_pure_and_fit_every_canonical_pair():
    required = {
        "left_align", "tie_rightmost", "tie_bottom_first", "largest_then_raster",
        "tie_taller_first", "tie_narrower_first", "tie_color_ascending", "tie_color_descending",
        "tie_bbox_area_descending",
    }
    shortcuts = GEN.CANONICAL_SHORTCUTS
    assert required <= set(shortcuts)
    assert required <= set(GEN.LESSON_COMPETITORS)
    assert "area_then_bbox_descending" in GEN.LESSON_COMPETITORS
    for name, solve in shortcuts.items():
        assert callable(solve), name
        for pair in PAIRS:
            grid = deepcopy(pair["input"])
            original = deepcopy(grid)
            first = solve(grid)
            assert grid == original, name
            assert first == pair["output"], (name, pair["split"], pair["pair_index"])
            assert solve(deepcopy(grid)) == first, name


def test_semantic_witnesses_are_boolean_and_refer_to_callable_rivals():
    witnesses = GEN.SEMANTIC_WITNESSES
    rivals = GEN.SEMANTIC_RIVALS
    links = GEN.WITNESS_RIVALS
    assert witnesses and links
    for witness, names in links.items():
        assert witness in witnesses
        if isinstance(names, str):
            names = [names]
        assert names
        assert all(name in rivals and callable(rivals[name]) for name in names)
    hits = {name: 0 for name in witnesses}
    for index in range(18):
        grid = GEN.generate(37, index)
        for name, predicate in witnesses.items():
            argument = deepcopy(grid)
            result = predicate(argument)
            assert type(result) is bool, name
            assert argument == grid, name
            hits[name] += result
    assert all(hits.values()), hits


def test_every_cyclic_window_refutes_new_tie_rivals_after_any_holdout():
    # Seed 61/start 40 was independently Racket-labeled: taller-first fit every
    # demonstration and changed the query in the first repair. Check each of
    # the three cyclic starts using geometric/color order, not Python labels.
    criteria = {
        "tie_taller_first": lambda a, b: a["height"] < b["height"],
        "tie_narrower_first": lambda a, b: a["width"] > b["width"],
        "tie_color_ascending": lambda a, b: a["color"] > b["color"],
        "tie_color_descending": lambda a, b: a["color"] < b["color"],
    }

    def refutes(objects, criterion):
        return any(
            a["area"] == b["area"] and a["top"] == b["top"]
            and a["left"] < b["left"] and a["shape"] != b["shape"]
            and criterion(a, b)
            for a in objects for b in objects
        )

    for band in BANDS:
        rows = [body_objects(GEN.generate(61, index, difficulty=band))
                for index in range(40, 48)]
        for phase in range(3):
            window = rows[phase:phase + 6]
            for held_out in range(6):
                demos = [objects for i, objects in enumerate(window) if i != held_out]
                for name, criterion in criteria.items():
                    assert any(refutes(objects, criterion) for objects in demos), (
                        band, 40 + phase, held_out, name,
                    )


def test_cyclic_windows_refute_bbox_area_tie_shortcuts_after_any_holdout():
    # Canonical Racket labels verified the old seed61/start43 ambiguity. A same-
    # top equal-area pair with increasing bbox area contradicts both measured
    # decreasing-bbox-area keys without using a Python output-label oracle.
    def refutes(objects):
        return any(
            a["area"] == b["area"] and a["top"] == b["top"]
            and a["left"] < b["left"]
            and a["height"] * a["width"] < b["height"] * b["width"]
            for a in objects for b in objects
        )

    for band in BANDS:
        rows = [body_objects(GEN.generate(61, index, difficulty=band))
                for index in range(43, 51)]
        for phase in range(3):
            window = rows[phase:phase + 6]
            for held_out in range(6):
                demos = [objects for i, objects in enumerate(window) if i != held_out]
                assert any(refutes(objects) for objects in demos), (band, 43 + phase, held_out)
