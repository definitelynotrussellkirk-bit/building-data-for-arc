"""
Shared grid primitives — single source of truth for low-level grid operations.

Everything else (transforms, features, views) imports from here.
No duplication of connected-component, enclosure, flood-fill logic.
"""

import numpy as np
from collections import Counter


# ============================================================
# Neighbor utilities
# ============================================================

def neighbors_4(r, c, h, w):
    """Yield 4-connected neighbor coords in bounds."""
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < h and 0 <= nc < w:
            yield nr, nc


def neighbors_8(r, c, h, w):
    """Yield 8-connected neighbor coords in bounds."""
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w:
                yield nr, nc


# ============================================================
# Grid basics
# ============================================================

def grid_shape(grid):
    """(height, width) of grid."""
    g = np.array(grid)
    return g.shape


def grid_colors(grid, bg=0):
    """Set of non-background colors."""
    g = np.array(grid)
    return set(int(v) for v in np.unique(g) if v != bg)


def color_mask(grid, color):
    """Boolean mask where grid == color."""
    return np.array(grid) == color


def bounding_box(cells):
    """(min_r, min_c, max_r, max_c) from a list of (r, c) tuples."""
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


# ============================================================
# Connected components
# ============================================================

def find_objects(grid, bg=0, connectivity=4):
    """Find connected components per color (analysis-side semantics).

    Contract — see docs/OWNERSHIP.md row "Connected components — Python
    (analysis side)":
      - Univalued: each component is a single color (different colors
        never merge, even when adjacent).
      - bg defaults to 0 (NOT inferred); pass `bg=...` to override.
      - Connectivity: 4 (default) or 8.
      - Return: list of dicts
            {color: int, size: int, cells: [(r, c), ...],
             bbox: (r1, c1, r2, c2), center_r: float, center_c: float}.

    NOT the same as `puzzle_generators.helpers.objects.find_objects`,
    which is multicolor by default, infers bg from mode, and returns
    a typed `Object` (set of (color, (r, c)) tuples). When you need
    the generator-typed shape, use that one and don't try to wrap
    this one — the bg-inference difference matters.
    """
    g = np.array(grid)
    h, w = g.shape
    visited = np.zeros_like(g, dtype=bool)
    neighbor_fn = neighbors_4 if connectivity == 4 else neighbors_8
    objects = []

    for r in range(h):
        for c in range(w):
            if visited[r, c] or g[r, c] == bg:
                continue
            color = int(g[r, c])
            cells = []
            stack = [(r, c)]
            visited[r, c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for nr, nc in neighbor_fn(cr, cc, h, w):
                    if not visited[nr, nc] and g[nr, nc] == color:
                        visited[nr, nc] = True
                        stack.append((nr, nc))

            r1, c1, r2, c2 = bounding_box(cells)
            objects.append({
                "color": color,
                "size": len(cells),
                "cells": cells,
                "bbox": (r1, c1, r2, c2),
                "center_r": (r1 + r2) / 2,
                "center_c": (c1 + c2) / 2,
            })

    return objects


def find_objects_multicolor(grid, bg=0, connectivity=4):
    """Find connected components across colors (any non-bg neighbor connects)."""
    g = np.array(grid)
    h, w = g.shape
    visited = np.zeros_like(g, dtype=bool)
    neighbor_fn = neighbors_4 if connectivity == 4 else neighbors_8
    objects = []

    for r in range(h):
        for c in range(w):
            if visited[r, c] or g[r, c] == bg:
                continue
            cells = []
            stack = [(r, c)]
            visited[r, c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for nr, nc in neighbor_fn(cr, cc, h, w):
                    if not visited[nr, nc] and g[nr, nc] != bg:
                        visited[nr, nc] = True
                        stack.append((nr, nc))

            colors = set(int(g[r2, c2]) for r2, c2 in cells)
            r1, c1, r2, c2 = bounding_box(cells)
            objects.append({
                "colors": colors,
                "size": len(cells),
                "cells": cells,
                "bbox": (r1, c1, r2, c2),
            })

    return objects


# ============================================================
# Enclosure detection
# ============================================================

def find_enclosed(grid, bg=0):
    """Return boolean mask of enclosed background cells (not reachable from grid edge)."""
    g = np.array(grid)
    h, w = g.shape
    reachable = np.zeros_like(g, dtype=bool)
    queue = []

    for r in range(h):
        for c in range(w):
            if (r == 0 or r == h - 1 or c == 0 or c == w - 1) and g[r, c] == bg:
                reachable[r, c] = True
                queue.append((r, c))

    while queue:
        cr, cc = queue.pop(0)
        for nr, nc in neighbors_4(cr, cc, h, w):
            if not reachable[nr, nc] and g[nr, nc] == bg:
                reachable[nr, nc] = True
                queue.append((nr, nc))

    return (g == bg) & ~reachable


# ============================================================
# Flood fill
# ============================================================

def flood_fill_mask(grid, seed_r, seed_c, connectivity=4):
    """Return boolean mask of cells reachable from seed (same color, connected)."""
    g = np.array(grid)
    h, w = g.shape
    color = g[seed_r, seed_c]
    mask = np.zeros_like(g, dtype=bool)
    neighbor_fn = neighbors_4 if connectivity == 4 else neighbors_8

    queue = [(seed_r, seed_c)]
    mask[seed_r, seed_c] = True
    while queue:
        cr, cc = queue.pop(0)
        for nr, nc in neighbor_fn(cr, cc, h, w):
            if not mask[nr, nc] and g[nr, nc] == color:
                mask[nr, nc] = True
                queue.append((nr, nc))

    return mask


def flood_fill_any(grid, seed_r, seed_c, bg=0, connectivity=4):
    """Return mask of cells reachable from seed through any non-bg cells."""
    g = np.array(grid)
    h, w = g.shape
    mask = np.zeros_like(g, dtype=bool)
    neighbor_fn = neighbors_4 if connectivity == 4 else neighbors_8

    queue = [(seed_r, seed_c)]
    mask[seed_r, seed_c] = True
    while queue:
        cr, cc = queue.pop(0)
        for nr, nc in neighbor_fn(cr, cc, h, w):
            if not mask[nr, nc] and g[nr, nc] != bg:
                mask[nr, nc] = True
                queue.append((nr, nc))

    return mask


# ============================================================
# Mask operations
# ============================================================

def where_color(grid, color):
    """Mask of cells with the given color."""
    return np.array(grid) == color


def where_not_color(grid, color):
    """Mask of cells NOT with the given color."""
    return np.array(grid) != color


def where_border(grid):
    """Mask of cells on the grid border."""
    g = np.array(grid)
    h, w = g.shape
    mask = np.zeros((h, w), dtype=bool)
    mask[0, :] = True
    mask[-1, :] = True
    mask[:, 0] = True
    mask[:, -1] = True
    return mask


def where_adjacent_to(grid, color, connectivity=4):
    """Mask of cells adjacent to at least one cell of `color`."""
    g = np.array(grid)
    h, w = g.shape
    target = g == color
    mask = np.zeros_like(g, dtype=bool)
    neighbor_fn = neighbors_4 if connectivity == 4 else neighbors_8

    for r in range(h):
        for c in range(w):
            if target[r, c]:
                continue
            for nr, nc in neighbor_fn(r, c, h, w):
                if target[nr, nc]:
                    mask[r, c] = True
                    break
    return mask


def where_enclosed(grid, bg=0):
    """Mask of enclosed background cells."""
    return find_enclosed(grid, bg)


def where_neighbor_count(grid, color, count, connectivity=4):
    """Mask of cells with exactly `count` neighbors of `color`."""
    g = np.array(grid)
    h, w = g.shape
    neighbor_fn = neighbors_4 if connectivity == 4 else neighbors_8
    mask = np.zeros((h, w), dtype=bool)

    for r in range(h):
        for c in range(w):
            n = sum(1 for nr, nc in neighbor_fn(r, c, h, w) if g[nr, nc] == color)
            if n == count:
                mask[r, c] = True
    return mask


def dilate_mask(mask, amount=1, connectivity=4):
    """Grow mask by `amount` cells."""
    m = np.array(mask, dtype=bool)
    h, w = m.shape
    neighbor_fn = neighbors_4 if connectivity == 4 else neighbors_8
    for _ in range(amount):
        new_m = m.copy()
        for r in range(h):
            for c in range(w):
                if not m[r, c]:
                    for nr, nc in neighbor_fn(r, c, h, w):
                        if m[nr, nc]:
                            new_m[r, c] = True
                            break
        m = new_m
    return m


def erode_mask(mask, amount=1, connectivity=4):
    """Shrink mask by `amount` cells."""
    m = np.array(mask, dtype=bool)
    h, w = m.shape
    neighbor_fn = neighbors_4 if connectivity == 4 else neighbors_8
    for _ in range(amount):
        new_m = m.copy()
        for r in range(h):
            for c in range(w):
                if m[r, c]:
                    for nr, nc in neighbor_fn(r, c, h, w):
                        if not m[nr, nc]:
                            new_m[r, c] = False
                            break
        m = new_m
    return m


# ============================================================
# Spatial analysis
# ============================================================

def object_properties(obj):
    """Compute properties of an object dict.

    Returns dict with: size, bbox, width, height, aspect_ratio,
    is_rectangular, is_line, is_dot, density
    """
    r1, c1, r2, c2 = obj["bbox"]
    bw = c2 - c1 + 1
    bh = r2 - r1 + 1
    area = bw * bh
    size = obj["size"]

    return {
        "size": size,
        "bbox": obj["bbox"],
        "width": bw,
        "height": bh,
        "aspect_ratio": round(bw / bh, 2) if bh > 0 else 0,
        "is_rectangular": size == area,
        "is_line": bw == 1 or bh == 1,
        "is_dot": size == 1,
        "density": round(size / area, 2) if area > 0 else 0,
    }


def spatial_relation(obj1, obj2):
    """Describe spatial relationship between two objects."""
    r1_1, c1_1, r2_1, c2_1 = obj1["bbox"]
    r1_2, c1_2, r2_2, c2_2 = obj2["bbox"]

    relations = []

    if r2_1 < r1_2:
        relations.append("above")
    elif r1_1 > r2_2:
        relations.append("below")
    if c2_1 < c1_2:
        relations.append("left_of")
    elif c1_1 > c2_2:
        relations.append("right_of")

    # Check adjacency
    if r2_1 + 1 == r1_2 or r1_1 - 1 == r2_2:
        relations.append("vertically_adjacent")
    if c2_1 + 1 == c1_2 or c1_1 - 1 == c2_2:
        relations.append("horizontally_adjacent")

    # Check overlap
    overlap_r = max(0, min(r2_1, r2_2) - max(r1_1, r1_2) + 1)
    overlap_c = max(0, min(c2_1, c2_2) - max(c1_1, c1_2) + 1)
    if overlap_r > 0 and overlap_c > 0:
        relations.append("overlapping")

    # Distance between centers
    dr = obj2.get("center_r", (r1_2 + r2_2) / 2) - obj1.get("center_r", (r1_1 + r2_1) / 2)
    dc = obj2.get("center_c", (c1_2 + c2_2) / 2) - obj1.get("center_c", (c1_1 + c2_1) / 2)

    return {
        "relations": relations,
        "center_distance": (round(dr, 1), round(dc, 1)),
        "same_row": abs(dr) < 1,
        "same_col": abs(dc) < 1,
    }
