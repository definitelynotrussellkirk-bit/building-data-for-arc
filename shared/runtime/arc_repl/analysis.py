"""
High-level grid analysis — detect structural patterns that appear across many ARC tasks.

These are the features that would have made previous tasks trivial to spot.
All functions work on raw grids (list-of-lists) and return structured dicts.
"""

import numpy as np
from collections import Counter
from .grid_ops import find_objects, find_enclosed, neighbors_4, bounding_box


# ============================================================
# Rectangular frames
# ============================================================

def detect_frames(grid, wall_color=None, bg=0):
    """Find rectangular outlines (frames) made of a single color.

    Returns list of {color, r1, c1, r2, c2, interior_cells, interior_size}.
    A frame = a rectangular ring of cells of one color surrounding a rectangular
    region of background cells.
    """
    g = np.array(grid)
    h, w = g.shape
    results = []

    # Try each non-bg color
    colors_to_check = [wall_color] if wall_color else sorted(set(g.flatten().tolist()) - {bg})

    for wc in colors_to_check:
        # Find all rectangular 0-regions and check if they have a wc frame
        visited = np.zeros_like(g, dtype=bool)
        for r in range(h):
            for c in range(w):
                if g[r, c] == bg and not visited[r, c]:
                    # BFS to find connected bg-region
                    queue = [(r, c)]
                    visited[r, c] = True
                    cells = []
                    while queue:
                        cr, cc = queue.pop(0)
                        cells.append((cr, cc))
                        for nr, nc in neighbors_4(cr, cc, h, w):
                            if g[nr, nc] == bg and not visited[nr, nc]:
                                visited[nr, nc] = True
                                queue.append((nr, nc))

                    # Check if rectangular
                    rs = [p[0] for p in cells]
                    cs = [p[1] for p in cells]
                    r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
                    if len(cells) != (r2 - r1 + 1) * (c2 - c1 + 1):
                        continue  # not rectangular

                    # Check frame: top, bottom, left, right
                    fr1, fr2, fc1, fc2 = r1 - 1, r2 + 1, c1 - 1, c2 + 1
                    ok = True

                    # Top and bottom must be in-bounds and wall_color
                    if fr1 < 0 or fr2 >= h:
                        ok = False
                    if ok:
                        for fc in range(max(0, fc1), min(w, fc2 + 1)):
                            if g[fr1, fc] != wc or g[fr2, fc] != wc:
                                ok = False
                                break
                    if ok:
                        for fr in range(fr1, fr2 + 1):
                            if fc1 >= 0 and g[fr, fc1] != wc:
                                ok = False
                                break
                            if fc2 < w and g[fr, fc2] != wc:
                                ok = False
                                break
                    # Extra check for border frames: the wall must NOT extend
                    # past the frame on the border side (else it's an L not a U)
                    if ok and (fc1 < 0 or fc2 >= w):
                        if fc1 < 0:  # left border
                            if fr1 > 0 and g[fr1 - 1, 0] == wc:
                                ok = False
                            if fr2 < h - 1 and g[fr2 + 1, 0] == wc:
                                ok = False
                        if fc2 >= w:  # right border
                            if fr1 > 0 and g[fr1 - 1, w - 1] == wc:
                                ok = False
                            if fr2 < h - 1 and g[fr2 + 1, w - 1] == wc:
                                ok = False

                    if ok:
                        results.append({
                            "color": wc,
                            "frame": (fr1, fc1, fr2, fc2),
                            "interior": (r1, c1, r2, c2),
                            "interior_cells": cells,
                            "interior_size": len(cells),
                        })

    return results


def fill_frame_interiors(grid, fill_color, wall_color=None, bg=0):
    """Find rectangular frames and fill their interiors with fill_color."""
    frames = detect_frames(grid, wall_color, bg)
    g = [list(row) for row in grid]
    for frame in frames:
        for r, c in frame["interior_cells"]:
            g[r][c] = fill_color
    return g


# ============================================================
# Full-span lines
# ============================================================

def detect_lines(grid, bg=0):
    """Find full-span rows and columns (all one non-bg color).

    Returns {rows: [(row_idx, color), ...], cols: [(col_idx, color), ...]}.
    """
    g = np.array(grid)
    h, w = g.shape

    full_rows = []
    for r in range(h):
        vals = set(g[r, :].tolist())
        if len(vals) == 1 and bg not in vals:
            full_rows.append((r, int(g[r, 0])))

    full_cols = []
    for c in range(w):
        vals = set(g[:, c].tolist())
        if len(vals) == 1 and bg not in vals:
            full_cols.append((c, int(g[0, c])))

    return {"rows": full_rows, "cols": full_cols}


def find_scattered_pixels(grid, bg=0):
    """Find isolated non-bg pixels that are NOT on full-span lines.

    Returns list of (r, c, color).
    """
    g = np.array(grid)
    h, w = g.shape
    lines = detect_lines(grid, bg)
    line_rows = set(r for r, _ in lines["rows"])
    line_cols = set(c for c, _ in lines["cols"])

    scattered = []
    for r in range(h):
        for c in range(w):
            if g[r, c] != bg and r not in line_rows and c not in line_cols:
                scattered.append((r, c, int(g[r, c])))
    return scattered


# ============================================================
# Regularity / periodicity detection
# ============================================================

def detect_regularity(grid, bg=0):
    """Detect periodic/tiled structure in the grid.

    Returns {periodic: bool, row_period, col_period, tile, anomalies}.
    """
    g = np.array(grid)
    h, w = g.shape

    # Try periods
    best_r, best_c = h, w

    for p in range(2, h // 2 + 1):
        if h % p != 0:
            continue
        tile = g[:p, :]
        matches = sum(1 for i in range(1, h // p)
                      if np.array_equal(g[i*p:(i+1)*p, :], tile))
        if matches == h // p - 1:
            best_r = p
            break

    for p in range(2, w // 2 + 1):
        if w % p != 0:
            continue
        tile = g[:, :p]
        matches = sum(1 for i in range(1, w // p)
                      if np.array_equal(g[:, i*p:(i+1)*p], tile))
        if matches == w // p - 1:
            best_c = p
            break

    periodic = best_r < h or best_c < w

    # Find anomalies: cells that don't match the expected periodic value
    anomalies = []
    if periodic:
        for r in range(h):
            for c in range(w):
                expected = g[r % best_r, c % best_c]
                if g[r, c] != expected:
                    anomalies.append((r, c, int(g[r, c]), int(expected)))

    # Also try majority-vote based regularity (for when anomalies break exact periodicity)
    if not periodic:
        for p in range(2, min(h // 2 + 1, 15)):
            # Majority vote at each position mod p
            votes = np.zeros((p, w), dtype=int)
            for pos_r in range(p):
                for pos_c in range(w):
                    vals = [int(g[r, pos_c]) for r in range(pos_r, h, p)]
                    votes[pos_r, pos_c] = Counter(vals).most_common(1)[0][0]

            # Count how many cells match the majority
            match_count = 0
            total = 0
            for r in range(h):
                for c in range(w):
                    total += 1
                    if g[r, c] == votes[r % p, c]:
                        match_count += 1

            if match_count / total > 0.9:  # >90% match = periodic with anomalies
                best_r = p
                periodic = True
                for r in range(h):
                    for c in range(w):
                        if g[r, c] != votes[r % p, c]:
                            anomalies.append((r, c, int(g[r, c]), int(votes[r % p, c])))
                break

    return {
        "periodic": periodic,
        "row_period": best_r if best_r < h else None,
        "col_period": best_c if best_c < w else None,
        "n_anomalies": len(anomalies),
        "anomalies": anomalies[:20],  # cap for readability
    }


# ============================================================
# Object motion detection
# ============================================================

def detect_motion(input_grid, output_grid, bg=0):
    """Detect how objects moved between input and output.

    Returns list of {color, size, from_bbox, to_bbox, displacement, status}.
    status: 'moved', 'stayed', 'vanished', 'appeared', 'recolored'.
    """
    from .grid_ops import find_objects
    in_objs = find_objects(input_grid, bg)
    out_objs = find_objects(output_grid, bg)

    # Extract sprites for matching
    def sprite(obj, grid):
        g = np.array(grid)
        r1, c1, r2, c2 = obj["bbox"]
        sub = g[r1:r2+1, c1:c2+1]
        mask = np.zeros_like(sub, dtype=bool)
        for r, c in obj["cells"]:
            mask[r - r1, c - c1] = True
        return (sub * mask).tobytes(), sub.shape

    # Match by sprite shape
    in_sprites = [(sprite(o, input_grid), o) for o in in_objs]
    out_sprites = [(sprite(o, output_grid), o) for o in out_objs]

    matched = []
    used_out = set()

    for (is_key, is_shape), io in in_sprites:
        best = None
        best_dist = float("inf")
        for j, ((os_key, os_shape), oo) in enumerate(out_sprites):
            if j in used_out:
                continue
            if is_shape == os_shape and is_key == os_key:
                dist = abs(io["center_r"] - oo["center_r"]) + abs(io["center_c"] - oo["center_c"])
                if dist < best_dist:
                    best_dist = dist
                    best = j
        if best is not None:
            oo = out_sprites[best][1]
            used_out.add(best)
            dr = oo["bbox"][0] - io["bbox"][0]
            dc = oo["bbox"][1] - io["bbox"][1]
            status = "stayed" if dr == 0 and dc == 0 else "moved"
            matched.append({
                "color": io["color"], "size": io["size"],
                "from_bbox": io["bbox"], "to_bbox": oo["bbox"],
                "displacement": (dr, dc), "status": status,
            })

    # Unmatched input = vanished
    matched_in = set(id(m) for _, m in in_sprites[:len(matched)])
    for (_, _), io in in_sprites:
        if not any(m["from_bbox"] == io["bbox"] for m in matched):
            matched.append({
                "color": io["color"], "size": io["size"],
                "from_bbox": io["bbox"], "to_bbox": None,
                "displacement": None, "status": "vanished",
            })

    # Unmatched output = appeared
    for j, (_, oo) in enumerate(out_sprites):
        if j not in used_out:
            matched.append({
                "color": oo["color"], "size": oo["size"],
                "from_bbox": None, "to_bbox": oo["bbox"],
                "displacement": None, "status": "appeared",
            })

    return matched


# ============================================================
# Characterize cells
# ============================================================

def characterize_cells(grid, cells, bg=0):
    """What's special about a set of cells? Returns properties they share.

    Checks: same row, same col, on border, on diagonal, all same color,
    all enclosed, all adjacent to specific color, form a line/rectangle,
    at lattice junctions, etc.
    """
    g = np.array(grid)
    h, w = g.shape
    if not cells:
        return {}

    rs = [c[0] for c in cells]
    cs = [c[1] for c in cells]
    colors = [int(g[r, c]) for r, c in cells]

    props = {}

    # Position patterns
    props["same_row"] = len(set(rs)) == 1
    props["same_col"] = len(set(cs)) == 1
    props["on_diagonal"] = all(r == c for r, c in cells)
    props["on_border"] = all(r == 0 or r == h-1 or c == 0 or c == w-1 for r, c in cells)
    props["all_same_color"] = len(set(colors)) == 1
    if props["all_same_color"]:
        props["color"] = colors[0]

    # Shape of the cell set
    r1, c1, r2, c2 = min(rs), min(cs), max(rs), max(cs)
    props["bbox"] = (r1, c1, r2, c2)
    props["is_rectangular"] = len(cells) == (r2-r1+1) * (c2-c1+1)
    props["is_line"] = (r1 == r2) or (c1 == c2)

    # Adjacency patterns
    all_colors = set(g.flatten().tolist()) - {bg}
    for ac in all_colors:
        adj = all(
            any(g[nr, nc] == ac for nr, nc in neighbors_4(r, c, h, w))
            for r, c in cells
        )
        if adj:
            props[f"all_adjacent_to_{ac}"] = True

    # Regular spacing
    if len(cells) > 1:
        if props["same_row"]:
            diffs = sorted(set(cs[i+1] - cs[i] for i in range(len(cs)-1)))
            if len(diffs) == 1:
                props["regular_col_spacing"] = diffs[0]
        if props["same_col"]:
            diffs = sorted(set(rs[i+1] - rs[i] for i in range(len(rs)-1)))
            if len(diffs) == 1:
                props["regular_row_spacing"] = diffs[0]

    return props


# ============================================================
# Internal separators & cell grid
# ============================================================

def internal_separators(grid, bg=0):
    """Find INTERNAL all-bg rows and columns (not border rows/cols).

    Returns {rows: [r1, r2, ...], cols: [c1, c2, ...]} of row/column indices
    where every cell is bg, excluding the first and last row/column.
    """
    g = np.array(grid)
    h, w = g.shape

    sep_rows = []
    for r in range(1, h - 1):
        if all(g[r, c] == bg for c in range(w)):
            sep_rows.append(r)

    sep_cols = []
    for c in range(1, w - 1):
        if all(g[r, c] == bg for r in range(h)):
            sep_cols.append(c)

    return {"rows": sep_rows, "cols": sep_cols}


def band_distance(grid, r, c, ref_r, ref_c, bg=0):
    """Compute number of internal separators between (r,c) and (ref_r,ref_c).

    Counts how many separator rows lie between r and ref_r (row band distance)
    and how many separator cols lie between c and ref_c (col band distance).
    Returns {row_band_dist: N, col_band_dist: N}.
    """
    seps = internal_separators(grid, bg)

    lo_r, hi_r = min(r, ref_r), max(r, ref_r)
    row_bd = sum(1 for sr in seps["rows"] if lo_r < sr < hi_r)

    lo_c, hi_c = min(c, ref_c), max(c, ref_c)
    col_bd = sum(1 for sc in seps["cols"] if lo_c < sc < hi_c)

    return {"row_band_dist": row_bd, "col_band_dist": col_bd}


def cell_grid(grid, bg=0):
    """Decompose grid into a cell grid based on internal separators.

    Returns {row_ranges: [(r_start, r_end), ...],
             col_ranges: [(c_start, c_end), ...],
             n_row_cells: N, n_col_cells: N,
             row_seps: [...], col_seps: [...]}.
    Each range is an inclusive (start, end) pair of the content rows/cols
    between separators.
    """
    g = np.array(grid)
    h, w = g.shape
    seps = internal_separators(grid, bg)

    # Build row ranges from separator positions
    row_boundaries = [-1] + seps["rows"] + [h]
    row_ranges = []
    for i in range(len(row_boundaries) - 1):
        start = row_boundaries[i] + 1
        end = row_boundaries[i + 1] - 1
        if start <= end:
            row_ranges.append((start, end))

    # Build col ranges from separator positions
    col_boundaries = [-1] + seps["cols"] + [w]
    col_ranges = []
    for i in range(len(col_boundaries) - 1):
        start = col_boundaries[i] + 1
        end = col_boundaries[i + 1] - 1
        if start <= end:
            col_ranges.append((start, end))

    return {
        "row_ranges": row_ranges,
        "col_ranges": col_ranges,
        "n_row_cells": len(row_ranges),
        "n_col_cells": len(col_ranges),
        "row_seps": seps["rows"],
        "col_seps": seps["cols"],
    }


def project_through_bands(grid, ref_r1, ref_c1, ref_r2, ref_c2, radius_fn, bg=0):
    """Create a boolean mask based on band distance from a reference rectangle.

    For each pixel (r, c), compute the band distance from the reference
    rectangle defined by (ref_r1, ref_c1) to (ref_r2, ref_c2).
    Then call radius_fn(row_band_dist, col_band_dist) -> (col_tolerance, row_tolerance).
    The pixel is True if its position within its band cell is within the
    tolerance of the reference rectangle's extent.

    This implements the "diamond projection" pattern from task 7d419a02:
    as band distance increases, the projection narrows.
    """
    g = np.array(grid)
    h, w = g.shape
    seps = internal_separators(grid, bg)

    mask = [[False] * w for _ in range(h)]

    # Ref rectangle center for band distance calculation
    ref_center_r = (ref_r1 + ref_r2) / 2.0
    ref_center_c = (ref_c1 + ref_c2) / 2.0

    for r in range(h):
        for c in range(w):
            # Skip separator rows/cols
            if r in seps["rows"] or c in seps["cols"]:
                continue

            # Compute band distances from this pixel to the reference rectangle
            # Row band distance: separators strictly between r and nearest ref row
            if r < ref_r1:
                near_r = ref_r1
            elif r > ref_r2:
                near_r = ref_r2
            else:
                near_r = r  # inside the ref rows

            lo_r, hi_r = min(r, near_r), max(r, near_r)
            d_rb = sum(1 for sr in seps["rows"] if lo_r < sr < hi_r)

            # Col band distance
            if c < ref_c1:
                near_c = ref_c1
            elif c > ref_c2:
                near_c = ref_c2
            else:
                near_c = c  # inside the ref cols

            lo_c, hi_c = min(c, near_c), max(c, near_c)
            d_cb = sum(1 for sc in seps["cols"] if lo_c < sc < hi_c)

            # Get tolerances from the radius function
            col_tol, row_tol = radius_fn(d_rb, d_cb)

            # Check if within tolerance
            # Row tolerance: distance from the ref row range
            if r < ref_r1:
                row_off = ref_r1 - r
            elif r > ref_r2:
                row_off = r - ref_r2
            else:
                row_off = 0

            # Col tolerance: distance from the ref col range
            if c < ref_c1:
                col_off = ref_c1 - c
            elif c > ref_c2:
                col_off = c - ref_c2
            else:
                col_off = 0

            if row_off <= row_tol and col_off <= col_tol:
                mask[r][c] = True

    return mask


def apply_to_mask_region(grid, mask, transform_fn):
    """Apply transform_fn only to pixels where mask is True.

    transform_fn(r, c, current_val) -> new_val
    Pixels where mask is False remain unchanged.
    Returns new grid (list-of-lists).
    """
    h = len(grid)
    w = len(grid[0]) if grid else 0
    result = [list(row) for row in grid]

    for r in range(h):
        for c in range(w):
            if mask[r][c] if isinstance(mask[r], list) else mask[r, c]:
                result[r][c] = transform_fn(r, c, grid[r][c])

    return result


def apply_rule_in_shape(grid, rule_fn, shape_mask):
    """Apply rule_fn to pixels within shape_mask, leave others unchanged.

    "Apply rule X to region Y in shape of Z."
    rule_fn(r, c, current_val) -> new_val
    shape_mask is a 2D boolean mask (list-of-lists or numpy array).
    Returns new grid (list-of-lists).
    """
    h = len(grid)
    w = len(grid[0]) if grid else 0
    result = [list(row) for row in grid]

    for r in range(h):
        for c in range(w):
            is_in = shape_mask[r][c] if isinstance(shape_mask[r], list) else shape_mask[r, c]
            if is_in:
                result[r][c] = rule_fn(r, c, grid[r][c])

    return result


def detect_object_with_enclosure(grid, wall_color=None, bg=0):
    """Find objects that contain enclosed regions inside their bounding box.

    For each non-bg object, check if its bounding box contains enclosed bg
    cells that are surrounded by the object's cells. Returns list of dicts:
    {color, cells, bbox, enclosed_cells, enclosed_count}.

    This is needed for tasks like b2862040 where objects with interior
    holes need special treatment.
    """
    g = np.array(grid)
    h, w = g.shape
    objects = find_objects(grid, bg)

    if wall_color is not None:
        objects = [o for o in objects if o["color"] == wall_color]

    results = []

    for obj in objects:
        r1, c1, r2, c2 = obj["bbox"]
        obj_cells = set(obj["cells"])
        bh = r2 - r1 + 1
        bw = c2 - c1 + 1

        # Skip trivially small objects (can't enclose anything)
        if bh < 3 or bw < 3:
            continue

        # Find bg cells inside the bounding box
        interior_bg = []
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if g[r, c] == bg and (r, c) not in obj_cells:
                    interior_bg.append((r, c))

        if not interior_bg:
            continue

        # Check which bg cells are enclosed by this object
        # BFS from all border-touching bg cells within the bbox
        bbox_bg_set = set(interior_bg)
        border_bg = set()
        for r, c in interior_bg:
            if r == r1 or r == r2 or c == c1 or c == c2:
                border_bg.add((r, c))

        # Flood fill from border bg cells through bg within bbox
        reachable = set()
        queue = list(border_bg)
        for cell in queue:
            reachable.add(cell)

        while queue:
            cr, cc = queue.pop(0)
            for nr, nc in neighbors_4(cr, cc, h, w):
                if (nr, nc) in bbox_bg_set and (nr, nc) not in reachable:
                    reachable.add((nr, nc))
                    queue.append((nr, nc))

        # Enclosed = bg cells in bbox that are NOT reachable from bbox border
        enclosed = [(r, c) for r, c in interior_bg if (r, c) not in reachable]

        if enclosed:
            results.append({
                "color": obj["color"],
                "cells": obj["cells"],
                "bbox": obj["bbox"],
                "enclosed_cells": enclosed,
                "enclosed_count": len(enclosed),
                "size": obj["size"],
                "center_r": obj.get("center_r", (r1 + r2) / 2),
                "center_c": obj.get("center_c", (c1 + c2) / 2),
            })

    return results
