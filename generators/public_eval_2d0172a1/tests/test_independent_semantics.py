"""Original-data schematic oracle, frozen before candidate exposure."""
from collections import Counter, deque


def neighbors(point, connectivity=4):
    r, c = point
    result = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
    if connectivity == 8:
        result += [(r + dr, c + dc) for dr in (-1, 1) for dc in (-1, 1)]
    return result


def bbox(cells):
    return (min(r for r, c in cells), min(c for r, c in cells), max(r for r, c in cells), max(c for r, c in cells))


def cavity(cells, connectivity=4):
    top, left, bottom, right = bbox(cells)
    rectangle = {(r, c) for r in range(top - 1, bottom + 2) for c in range(left - 1, right + 2)}
    free = rectangle - cells
    seed = (top - 1, left - 1)
    reached, queue = {seed}, deque([seed])
    while queue:
        for nxt in neighbors(queue.popleft(), connectivity):
            if nxt in free and nxt not in reached:
                reached.add(nxt)
                queue.append(nxt)
    return free - reached


def inspect(grid, connectivity=4, hole_connectivity=4):
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("Expected a nonempty rectangular grid")
    counts = Counter(value for row in grid for value in row)
    if len(counts) != 2:
        raise ValueError("Expected exactly two colors")
    (background, bcount), (foreground, fcount) = counts.most_common()
    if bcount == fcount:
        raise ValueError("The modeled input grammar requires a unique majority background")
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == foreground}
    components = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        cells, queue = {seed}, deque([seed])
        while queue:
            for nxt in neighbors(queue.popleft(), connectivity):
                if nxt in remaining:
                    remaining.remove(nxt)
                    cells.add(nxt)
                    queue.append(nxt)
        inside = cavity(cells, hole_connectivity)
        components.append({"id": len(components), "cells": cells, "bounds": bbox(cells), "inside": inside, "kind": "loop" if inside else "blob"})
    return {"background": background, "foreground": foreground, "components": components}


def select_components(components, frame_policy="all"):
    if frame_policy not in ("all", "outermost"):
        raise ValueError("frame_policy must be all or outermost")
    if frame_policy == "all":
        return list(components)
    return [item for item in components if item["kind"] == "blob" or not any(item["cells"] <= other["inside"] for other in components if other["id"] != item["id"] and other["kind"] == "loop")]


def coordinate_groups(components, axis, blob_mode="span", merge_mode="overlap", pitch=2):
    events = []
    for item in components:
        low, high = item["bounds"][axis], item["bounds"][axis + 2]
        if item["kind"] == "loop":
            events += [(low, low, (item["id"], "low"), "loop"), (high, high, (item["id"], "high"), "loop")]
        else:
            if blob_mode == "center":
                low = high = (low + high) / 2
            elif blob_mode == "low":
                high = low
            elif blob_mode == "high":
                low = high
            events.append((low, high, (item["id"], "point"), "blob"))
    groups = []
    for low, high, key, kind in sorted(events):
        joins = False
        if groups:
            group = groups[-1]
            joins = low <= group["high"]
            if merge_mode == "strict":
                joins = low < group["high"] or low == high == group["low"] == group["high"]
            elif merge_mode == "nontransitive":
                joins = low <= group["initial_high"]
            elif merge_mode == "adjacent_blobs" and kind == "blob" and group["all_blobs"]:
                joins = low <= group["high"] + 1
        if joins:
            group["high"] = max(group["high"], high)
            group["keys"].append(key)
            group["all_blobs"] &= kind == "blob"
        else:
            groups.append({"low": low, "high": high, "initial_high": high, "keys": [key], "all_blobs": kind == "blob"})
    return {key: pitch * index for index, group in enumerate(groups) for key in group["keys"]}


def render(components, background, foreground, *, blob_mode="span", merge_mode="overlap", halo="points", pitch=2, paint_components=None):
    if not components:
        raise ValueError("Expected at least one retained component")
    ys = coordinate_groups(components, 0, blob_mode, merge_mode, pitch)
    xs = coordinate_groups(components, 1, blob_mode, merge_mode, pitch)
    painted = components if paint_components is None else paint_components
    pixels, extent = set(), []
    for item in painted:
        identity = item["id"]
        if item["kind"] == "loop":
            top, bottom = ys[(identity, "low")], ys[(identity, "high")]
            left, right = xs[(identity, "low")], xs[(identity, "high")]
            if top >= bottom or left >= right:
                raise ValueError("Coordinate projection collapses a selected loop")
            pixels |= {(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1) if r in (top, bottom) or c in (left, right)}
            extra = 1 if halo == "all" else 0
            extent += [(top - extra, left - extra), (bottom + extra, right + extra)]
        else:
            y, x = ys[(identity, "point")], xs[(identity, "point")]
            pixels.add((y, x))
            extra = 0 if halo == "none" else 1
            extent += [(y - extra, x - extra), (y + extra, x + extra)]
    top, left, bottom, right = bbox(set(extent))
    return [[foreground if (r, c) in pixels else background for c in range(left, right + 1)] for r in range(top, bottom + 1)]


def solve(grid, frame_policy="all"):
    info = inspect(grid)
    selected = select_components(info["components"], frame_policy)
    return render(selected, info["background"], info["foreground"])


"""Explicit schematic labels; no oracle or candidate imports."""


def picture(height, width, background=0, foreground=1, frames=(), blobs=()):
    grid = [[background] * width for _ in range(height)]
    for top, left, bottom, right in frames:
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                if r in (top, bottom) or c in (left, right):
                    grid[r][c] = foreground
    for cells in blobs:
        for r, c in cells:
            grid[r][c] = foreground
    return grid


def rectangle(top, left, bottom, right):
    return [(r, c) for r in range(top, bottom + 1) for c in range(left, right + 1)]


CASES = [
    {"name": "empty_loop", "input": picture(9, 11, frames=[(2, 2, 6, 8)]), "output": picture(3, 3, frames=[(0, 0, 2, 2)]), "purpose": "True hole detection when a loop contains no other component."},
    {"name": "singleton_blob_only", "input": picture(5, 5, background=2, foreground=4, blobs=[[(2, 2)]]), "output": picture(3, 3, background=2, foreground=4, blobs=[[(1, 1)]]), "purpose": "Singleton retention and complete exposed-point halo; authored blob-only boundary."},
    {"name": "loop_and_singleton", "input": picture(9, 9, foreground=6, frames=[(1, 1, 7, 7)], blobs=[[(4, 4)]]), "output": picture(5, 5, foreground=6, frames=[(0, 0, 4, 4)], blobs=[[(2, 2)]]), "purpose": "One-pixel objects are data, not discarded noise."},
    {"name": "two_disjoint_empty_loops", "input": picture(9, 15, frames=[(2, 1, 6, 5), (2, 9, 6, 13)]), "output": picture(3, 7, frames=[(0, 0, 2, 2), (0, 4, 2, 6)]), "purpose": "Independent loops and shared endpoint groups; authored multi-root boundary."},
    {"name": "nested_empty_loop", "input": picture(11, 13, frames=[(1, 1, 9, 11), (3, 4, 7, 8)]), "output": picture(7, 7, frames=[(0, 0, 6, 6), (2, 2, 4, 4)]), "outermost_output": picture(3, 3, frames=[(0, 0, 2, 2)]), "purpose": "Select loops before compression; dropping inner frames after compression is different."},
    {"name": "transitive_endpoint_overlap_chain", "input": picture(15, 17, frames=[(1, 1, 13, 15)], blobs=[rectangle(3, 3, 4, 6), rectangle(6, 6, 7, 9), rectangle(9, 9, 10, 12)]), "output": picture(9, 5, frames=[(0, 0, 8, 4)], blobs=[[(2, 2)], [(4, 2)], [(6, 2)]]), "purpose": "Three projected spans overlap in a chain, including exact endpoint contact."},
    {"name": "diagonal_singletons", "input": picture(11, 11, frames=[(1, 1, 9, 9)], blobs=[[(4, 4)], [(5, 5)]]), "output": picture(7, 7, frames=[(0, 0, 6, 6)], blobs=[[(2, 2)], [(4, 4)]]), "purpose": "Distinguish4-connectivity from8 and overlap from adjacency."},
    {"name": "exterior_points_above_left_below_right", "input": picture(11, 11, frames=[(3, 3, 7, 7)], blobs=[[(1, 1)], [(9, 9)]]), "output": picture(9, 9, frames=[(3, 3, 5, 5)], blobs=[[(1, 1)], [(7, 7)]]), "purpose": "Expose halos on all four sides without padding the loop itself."},
    {"name": "exterior_point_aligned_to_loop_edge", "input": picture(9, 11, frames=[(2, 4, 6, 8)], blobs=[rectangle(2, 1, 3, 2)]), "output": picture(4, 6, frames=[(1, 3, 3, 5)], blobs=[[(1, 1)]]), "purpose": "Point and loop-endpoint intervals may share a group; the point halo can extend beyond that loop edge."},
]


"""Additional bounded geometry witnesses, derived from the frozen rule."""


def boundary_cases():
    maximum = picture(30, 30, background=7, foreground=2, frames=[(27, 27, 29, 29)], blobs=[[(i, i)] for i in range(13)])
    maximum_expected = picture(30, 30, background=7, foreground=2, frames=[(27, 27, 29, 29)], blobs=[[(2 * i + 1, 2 * i + 1)] for i in range(13)])
    twenty = picture(17, 14, background=9, foreground=0, blobs=[[(r, c)] for r in (1, 4, 7, 10, 13) for c in (1, 4, 7, 10)])
    twenty_expected = picture(11, 9, background=9, foreground=0, blobs=[[(r, c)] for r in (1, 3, 5, 7, 9) for c in (1, 3, 5, 7)])
    grid = picture(25, 25, background=3, foreground=5, frames=[(11, 12, 16, 17)])
    vertices = [(1, 1), (1, 19), (7, 19), (7, 9), (19, 9), (19, 1), (1, 1)]
    for (r0, c0), (r1, c1) in zip(vertices, vertices[1:]):
        for r in range(min(r0, r1), max(r0, r1) + 1):
            for c in range(min(c0, c1), max(c0, c1) + 1):
                grid[r][c] = 5
    expected = picture(7, 7, background=3, foreground=5, frames=[(0, 0, 6, 6), (2, 2, 4, 4)])
    return [
        {"name": "thirty_by_thirty_compact_extent", "input": maximum, "output": maximum_expected, "outermost_output": maximum_expected},
        {"name": "twenty_singleton_components", "input": twenty, "output": twenty_expected, "outermost_output": twenty_expected},
        {"name": "bbox_nesting_without_true_enclosure", "input": grid, "output": expected, "outermost_output": expected},
    ]


def invalid_boundary_cases():
    return [
        ("twenty_one_components", picture(25, 14, blobs=[[(r, c)] for r in (1, 4, 7, 10, 13, 16, 19) for c in (1, 4, 7)])),
        ("thirty_one_output_extent", picture(20, 20, blobs=[[(i, i)] for i in range(1, 16)])),
    ]


# The oracle and nine primary handcases above were frozen from public examples
# before candidate inspection. Embedded copies keep this test task-portable.
import importlib.util
import json
from pathlib import Path

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def candidate():
    spec = importlib.util.spec_from_file_location("independent2d_candidate", TASK_HOME / "generator.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("row", CASES + boundary_cases(), ids=lambda row: row["name"])
@pytest.mark.parametrize("policy", ["all", "outermost"])
def test_independently_labeled_boundaries(candidate, row, policy):
    expected = solve(row["input"], policy)
    if policy == "all":
        assert expected == row["output"]
    elif "outermost_output" in row:
        assert expected == row["outermost_output"]
    assert candidate.solve(row["input"], policy) == expected


@pytest.mark.parametrize("seed", [0, 2**63 - 1])
@pytest.mark.parametrize("policy", ["all", "outermost"])
def test_all_ten_generated_profiles_match_prefrozen_oracle(candidate, seed, policy):
    demos, queries = candidate.lesson_inputs(seed)
    assert len(demos) == 6 and len(queries) == 4
    for grid in demos + queries:
        assert candidate.solve(grid, policy) == solve(grid, policy)


def test_frozen_oracle_and_candidate_match_all_six_public_pairs(candidate):
    raw = TASK_HOME.parents[1] / "shared/data/raw"
    task = json.loads((raw / "arc-agi_evaluation_challenges.json").read_text())["2d0172a1"]
    gold = json.loads((raw / "arc-agi_evaluation_solutions.json").read_text())["2d0172a1"]
    pairs = task["train"] + [{"input": pair["input"], "output": output} for pair, output in zip(task["test"], gold)]
    assert len(pairs) == 6
    for pair in pairs:
        assert solve(pair["input"]) == candidate.solve(pair["input"]) == pair["output"]


@pytest.mark.parametrize("name,grid", invalid_boundary_cases())
def test_declared_component_and_output_limits_reject_overflow(candidate, name, grid):
    with pytest.raises(ValueError):
        candidate.solve(grid)
