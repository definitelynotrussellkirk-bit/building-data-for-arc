"""Episode-level halo-component family for 1ba9f2a08016.

Step A always performs the canonical operation: keep red(2) seeds and paint
blank orthogonal neighbours magenta(6).  For the two nondefault settings, the
input-dependent intermediate is the set of 4-connected components in the
red+magenta mask.  Step B selects the largest or smallest component and
recolors only that component's magenta cells yellow(4).  ``plain`` remains the
exact selected canonical program.
"""
from __future__ import annotations

from collections import deque
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import canonical_path, find_root

TASK_ID = "1ba9f2a08016"
COMPONENT_POLICIES = ("plain", "highlight_largest", "highlight_smallest")
DEFAULT_POLICY = "plain"
ROOT = find_root(__file__)
_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or seed < 0:
        raise ValueError("seed must be a nonnegative exact integer")


def _validate_policy(component_policy: str) -> None:
    if type(component_policy) is not str or component_policy not in COMPONENT_POLICIES:
        raise ValueError(f"component_policy must be one of {COMPONENT_POLICIES}")


def _validate_counts(demos: int, queries: int) -> None:
    if type(demos) is not int or not 2 <= demos <= 6:
        raise ValueError("demos must be an exact integer in 2..6")
    if type(queries) is not int or queries != 4:
        raise ValueError("queries must be the exact integer 4")


def canonical_source(*, root: Path = ROOT) -> str:
    sources: list[str] = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if type(source) is not str or not source.strip():
                    raise ValueError("canonical record has no Racket program")
                sources.append(source)
    if not sources or len(set(sources)) != 1:
        raise ValueError("expected one unique canonical Racket program")
    return sources[0]


_HALO_EXPR = """(for/fold ([out g]) ([p (in-list (find-color g 2))])
    (for/fold ([acc out]) ([d (in-list cardinal-deltas)])
      (let ((rr (+ (first p) (first d)))
            (cc (+ (second p) (second d))))
        (if (and (in-bounds? rr cc (rows g) (cols g)) (= (at acc rr cc) 0))
            (set-cell acc rr cc 6)
            acc))))"""


def _highlight_program(*, largest: bool) -> str:
    order = ">" if largest else "<"
    return f"""(rule!
  (let* ((halo
           {_HALO_EXPR})
         (mask (grid-from-fn (rows halo) (cols halo)
                 (lambda (r c)
                   (if (or (= (at halo r c) 2) (= (at halo r c) 6)) 1 0))))
         (objs (sort (objects mask 0)
                     (lambda (a b)
                       (if (= (obj-size a) (obj-size b))
                           (if (= (obj-r1 a) (obj-r1 b))
                               (< (obj-c1 a) (obj-c1 b))
                               (< (obj-r1 a) (obj-r1 b)))
                           ({order} (obj-size a) (obj-size b))))))
         (target (first objs)))
    (for/fold ([out halo]) ([p (in-list (obj-cells target))])
      (if (= (at out (first p) (second p)) 6)
          (set-cell out (first p) (second p) 4)
          out))))"""


def program_for(component_policy: str = DEFAULT_POLICY, *, root: Path = ROOT) -> str:
    _validate_policy(component_policy)
    if component_policy == DEFAULT_POLICY:
        return canonical_source(root=root)
    return _highlight_program(largest=component_policy == "highlight_largest")


def _rng(seed: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|halo-components-v2|{seed}|{label}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def canonical_halo(grid: list[list[int]]) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    out = [row[:] for row in grid]
    seeds = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    for r, c in seeds:
        for dr, dc in _CARDINALS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < len(out) and 0 <= cc < width and out[rr][cc] == 0:
                out[rr][cc] = 6
    return out


def _mask_components(halo: list[list[int]]) -> list[dict[str, Any]]:
    h, w = len(halo), len(halo[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if halo[r][c] in (2, 6)}
    result: list[dict[str, Any]] = []
    while unseen:
        start = min(unseen)
        queue = deque([start])
        unseen.remove(start)
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in _CARDINALS:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    queue.append(nxt)
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        result.append({
            "cells": sorted(cells),
            "magenta_cells": sorted((r, c) for r, c in cells if halo[r][c] == 6),
            "red_cells": sorted((r, c) for r, c in cells if halo[r][c] == 2),
            "size": len(cells),
            "r1": min(rows),
            "c1": min(cols),
            "r2": max(rows),
            "c2": max(cols),
        })
    return result


def scene_facts(grid: list[list[int]]) -> dict[str, Any]:
    halo = canonical_halo(grid)
    components = _mask_components(halo)
    return {"halo": halo, "components": components}


def select_intermediate(facts: dict[str, Any], component_policy: str) -> dict[str, Any]:
    _validate_policy(component_policy)
    if component_policy == "plain":
        raise ValueError("plain has no component-selection second stage")
    components = list(facts["components"])
    reverse = component_policy == "highlight_largest"
    components.sort(
        key=lambda component: (
            -component["size"] if reverse else component["size"],
            component["r1"],
            component["c1"],
        )
    )
    if not components:
        raise ValueError("scene has no red+halo component")
    return dict(components[0])


def python_mirror(grid: list[list[int]], *, component_policy: str = DEFAULT_POLICY) -> list[list[int]]:
    _validate_policy(component_policy)
    facts = scene_facts(grid)
    out = [row[:] for row in facts["halo"]]
    if component_policy == "plain":
        return out
    selected = select_intermediate(facts, component_policy)
    for r, c in selected["magenta_cells"]:
        out[r][c] = 4
    return out


def _scene_dimensions(index: int, total: int) -> tuple[int, int, bool]:
    if index == total - 1:
        return 30, 30, True
    schedule = ((12, 14), (13, 16), (15, 18), (17, 20), (19, 22), (21, 24), (23, 26), (25, 28), (14, 21))
    h, w = schedule[index % len(schedule)]
    return h, w, False


def _line_cells(length: int, orientation: str, row: int, col: int) -> list[tuple[int, int]]:
    if orientation == "h":
        return [(row, col + offset) for offset in range(length)]
    return [(row + offset, col) for offset in range(length)]


def _potential_halo(cells: list[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    footprint = set(cells)
    for r, c in cells:
        for dr, dc in _CARDINALS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < h and 0 <= cc < w:
                footprint.add((rr, cc))
    return footprint


def _separate(footprint: set[tuple[int, int]], existing: list[set[tuple[int, int]]]) -> bool:
    for other in existing:
        if any(abs(r - rr) + abs(c - cc) <= 1 for r, c in footprint for rr, cc in other):
            return False
    return True


def _interior_line_candidates(length: int, h: int, w: int) -> list[list[tuple[int, int]]]:
    """Enumerate open line placements with a one-cell in-bounds halo."""

    candidates: list[list[tuple[int, int]]] = []
    for row in range(1, h - 1):
        for col in range(1, w - length):
            candidates.append(_line_cells(length, "h", row, col))
    for row in range(1, h - length):
        for col in range(1, w - 1):
            candidates.append(_line_cells(length, "v", row, col))
    return candidates


def _corner_block(
    rows: int,
    cols: int,
    h: int,
    w: int,
    corner: str,
) -> list[tuple[int, int]]:
    if corner == "top_left":
        r0, c0 = 0, 0
    elif corner == "top_right":
        r0, c0 = 0, w - cols
    elif corner == "bottom_left":
        r0, c0 = h - rows, 0
    elif corner == "bottom_right":
        r0, c0 = h - rows, w - cols
    else:
        raise ValueError(f"unknown corner {corner!r}")
    return [(r, c) for r in range(r0, r0 + rows) for c in range(c0, c0 + cols)]


def _profile(seed: int, index: int, *, stress: bool) -> tuple[tuple[int, int], int, int]:
    """Return a compact block and two open-line lengths.

    Red-seed counts deliberately cross post-halo component sizes: the compact
    block has the most red cells but becomes smallest after all but one halo
    cell are blocked; the short line has the fewest red cells but is middle;
    and the long line is largest without having the most red seeds.
    """

    if stress:
        return (3, 6), 10, 14
    profiles = (
        ((2, 2), 2, 3),
        ((2, 3), 3, 4),
        ((2, 4), 4, 5),
    )
    return profiles[(seed + index) % len(profiles)]


def _build_scene(seed: int, index: int, total: int) -> list[list[int]]:
    h, w, stress = _scene_dimensions(index, total)
    rng = _rng(seed, f"scene:{index}:{total}")
    block_shape, short_length, long_length = _profile(seed, index, stress=stress)
    corners = ("top_left", "top_right", "bottom_right", "bottom_left")
    corner = corners[(seed + 3 * index) % len(corners)]
    if (seed + index) % 2:
        block_shape = (block_shape[1], block_shape[0])

    # Component A has the most red seeds, but only one exposed halo cell.  It
    # therefore becomes the smallest red+magenta component after Step A.
    block = _corner_block(*block_shape, h, w, corner)
    block_footprint = _potential_halo(block, h, w)
    exposed = sorted(block_footprint - set(block))
    rng.shuffle(exposed)
    if not exposed:
        raise RuntimeError("corner block unexpectedly has no exposed halo")
    keep_blank = exposed[0]

    # Components B/C are open interior lines.  Their post-halo sizes are
    # 3*n+2, while A's post-halo size is red_count+1.  This creates the strict
    # ordering A < B < C even though red counts order B < C < A.
    occupied = [block_footprint]
    chosen_lines: list[tuple[int, list[tuple[int, int]], set[tuple[int, int]]]] = []
    for length in (short_length, long_length):
        candidates = _interior_line_candidates(length, h, w)
        rng.shuffle(candidates)
        for cells in candidates:
            footprint = _potential_halo(cells, h, w)
            if _separate(footprint, occupied):
                chosen_lines.append((length, cells, footprint))
                occupied.append(footprint)
                break
        else:
            raise RuntimeError("could not place separated open-line halo component")

    grid = [[0 for _ in range(w)] for _ in range(h)]
    for r, c in block:
        grid[r][c] = 2
    for r, c in exposed:
        if (r, c) != keep_blank:
            grid[r][c] = 8
    for _, cells, _ in chosen_lines:
        for r, c in cells:
            grid[r][c] = 2

    occupied_footprint = set().union(*occupied)
    # Remote non-red objects are no-overwrite controls and force the component
    # stage to use the red+magenta mask rather than all nonzero cells.
    remote = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 0
        and all(abs(r - rr) + abs(c - cc) >= 2 for rr, cc in occupied_footprint)
    ]
    rng.shuffle(remote)
    decoy_count = 6 if stress else 2 + (index % 3)
    if len(remote) < decoy_count:
        raise RuntimeError("not enough remote cells for no-overwrite controls")
    for offset, (r, c) in enumerate(remote[:decoy_count]):
        grid[r][c] = (1, 3, 7, 9)[(index + offset) % 4]

    facts = scene_facts(grid)
    components = facts["components"]
    if len(components) != 3:
        raise RuntimeError("constructed scene does not have three halo components")
    sizes = [component["size"] for component in components]
    red_counts = [len(component["red_cells"]) for component in components]
    largest = select_intermediate(facts, "highlight_largest")
    smallest = select_intermediate(facts, "highlight_smallest")
    if len(set(sizes)) != 3 or any(not component["magenta_cells"] for component in components):
        raise RuntimeError("constructed halo components are not distinct and active")
    if len(largest["red_cells"]) == max(red_counts):
        raise RuntimeError("largest post-halo component leaks through red-seed count")
    if len(smallest["red_cells"]) == min(red_counts):
        raise RuntimeError("smallest post-halo component leaks through red-seed count")
    return grid


def generate_claims(
    seed: int,
    component_policy: str = DEFAULT_POLICY,
    demos: int = 2,
    queries: int = 4,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    _validate_seed(seed)
    _validate_policy(component_policy)
    _validate_counts(demos, queries)
    total = demos + queries
    pairs = []
    for index in range(total):
        grid = _build_scene(seed, index, total)
        pairs.append({
            "input": grid,
            "output": python_mirror(grid, component_policy=component_policy),
        })
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program_for(component_policy, root=root),
    }
