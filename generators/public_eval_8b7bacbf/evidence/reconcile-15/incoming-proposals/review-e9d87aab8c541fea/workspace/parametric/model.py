"""Route-colored pocket filling for public parent 8b7bacbf.

A singleton payload color embedded in a carrier path propagates through that
carrier's 8-connected route and fills every uniformly bounded background pocket
it reaches.  The canonical branch may bridge carrier components across one
intervening cell, which is how routes continue through crossings.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Iterable

from puzzle_generators.base import gen_ctx

TASK = "public_eval_8b7bacbf"
VERSION = "1.0.0"
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
ALL8 = CARDINAL + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def validate(grid: list[list[int]]) -> None:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or any(type(row) is not list for row in grid)
        or not grid
        or not 1 <= len(grid[0]) <= 30
        or any(len(row) != len(grid[0]) for row in grid)
        or any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row)
    ):
        raise ValueError("expected a rectangular 1..30 exact-integer ARC color grid")


def _background(grid: list[list[int]]) -> int:
    counts = Counter(value for row in grid for value in row)
    return min(counts, key=lambda value: (-counts[value], value))


def _regions(grid: list[list[int]], color: int, deltas=CARDINAL) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    answer: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            cells: list[tuple[int, int]] = []
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in deltas:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            answer.append(cells)
    return answer


def _components8(grid: list[list[int]], background: int) -> list[dict[str, object]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    answer: list[dict[str, object]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == background or (r, c) in seen:
                continue
            color = grid[r][c]
            cells: list[tuple[int, int]] = []
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ALL8:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            answer.append({"color": color, "cells": cells})
    return answer


def _pockets(grid: list[list[int]], background: int) -> list[dict[str, object]]:
    h, w = len(grid), len(grid[0])
    answer: list[dict[str, object]] = []
    for cells in _regions(grid, background, CARDINAL):
        boundary: set[tuple[int, int]] = set()
        for r, c in cells:
            for dr, dc in CARDINAL:
                nr, nc = r + dr, c + dc
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] != background:
                    boundary.add((nr, nc))
        colors = {grid[r][c] for r, c in boundary}
        # The area guard excludes a dense scene's exterior while preserving
        # border-sealed pockets whose missing side is the canvas edge.
        if len(cells) <= (h * w) // 3 and len(boundary) >= 3 and len(colors) == 1:
            answer.append({"cells": cells, "boundary": sorted(boundary), "color": next(iter(colors))})
    return answer


def _near(left: Iterable[tuple[int, int]], right: Iterable[tuple[int, int]], limit: int) -> bool:
    right_cells = tuple(right)
    return any(
        max(abs(r1 - r2), abs(c1 - c2)) <= limit
        for r1, c1 in left
        for r2, c2 in right_cells
    )


def analyze(grid: list[list[int]], bridge_short_gaps: bool = True) -> dict[str, object]:
    validate(grid)
    if type(bridge_short_gaps) is not bool:
        raise ValueError("bridge_short_gaps must be Boolean")
    h, w = len(grid), len(grid[0])
    background = _background(grid)
    pockets = _pockets(grid, background)
    components = _components8(grid, background)
    position_component = {
        position: index
        for index, component in enumerate(components)
        for position in component["cells"]
    }

    sources: list[dict[str, object]] = []
    for index, component in enumerate(components):
        cells = component["cells"]
        if len(cells) != 1:
            continue
        r, c = cells[0]
        payload = component["color"]
        support: Counter[int] = Counter()
        for dr, dc in ALL8:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                value = grid[nr][nc]
                if value not in (background, payload):
                    support[value] += 1
        if not support:
            continue
        carrier, count = min(support.items(), key=lambda pair: (-pair[1], pair[0]))
        if count < 3:
            continue
        starts = sorted(
            {
                position_component[(r + dr, c + dc)]
                for dr, dc in ALL8
                if (r + dr, c + dc) in position_component
                and components[position_component[(r + dr, c + dc)]]["color"] == carrier
            }
        )
        if starts:
            sources.append(
                {
                    "component": index,
                    "position": (r, c),
                    "payload": payload,
                    "carrier": carrier,
                    "start_components": starts,
                }
            )

    component_pockets: list[set[int]] = [set() for _ in components]
    pocket_components: list[set[int]] = [set() for _ in pockets]
    for component_index, component in enumerate(components):
        for pocket_index, pocket in enumerate(pockets):
            if _near(component["cells"], pocket["boundary"], 1):
                component_pockets[component_index].add(pocket_index)
                pocket_components[pocket_index].add(component_index)

    bridge_components: list[set[int]] = [set() for _ in components]
    if bridge_short_gaps:
        for left in range(len(components)):
            for right in range(left + 1, len(components)):
                if (
                    components[left]["color"] == components[right]["color"]
                    and _near(components[left]["cells"], components[right]["cells"], 2)
                ):
                    bridge_components[left].add(right)
                    bridge_components[right].add(left)

    assignments: dict[int, int] = {}
    source_reach: list[dict[str, object]] = []
    for source in sources:
        carrier = source["carrier"]
        queue = deque(("component", index) for index in source["start_components"])
        seen = set(queue)
        reached: list[int] = []
        while queue:
            kind, index = queue.popleft()
            if kind == "component":
                for pocket_index in sorted(component_pockets[index]):
                    node = ("pocket", pocket_index)
                    if node not in seen:
                        seen.add(node)
                        queue.append(node)
                for component_index in sorted(bridge_components[index]):
                    if components[component_index]["color"] == carrier:
                        node = ("component", component_index)
                        if node not in seen:
                            seen.add(node)
                            queue.append(node)
            else:
                reached.append(index)
                for component_index in sorted(pocket_components[index]):
                    if components[component_index]["color"] == carrier:
                        node = ("component", component_index)
                        if node not in seen:
                            seen.add(node)
                            queue.append(node)
        for pocket_index in reached:
            assignments.setdefault(pocket_index, source["payload"])
        source_reach.append({**source, "reached_pockets": reached})

    return {
        "background": background,
        "pockets": pockets,
        "components": components,
        "sources": source_reach,
        "assignments": assignments,
    }


def solve(grid: list[list[int]], bridge_short_gaps: bool = True) -> list[list[int]]:
    state = analyze(grid, bridge_short_gaps=bridge_short_gaps)
    out = [row[:] for row in grid]
    for pocket_index, payload in state["assignments"].items():
        for r, c in state["pockets"][pocket_index]["cells"]:
            out[r][c] = payload
    return out


def _frame(grid: list[list[int]], top: int, left: int, height: int, width: int, color: int) -> int:
    bottom, right = top + height - 1, left + width - 1
    for c in range(left, right + 1):
        grid[top][c] = grid[bottom][c] = color
    for r in range(top, bottom + 1):
        grid[r][left] = grid[r][right] = color
    return left + (width - 1) // 2


def _chain(
    grid: list[list[int]],
    *,
    top: int,
    lefts: tuple[int, ...],
    frame_height: int,
    frame_width: int,
    carrier: int,
    payload: int,
    crossing: int,
    source_at_right: bool,
) -> None:
    bottoms = top + frame_height - 1
    centers = [_frame(grid, top, left, frame_height, frame_width, carrier) for left in lefts]
    route_row = bottoms + 2
    for center in centers:
        for r in range(bottoms, route_row + 1):
            grid[r][center] = carrier
    for left_center, right_center in zip(centers, centers[1:]):
        for c in range(left_center, right_center + 1):
            grid[route_row][c] = carrier
        gap = (left_center + right_center) // 2
        grid[route_row][gap] = crossing
    source_col = centers[-1] if source_at_right else centers[0]
    source_row = route_row + 2
    grid[source_row][source_col] = payload
    for r, c in (
        (source_row - 1, source_col),
        (source_row + 1, source_col),
        (source_row, source_col - 1),
        (source_row, source_col + 1),
    ):
        grid[r][c] = carrier


def sample_input(seed: int, index: int, *, stress: bool = False) -> list[list[int]]:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an exact integer in 0..2**63-1")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")
    ctx = gen_ctx(seed=seed, sample_index=index, version=VERSION, task_id=TASK)
    is_stress = stress or index == 103
    if is_stress:
        h = w = 30
        bg, carrier1, payload1, crossing1, carrier2, payload2, crossing2 = ctx.draw_distinct_colors(
            "scene-colors", n=7
        )
        grid = [[bg] * w for _ in range(h)]
        _chain(
            grid,
            top=2,
            lefts=(1, 10, 19),
            frame_height=5,
            frame_width=6,
            carrier=carrier1,
            payload=payload1,
            crossing=crossing1,
            source_at_right=False,
        )
        _chain(
            grid,
            top=17,
            lefts=(1, 10, 19),
            frame_height=5,
            frame_width=6,
            carrier=carrier2,
            payload=payload2,
            crossing=crossing2,
            source_at_right=True,
        )
    else:
        h = ctx.draw_int("height", 13, 18)
        w = ctx.draw_int("width", 24, 30)
        bg, carrier, payload, crossing = ctx.draw_distinct_colors("scene-colors", n=4)
        grid = [[bg] * w for _ in range(h)]
        shift = (w - 24) // 2
        _chain(
            grid,
            top=1,
            lefts=(1 + shift, 9 + shift, 17 + shift),
            frame_height=4,
            frame_width=5,
            carrier=carrier,
            payload=payload,
            crossing=crossing,
            source_at_right=bool(index % 2),
        )
    state = analyze(grid, bridge_short_gaps=True)
    if not state["sources"] or len(state["assignments"]) < 2:
        raise RuntimeError("constructed routed-pocket grammar is ambiguous")
    if solve(grid, True) == solve(grid, False):
        raise RuntimeError("constructed scene does not identify bridge policy")
    return grid
