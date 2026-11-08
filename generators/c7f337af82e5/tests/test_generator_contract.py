"""Behavioral regressions for the public sampler, portable into review runtimes."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, canonical_path, find_root

TASK = "c7f337af82e5"
ROOT = find_root(__file__)
SOURCE = next(p for p in (
    ROOT / "generators" / TASK / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
) if p.is_file())
SPEC = importlib.util.spec_from_file_location("reviewed_control_objects", SOURCE)
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def objects(grid):
    """Independent flood fill and rectangle measurements, not generator helpers."""
    pending = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7}
    result = []
    while pending:
        cell = min(pending)
        pending.remove(cell)
        component, todo = {cell}, [cell]
        while todo:
            r, c = todo.pop()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in pending:
                    pending.remove(p)
                    component.add(p)
                    todo.append(p)
        rs, cs = zip(*component)
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        box = {(r, c) for r in range(r0, r1 + 1) for c in range(c0, c1 + 1)}
        edge = {(r, c) for r, c in box if r in (r0, r1) or c in (c0, c1)}
        result.append({"cells": component, "bbox": (r0, c0, r1, c1),
                       "area": len(component), "bbox_area": len(box),
                       "solid": component == box,
                       "hollow": r1 - r0 >= 2 and c1 - c0 >= 2 and component == edge})
    return result


def expected_output(grid):
    out = [row[:] for row in grid]
    out[0][0] = 0
    for obj in objects(grid):
        if (grid[0][0] == 1 and obj["hollow"]) or (grid[0][0] == 2 and obj["solid"]):
            for r, c in obj["cells"]:
                out[r][c] = 8
    return out


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_control_override_changes_only_the_control_pixel(band):
    # Catches the baseline's unconsumed control axis and accidental geometry leakage.
    for seed in range(8):
        one = GEN.generate(seed, 0, difficulty=band, control=1)
        two = GEN.generate(seed, 0, difficulty=band, control=2)
        assert one[0][0] == 1
        assert two[0][0] == 2
        two[0][0] = 1
        assert one == two


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_exact_joint_controls_work_at_boundaries_in_every_band(band):
    # Catch clipped counts, band-limited dimensions, or impossible advertised combinations.
    for seed in (0, 17):
        for height in (8, 16):
            for width in (9, 18):
                for count in (2, 3, 4):
                    for control in (1, 2):
                        grid = GEN.generate(seed, 1, difficulty=band, grid_h=height,
                                            grid_w=width, n_objects=count, control=control)
                        assert (len(grid), len(grid[0]), grid[0][0]) == (height, width, control)
                        components = objects(grid)
                        assert len(components) == count
                        assert all(o["hollow"] or o["solid"] for o in components)
                        assert any(o["hollow"] for o in components)
                        assert any(o["solid"] for o in components)
                        assert GEN.self_check(grid) == []
                        assert GEN.observe_overrides(grid) == {
                            "grid_h": height, "grid_w": width,
                            "control": control, "n_objects": count,
                        }


@pytest.mark.parametrize("overrides", [
    {"typo": 1}, {"palette_kind": "warm"}, {"texture": "default"},
    {"control": 0}, {"control": 3}, {"control": True}, {"control": "1"},
    {"grid_h": 7}, {"grid_h": 17}, {"grid_h": 8.0},
    {"grid_w": 8}, {"grid_w": 19}, {"n_objects": 1}, {"n_objects": 5},
])
def test_invalid_and_removed_controls_fail_explicitly(overrides):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, 0, **overrides)


@pytest.mark.parametrize("bad", [None, [], [[]], [[1], []], [[1, 0], [0]],
                                  [[True, 0], [0, 7]], [[1, 0], [0, 7.0]]])
def test_malformed_grids_return_diagnostics_instead_of_crashing(bad):
    assert GEN.self_check(bad)


def test_validator_rejects_extra_control_and_unadvertised_colors():
    grid = GEN.generate(6, 0, grid_h=16, grid_w=18)
    for color in (1, 2, 3, 8, 9):
        altered = [row[:] for row in grid]
        empty = next((r, c) for r, row in enumerate(altered) for c, v in enumerate(row)
                     if v == 0 and (r, c) != (0, 0))
        altered[empty[0]][empty[1]] = color
        assert GEN.self_check(altered), color


def test_canonical_inputs_and_rival_claims_are_validated_against_all_pairs():
    pairs = canonical_pairs(TASK, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
    assert GEN.CANONICAL_SHORTCUTS
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        assert all(rival(p["input"]) == p["output"] for p in pairs), name
    with canonical_path(ROOT).open() as stream:
        record = next(row for row in map(json.loads, stream) if row["task_id"] == TASK)
    normalized_rule = " ".join(record["program_solution"].split())
    assert GEN.RULE_HASH == hashlib.sha256(normalized_rule.encode()).hexdigest()[:12]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_retains_profiles_and_breaks_size_count_and_border_restrictions(band):
    found = set()
    for seed in range(8):
        grids = [GEN.generate(seed, i, difficulty=band) for i in range(16)]
        for grid in grids:
            assert GEN.self_check(grid) == []
            parts = objects(grid)
            hollow = [o for o in parts if o["hollow"]]
            solid = [o for o in parts if o["solid"]]
            found.add(("shape", len(grid), len(grid[0])))
            found.add(("count", len(parts)))
            if any(o["solid"] and o["bbox_area"] == 4 for o in parts):
                found.add("canonical_small_solid")
            if any(a["area"] < b["area"] for a in hollow for b in solid):
                found.add("reversed_area")
            if any(a["bbox_area"] == b["bbox_area"] for a in hollow for b in solid):
                found.add("equal_bbox")
            if any(a["bbox_area"] < b["bbox_area"] for a in hollow for b in solid):
                found.add("reversed_bbox")
            if any(r in (0, len(grid)-1) or c in (0, len(grid[0])-1)
                   for o in parts for r, c in o["cells"]):
                found.add("border")
        # Any query rotation of a five-pair lesson must still demonstrate both controls.
        for start in range(12):
            window = grids[start:start+5]
            for query in range(5):
                assert {g[0][0] for i, g in enumerate(window) if i != query} == {1, 2}
    assert {("shape", 8, 9), ("shape", 11, 10), ("count", 2), ("count", 3),
            ("count", 4), "canonical_small_solid", "reversed_area", "equal_bbox",
            "reversed_bbox", "border"} <= found


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_rotations_refute_branch_specific_canonical_shortcuts(band):
    # A shortcut may apply only under one control and use the intended rule
    # under the other. One counterexample anywhere in a lesson is insufficient.
    for seed in (0, 1, 9, 17, 52):
        pairs = []
        for index in range(16):
            grid = GEN.generate(seed, index, difficulty=band)
            pairs.append({"input": grid, "output": expected_output(grid)})
        for start in range(12):
            window = pairs[start:start + 5]
            for query_index, query in enumerate(window):
                demos = [p for i, p in enumerate(window) if i != query_index
                         and p["input"][0][0] == query["input"][0][0]]
                for name, rival in GEN.CANONICAL_SHORTCUTS.items():
                    ambiguity = (all(rival(p["input"]) == p["output"] for p in demos)
                                 and rival(query["input"]) != query["output"])
                    assert not ambiguity, (band, seed, start, query_index, name)


def test_contrast_also_refutes_the_canonical_perimeter_shortcut():
    # The baseline's frame perimeter is ALWAYS larger than its solid perimeter.
    # A larger-area solid alone does not necessarily break that shortcut.
    for index in range(5):
        if not GEN.schedule_profile(17, index).startswith("contrast"):
            continue
        grid = GEN.generate(17, index, grid_h=16, grid_w=18, n_objects=2)
        parts = objects(grid)
        perimeters = [sum((r + dr, c + dc) not in p["cells"]
                          for r, c in p["cells"]
                          for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                      for p in parts]
        rival = [row[:] for row in grid]
        rival[0][0] = 0
        for obj, perimeter in zip(parts, perimeters):
            if (perimeter != min(perimeters)) == (grid[0][0] == 1):
                for r, c in obj["cells"]:
                    rival[r][c] = 8
        assert rival != expected_output(grid)


def test_production_duplicate_rejection_keeps_each_query_taught():
    # Actual Racket census regression: easy seed 1115388330, start 7 skipped
    # duplicate index 10, accepted [7,8,9,11,12], then a rotated query was ambiguous.
    for seed, start in ((1115388330, 7), (0, 0), (17, 4), (52, 9)):
        seen, pairs = set(), []
        for index in range(start, start + 30):
            grid = GEN.generate(seed, index, difficulty="easy")
            key = tuple(map(tuple, grid))
            if key in seen:
                continue
            seen.add(key)
            pairs.append({"input": grid, "output": expected_output(grid)})
            if len(pairs) == 5:
                break
        assert len(pairs) == 5
        for query_index, query in enumerate(pairs):
            demos = [p for i, p in enumerate(pairs) if i != query_index]
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert not (all(rival(p["input"]) == p["output"] for p in demos)
                            and rival(query["input"]) != query["output"]), (seed, start, query_index, name)
