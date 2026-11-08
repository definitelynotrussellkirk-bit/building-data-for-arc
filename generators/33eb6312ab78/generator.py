"""Generator for S11_M3 — header count selects a boundary-count object.

The number of blue cells in row 0 is ``n``.  In the body, choose the first
(row-major) object whose number of boundary cells is ``n``.  Crop to that
object's bounding box and keep only its boundary cells in its original color.

The canonical corpus contains both a unique-match case and one deliberate
(or at least executable) two-match case.  The latter is resolved by the
canonical Racket program's ``find-first`` order, so generated lessons schedule
both branches instead of pretending every canonical example is unique.
"""
from __future__ import annotations

from collections import deque
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "33eb6312ab78"
TASK_ID = "33eb6312ab78"
VERSION = "4.0.0"
RULE_HASH = "282a32f858ab"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "A 0-background grid has a contiguous blue header run in row 0 and "
    "exactly three separate, differently colored body components.  Let n be "
    "the number of blue header cells.  Scan body components in row-major order "
    "and take the first object with exactly n boundary cells.  Crop to that "
    "object's full bounding box, erase its interior cells, and preserve its "
    "boundary in the object's original color.  Most generated scenes have "
    "one match; every fourth sample has two matches so the canonical "
    "find-first tie branch is taught explicitly."
)

INVARIANTS = [
    "row 0 contains one contiguous run of 4..10 blue cells and otherwise 0",
    "exactly three 4-connected body components use distinct non-{0,1} colors",
    "one or two body components have boundary-cell count equal to the header count",
    "if two components match, the row-major first match is the selected object",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical-weighted 6..13", "valid": "6..13"},
    "grid_w": {"type": "int", "default": "canonical-weighted 12..18", "valid": "12..18"},
    "n_ones": {"type": "int", "default": "canonical-weighted 4..10", "valid": "4..10"},
}

_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))
_BODY_COLORS = (2, 3, 4, 5, 6, 7, 8, 9)


def _normalize(cells):
    cells = tuple(cells)
    min_r = min(r for r, _ in cells)
    min_c = min(c for _, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _connected(cells) -> bool:
    remaining = set(cells)
    if not remaining:
        return False
    seen = {next(iter(remaining))}
    queue = deque(seen)
    while queue:
        r, c = queue.popleft()
        for dr, dc in _CARD:
            nxt = (r + dr, c + dc)
            if nxt in remaining and nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return len(seen) == len(remaining)


def _boundary_cells(cells):
    cell_set = set(cells)
    return tuple(
        sorted(
            (r, c)
            for r, c in cell_set
            if any((r + dr, c + dc) not in cell_set for dr, dc in _CARD)
        )
    )


def _boundary_count(cells) -> int:
    return len(_boundary_cells(cells))


def _shape_dims(shape) -> tuple[int, int]:
    return (
        1 + max(r for r, _ in shape),
        1 + max(c for _, c in shape),
    )


def _is_solid_rectangle(shape) -> bool:
    h, w = _shape_dims(shape)
    return len(shape) == h * w


def _build_shape_pool():
    """Enumerate compact connected shapes fitting every legal grid boundary.

    A 5x3 window has only 32768 subsets, so doing this once at import is small,
    deterministic, and gives broad shape support without a fragile hand bank.
    """
    cells = [(r, c) for r in range(5) for c in range(3)]
    pools = {n: set() for n in range(4, 11)}
    for mask in range(1, 1 << len(cells)):
        if mask.bit_count() < 4:
            continue
        shape = _normalize(
            cells[index]
            for index in range(len(cells))
            if mask & (1 << index)
        )
        if not _connected(shape):
            continue
        n = _boundary_count(shape)
        if n in pools:
            pools[n].add(shape)
    return {n: tuple(sorted(shapes)) for n, shapes in pools.items()}


_SHAPES = _build_shape_pool()
_ALL_SHAPES = tuple(
    (n, shape) for n, shapes in sorted(_SHAPES.items()) for shape in shapes
)


def _weighted_axis(ctx, label: str, all_values, canonical_values):
    """Draw from the full override domain while weighting canonical scales."""
    if ctx.difficulty == "easy":
        options = tuple(canonical_values) * 5 + tuple(all_values)
    elif ctx.difficulty == "hard":
        options = tuple(canonical_values) * 2 + tuple(all_values)
    else:
        options = tuple(canonical_values) * 3 + tuple(all_values)
    return ctx.draw_choice(label, options)


def _pick(rng, choices):
    choices = tuple(choices)
    if not choices:
        raise ValueError("no feasible compact shape for requested semantic branch")
    return choices[rng.randrange(len(choices))]


def _target_shape(rng, n: int, branch: int):
    shapes = _SHAPES[n]
    if branch == 1:
        # Entire selected object is boundary, but keep a hole in its bounding
        # box.  This teaches the all-boundary branch without producing a solid
        # single-color crop that downstream quality gates rightly flag as an
        # ambiguous label-like output.
        all_boundary = [
            shape
            for shape in shapes
            if len(shape) == n and not _is_solid_rectangle(shape)
        ]
        if all_boundary:
            return _pick(rng, all_boundary)
    # Interior-bearing irregular components teach boundary-vs-whole-object.
    interior = [
        shape
        for shape in shapes
        if len(shape) > n and not _is_solid_rectangle(shape)
    ]
    if interior:
        area = max(map(len, interior)) if branch == 3 else min(map(len, interior))
        return _pick(rng, (shape for shape in interior if len(shape) == area))
    return _pick(rng, (shape for shape in shapes if not _is_solid_rectangle(shape)))


def _pick_same_area_decoy(rng, target, forbidden_counts):
    target_area = len(target)
    candidates = [
        (count, shape)
        for count, shape in _ALL_SHAPES
        if count not in forbidden_counts and len(shape) == target_area
    ]
    if not candidates:
        candidates = [
            (count, shape)
            for count, shape in _ALL_SHAPES
            if count not in forbidden_counts
        ]
    return _pick(rng, candidates)


def _pick_large_decoy(rng, target, forbidden_counts):
    target_area = len(target)
    candidates = [
        (count, shape)
        for count, shape in _ALL_SHAPES
        if count not in forbidden_counts and len(shape) > target_area
    ]
    if not candidates:
        candidates = [
            (count, shape)
            for count, shape in _ALL_SHAPES
            if count not in forbidden_counts
        ]
    max_area = max(len(shape) for _, shape in candidates)
    return _pick(rng, ((count, shape) for count, shape in candidates if len(shape) == max_area))


def _components(grid):
    """Return body components in row-major order, with original coordinates."""
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r0 in range(1, h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color in (0, 1) or (r0, c0) in seen:
                continue
            queue = deque([(r0, c0)])
            seen.add((r0, c0))
            cells = []
            while queue:
                r, c = queue.popleft()
                cells.append((r, c))
                for dr, dc in _CARD:
                    nr, nc = r + dr, c + dc
                    if (
                        1 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append({"color": color, "cells": tuple(sorted(cells))})
    components.sort(key=lambda obj: min(obj["cells"]))
    return components


def _analysis(grid):
    n = sum(value == 1 for value in grid[0])
    components = _components(grid)
    for obj in components:
        obj["boundary"] = _boundary_cells(obj["cells"])
        obj["boundary_count"] = len(obj["boundary"])
        rows = [r for r, _ in obj["cells"]]
        cols = [c for _, c in obj["cells"]]
        obj["bbox"] = (min(rows), min(cols), max(rows), max(cols))
    matches = [obj for obj in components if obj["boundary_count"] == n]
    return n, components, matches


def _crop_boundary(obj):
    r0, c0, r1, c1 = obj["bbox"]
    out = full_grid(r1 - r0 + 1, c1 - c0 + 1, 0)
    for r, c in obj["boundary"]:
        out[r - r0][c - c0] = obj["color"]
    return out


def oracle_output(grid):
    """Python mirror used only by tests/semantic diagnostics; Racket is authority."""
    _, _, matches = _analysis(grid)
    if not matches:
        raise ValueError("no body object matches the header boundary count")
    return _crop_boundary(matches[0])


def observe_overrides(grid) -> dict[str, int]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_ones": sum(value == 1 for value in grid[0]),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid must be rectangular"]
    h = len(grid)
    errors = []
    if not (6 <= h <= 30 and 12 <= w <= 30):
        errors.append(f"grid dimensions {h}x{w} are outside the task envelope")
    if any(value not in (0, 1) for value in grid[0]):
        errors.append("row 0 may contain only background and blue count markers")
    n = sum(value == 1 for value in grid[0])
    if not 4 <= n <= 10:
        errors.append(f"row 0 must contain 4..10 blue cells, got {n}")
    one_cols = [c for c, value in enumerate(grid[0]) if value == 1]
    if one_cols and one_cols != list(range(one_cols[0], one_cols[-1] + 1)):
        errors.append("blue header cells must form one contiguous run")
    if any(grid[r][c] == 1 for r in range(1, h) for c in range(w)):
        errors.append("blue count-marker cells may not appear in the body")

    components = _components(grid)
    if len(components) != 3:
        errors.append(f"expected exactly 3 body components, got {len(components)}")
    colors = [obj["color"] for obj in components]
    if len(colors) != len(set(colors)):
        errors.append("body components must use distinct colors")

    if len(components) == 3:
        counts = [_boundary_count(obj["cells"]) for obj in components]
        matching = [index for index, count in enumerate(counts) if count == n]
        if len(matching) not in (1, 2):
            errors.append(
                f"expected one or two boundary-count matches for n={n}, got {len(matching)}"
            )
        if len(matching) == 2 and matching[0] == matching[1]:
            errors.append("tie branch did not expose two distinct matching components")
        for left in range(len(components)):
            for right in range(left + 1, len(components)):
                a = set(components[left]["cells"])
                b = set(components[right]["cells"])
                if any((r + dr, c + dc) in b for r, c in a for dr, dc in _CARD):
                    errors.append("different body components may not touch cardinally")
                    break
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def _witness_unique(grid) -> bool:
    return len(_analysis(grid)[2]) == 1


def _witness_tie(grid) -> bool:
    return len(_analysis(grid)[2]) == 2


def _witness_interior(grid) -> bool:
    matches = _analysis(grid)[2]
    return bool(matches) and len(matches[0]["cells"]) > matches[0]["boundary_count"]


def _witness_all_boundary(grid) -> bool:
    matches = _analysis(grid)[2]
    return bool(matches) and len(matches[0]["cells"]) == matches[0]["boundary_count"]


def _witness_same_area_decoy(grid) -> bool:
    _, components, matches = _analysis(grid)
    if not matches:
        return False
    target = matches[0]
    return any(
        obj is not target
        and len(obj["cells"]) == len(target["cells"])
        and obj["boundary_count"] != target["boundary_count"]
        for obj in components
    )


def _witness_larger_decoy(grid) -> bool:
    _, components, matches = _analysis(grid)
    return bool(matches) and any(
        len(obj["cells"]) > len(matches[0]["cells"]) for obj in components
    )


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "unique_match": _witness_unique,
    "two_matches_first_wins": _witness_tie,
    "selected_object_has_interior": _witness_interior,
    "selected_object_all_boundary": _witness_all_boundary,
    "same_area_wrong_boundary_decoy": _witness_same_area_decoy,
    "larger_area_decoy": _witness_larger_decoy,
}


def _candidate_output(grid, mode: str):
    n, components, matches = _analysis(grid)
    if not components:
        return None
    if mode == "official":
        chosen = matches[0] if matches else None
        return _crop_boundary(chosen) if chosen else None
    if mode == "last_match":
        chosen = matches[-1] if matches else None
        return _crop_boundary(chosen) if chosen else None
    if mode == "area_equals_header":
        candidates = [obj for obj in components if len(obj["cells"]) == n]
        return _crop_boundary(candidates[0]) if candidates else None
    if mode == "largest_area":
        return _crop_boundary(max(components, key=lambda obj: len(obj["cells"])))
    if mode == "smallest_area":
        return _crop_boundary(min(components, key=lambda obj: len(obj["cells"])))
    if mode == "leftmost":
        return _crop_boundary(min(components, key=lambda obj: min(c for _, c in obj["cells"])))
    if mode == "rightmost":
        return _crop_boundary(max(components, key=lambda obj: max(c for _, c in obj["cells"])))
    if mode == "lowest_color":
        return _crop_boundary(min(components, key=lambda obj: obj["color"]))
    if mode == "highest_color":
        return _crop_boundary(max(components, key=lambda obj: obj["color"]))
    if mode == "whole_object":
        chosen = matches[0] if matches else None
        if chosen is None:
            return None
        r0, c0, r1, c1 = chosen["bbox"]
        out = full_grid(r1 - r0 + 1, c1 - c0 + 1, 0)
        for r, c in chosen["cells"]:
            out[r - r0][c - c0] = chosen["color"]
        return out
    raise ValueError(mode)


def lesson_identifiable(demos, query) -> list[str]:
    rivals = (
        "last_match",
        "area_equals_header",
        "largest_area",
        "smallest_area",
        "leftmost",
        "rightmost",
        "lowest_color",
        "highest_color",
        "whole_object",
    )
    official_query = _candidate_output(query["input"], "official")
    errors = []
    for rival in rivals:
        if all(_candidate_output(demo["input"], rival) == demo["output"] for demo in demos):
            rival_query = _candidate_output(query["input"], rival)
            if rival_query != official_query:
                errors.append(f"demos do not rule out rival operation {rival}")
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis: {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = _weighted_axis(ctx, "grid_h", range(6, 14), (6, 7))
    w = _weighted_axis(ctx, "grid_w", range(12, 19), (12, 13))
    n = _weighted_axis(ctx, "n_ones", range(4, 11), (4, 8, 10))

    shape_rng = ctx.draw_rng("shapes")
    layout_rng = ctx.draw_rng("layout")
    palette_rng = ctx.draw_rng("palette")
    branch = sample_index % 4
    target = _target_shape(shape_rng, n, branch)

    if branch == 0:
        # Canonical tie branch.  The selected target occupies the earliest
        # row-major slot; a second n-boundary object follows it.
        smaller_matches = [shape for shape in _SHAPES[n] if len(shape) < len(target)]
        twin = _pick(shape_rng, smaller_matches)
        other_count, other = _pick_large_decoy(shape_rng, target, {n})
        del other_count
        slot_shapes = [target, twin, other]
        target_slot = 0
        force_top_aligned = True
    else:
        count_a, decoy_a = _pick_same_area_decoy(shape_rng, target, {n})
        count_b, decoy_b = _pick_large_decoy(shape_rng, target, {n, count_a})
        del count_b
        target_slot = branch % 3
        slot_shapes = [None, None, None]
        slot_shapes[target_slot] = target
        remaining = [slot for slot in range(3) if slot != target_slot]
        slot_shapes[remaining[0]] = decoy_a
        slot_shapes[remaining[1]] = decoy_b
        force_top_aligned = False

    colors = list(_BODY_COLORS)
    palette_rng.shuffle(colors)
    colors = colors[:3]
    if branch == 0:
        # The tie lesson alone rules out both color shortcuts: the selected
        # first match receives the middle of three colors, never the min/max.
        ordered = sorted(colors)
        assigned = [None, None, None]
        assigned[target_slot] = ordered[1]
        other_slots = [slot for slot in range(3) if slot != target_slot]
        assigned[other_slots[0]] = ordered[0]
        assigned[other_slots[1]] = ordered[2]
        colors = assigned
    g = full_grid(h, w, 0)

    header_start = layout_rng.randint(0, w - n)
    for c in range(header_start, header_start + n):
        g[0][c] = 1

    # Three width-3 slots plus two one-column separators use 11 columns.
    left_margin = layout_rng.randint(0, w - 11)
    slot_starts = (left_margin, left_margin + 4, left_margin + 8)
    for slot, (shape, color) in enumerate(zip(slot_shapes, colors)):
        sh, sw = _shape_dims(shape)
        if force_top_aligned:
            row0 = 1
        else:
            row0 = 1 + layout_rng.randint(0, (h - 1) - sh)
        col0 = slot_starts[slot] + layout_rng.randint(0, 3 - sw)
        for dr, dc in shape:
            g[row0 + dr][col0 + dc] = color

    errors = self_check(g)
    if errors:
        raise AssertionError(f"internal generator invariant failure: {errors}")
    return g
