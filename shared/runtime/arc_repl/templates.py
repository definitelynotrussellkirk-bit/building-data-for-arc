"""
Rule templates — pre-built composable rule factories for common ARC patterns.

Each template returns a callable(grid) -> grid.
Use via: template! <name> [args]
Or from Python: rule_fn = template_recolor_map({8: 7, 1: 0})

These cover the most common ARC task types.
"""

import numpy as np
from copy import deepcopy
from .grid_ops import find_objects, find_enclosed, where_color
from . import analysis as _analysis


# ============================================================
# Color templates
# ============================================================

def template_recolor_map(mapping):
    """Apply a color mapping {old: new}."""
    def rule(grid):
        g = np.array(grid)
        for old, new in mapping.items():
            g[g == old] = new
        return g.tolist()
    return rule


def template_swap_colors(c1, c2):
    """Swap two colors everywhere."""
    def rule(grid):
        g = np.array(grid)
        m1 = g == c1
        m2 = g == c2
        g[m1] = c2
        g[m2] = c1
        return g.tolist()
    return rule


def template_recolor_by_size(color_order=None, bg=0):
    """Recolor objects by size rank. Smallest gets first color in order."""
    def rule(grid):
        g = np.array(grid)
        objs = find_objects(grid, bg=bg)
        objs.sort(key=lambda o: o["size"])
        if color_order is None:
            colors = list(range(1, 10))
        else:
            colors = list(color_order)
        for i, obj in enumerate(objs):
            c = colors[i % len(colors)]
            for r, cc in obj["cells"]:
                g[r, cc] = c
        return g.tolist()
    return rule


# ============================================================
# Fill templates
# ============================================================

def template_fill_enclosed(color=None):
    """Fill all enclosed background regions."""
    def rule(grid):
        g = np.array(grid)
        enclosed = find_enclosed(grid)
        if color is not None:
            g[enclosed] = color
        else:
            # Fill with adjacent boundary color
            from collections import Counter
            h, w = g.shape
            visited = np.zeros_like(g, dtype=bool)
            for r in range(h):
                for c in range(w):
                    if enclosed[r, c] and not visited[r, c]:
                        region = []
                        queue = [(r, c)]
                        visited[r, c] = True
                        boundary = []
                        while queue:
                            cr, cc = queue.pop(0)
                            region.append((cr, cc))
                            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                                nr, nc = cr+dr, cc+dc
                                if 0 <= nr < h and 0 <= nc < w:
                                    if enclosed[nr, nc] and not visited[nr, nc]:
                                        visited[nr, nc] = True
                                        queue.append((nr, nc))
                                    elif g[nr, nc] != 0:
                                        boundary.append(int(g[nr, nc]))
                        if boundary:
                            fc = Counter(boundary).most_common(1)[0][0]
                            for pr, pc in region:
                                g[pr, pc] = fc
        return g.tolist()
    return rule


def template_gravity(direction="down", color=None, bg=0):
    """Drop non-bg cells (or specific color) in a direction until hitting something."""
    def rule(grid):
        g = np.array(grid)
        h, w = g.shape
        if direction in ("down", "up"):
            for c in range(w):
                col = g[:, c].tolist()
                cells = [(i, v) for i, v in enumerate(col) if v != bg and (color is None or v == color)]
                # Remove them
                for i, v in cells:
                    g[i, c] = bg
                # Drop them
                if direction == "down":
                    pos = h - 1
                    for _, v in reversed(cells):
                        while pos >= 0 and g[pos, c] != bg:
                            pos -= 1
                        if pos >= 0:
                            g[pos, c] = v
                            pos -= 1
                else:  # up
                    pos = 0
                    for _, v in cells:
                        while pos < h and g[pos, c] != bg:
                            pos += 1
                        if pos < h:
                            g[pos, c] = v
                            pos += 1
        elif direction in ("left", "right"):
            for r in range(h):
                row = g[r, :].tolist()
                cells = [(i, v) for i, v in enumerate(row) if v != bg and (color is None or v == color)]
                for i, v in cells:
                    g[r, i] = bg
                if direction == "right":
                    pos = w - 1
                    for _, v in reversed(cells):
                        while pos >= 0 and g[r, pos] != bg:
                            pos -= 1
                        if pos >= 0:
                            g[r, pos] = v
                            pos -= 1
                else:  # left
                    pos = 0
                    for _, v in cells:
                        while pos < w and g[r, pos] != bg:
                            pos += 1
                        if pos < w:
                            g[r, pos] = v
                            pos += 1
        return g.tolist()
    return rule


# ============================================================
# Geometric templates
# ============================================================

def template_mirror(axis):
    """Mirror grid across axis: 'lr', 'ud', 'both'."""
    def rule(grid):
        g = np.array(grid)
        if axis == "lr":
            return np.fliplr(g).tolist()
        elif axis == "ud":
            return np.flipud(g).tolist()
        elif axis == "both":
            return np.flipud(np.fliplr(g)).tolist()
        return grid
    return rule


def template_complete_symmetry(axis):
    """Complete partial symmetry by mirroring the denser half."""
    def rule(grid):
        g = np.array(grid)
        h, w = g.shape
        if axis == "lr":
            left = (g[:, :w//2] != 0).sum()
            right = (g[:, w//2:] != 0).sum()
            if left >= right:
                g[:, w//2:] = np.fliplr(g[:, :w//2 + (w % 2)])[:, :w - w//2]
            else:
                g[:, :w//2] = np.fliplr(g[:, w//2 - (w % 2):])[:, :w//2]
        elif axis == "ud":
            top = (g[:h//2, :] != 0).sum()
            bot = (g[h//2:, :] != 0).sum()
            if top >= bot:
                g[h//2:, :] = np.flipud(g[:h//2 + (h % 2), :])[:h - h//2, :]
            else:
                g[:h//2, :] = np.flipud(g[h//2 - (h % 2):, :])[:h//2, :]
        return g.tolist()
    return rule


def template_upscale(factor):
    """Scale grid up by integer factor."""
    def rule(grid):
        g = np.array(grid)
        return np.kron(g, np.ones((factor, factor), dtype=int)).tolist()
    return rule


def template_tile(nr, nc):
    """Tile the grid nr × nc times."""
    def rule(grid):
        return np.tile(np.array(grid), (nr, nc)).tolist()
    return rule


# ============================================================
# Object templates
# ============================================================

def template_for_each_object(object_fn, bg=0):
    """Apply object_fn(grid, obj) -> grid for each object sequentially."""
    def rule(grid):
        objs = find_objects(grid, bg=bg)
        current = deepcopy(grid)
        for obj in objs:
            current = object_fn(current, obj)
        return current
    return rule


def template_remove_color(color, bg=0):
    """Remove all cells of a specific color."""
    def rule(grid):
        g = np.array(grid)
        g[g == color] = bg
        return g.tolist()
    return rule


def template_keep_only(color, bg=0):
    """Keep only cells of a specific color, zero everything else."""
    def rule(grid):
        g = np.array(grid)
        g[g != color] = bg
        return g.tolist()
    return rule


def template_crop_to_object(color=None, bg=0):
    """Crop grid to the bounding box of a specific colored object (or all non-bg)."""
    def rule(grid):
        g = np.array(grid)
        if color is not None:
            mask = g == color
        else:
            mask = g != bg
        if not mask.any():
            return grid
        rows = np.any(mask, axis=1)
        cols = np.any(mask, axis=0)
        r1, r2 = np.where(rows)[0][[0, -1]]
        c1, c2 = np.where(cols)[0][[0, -1]]
        return g[r1:r2+1, c1:c2+1].tolist()
    return rule


def template_sort_objects(by="size", direction="lr", bg=0):
    """Sort objects by property and rearrange in direction."""
    def rule(grid):
        g = np.array(grid)
        objs = find_objects(grid, bg=bg)
        if not objs:
            return grid

        if by == "size":
            objs.sort(key=lambda o: o["size"])
        elif by == "color":
            objs.sort(key=lambda o: o["color"])

        # Clear all objects
        result = np.full_like(g, bg)

        # Place them in order
        if direction in ("lr", "rl"):
            if direction == "rl":
                objs = list(reversed(objs))
            col_offset = 0
            for obj in objs:
                r1, c1, r2, c2 = obj["bbox"]
                oh, ow = r2 - r1 + 1, c2 - c1 + 1
                for r, c in obj["cells"]:
                    nr, nc = r - r1, c - c1 + col_offset
                    if 0 <= nr < g.shape[0] and 0 <= nc < g.shape[1]:
                        result[nr, nc] = g[r, c]
                col_offset += ow + 1

        return result.tolist()
    return rule


# ============================================================
# Structural templates
# ============================================================

def template_connect_dots(color, line_color=None):
    """Draw lines between all cells of a color."""
    def rule(grid):
        g = np.array(grid)
        lc = line_color if line_color is not None else color
        positions = list(zip(*np.where(g == color)))
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                r1, c1 = positions[i]
                r2, c2 = positions[j]
                # Only connect along same row or same col
                if r1 == r2:
                    for c in range(min(c1, c2), max(c1, c2) + 1):
                        if g[r1, c] == 0:
                            g[r1, c] = lc
                elif c1 == c2:
                    for r in range(min(r1, r2), max(r1, r2) + 1):
                        if g[r, c1] == 0:
                            g[r, c1] = lc
        return g.tolist()
    return rule


def template_extend_lines(color, direction=None, until="edge", bg=0):
    """Extend all cells of a color in a direction until hitting edge or another color."""
    def rule(grid):
        g = np.array(grid)
        h, w = g.shape
        positions = list(zip(*np.where(g == color)))

        dirs = []
        if direction is None:
            dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        elif direction == "up":
            dirs = [(-1, 0)]
        elif direction == "down":
            dirs = [(1, 0)]
        elif direction == "left":
            dirs = [(0, -1)]
        elif direction == "right":
            dirs = [(0, 1)]
        elif direction == "all":
            dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        for r, c in positions:
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                while 0 <= nr < h and 0 <= nc < w:
                    if g[nr, nc] != bg:
                        break
                    g[nr, nc] = color
                    nr += dr
                    nc += dc
        return g.tolist()
    return rule


# ============================================================
# Template registry (for template! macro)
# ============================================================

# ============================================================
# Enclosure-based templates
# ============================================================

def template_recolor_enclosing_objects(new_color, wall_color=None, bg=0):
    """Recolor objects that contain enclosed regions.

    Finds objects with interior holes and recolors them to new_color.
    """
    def rule(grid):
        g = np.array(grid)
        enclosing = _analysis.detect_object_with_enclosure(grid, wall_color, bg)
        for obj in enclosing:
            for r, c in obj["cells"]:
                g[r, c] = new_color
        return g.tolist()
    return rule


def template_project_diamond(ref_color, change_from, change_to, bg=0):
    """8-to-4 diamond projection from a reference color block through band separators.

    Finds the bounding box of ref_color, then projects outward through bands.
    At band distance d (either row or col), the projection narrows by d cells
    on each side, creating a diamond shape. Cells within the diamond that are
    change_from get recolored to change_to.

    This is the 7d419a02 rule generalized.
    """
    def rule(grid):
        g = np.array(grid)
        h, w = g.shape

        # Find bounding box of ref_color
        positions = list(zip(*np.where(g == ref_color)))
        if not positions:
            return grid
        ref_r1 = min(r for r, c in positions)
        ref_c1 = min(c for r, c in positions)
        ref_r2 = max(r for r, c in positions)
        ref_c2 = max(c for r, c in positions)

        # Ref block half-widths for tolerance calculation
        ref_half_h = (ref_r2 - ref_r1) / 2.0
        ref_half_w = (ref_c2 - ref_c1) / 2.0

        # Diamond radius function: as band distance increases, tolerance shrinks
        def diamond_radius(d_rb, d_cb):
            total_d = d_rb + d_cb
            # At distance 0, full extent; shrinks by 1 cell per band distance
            col_tol = max(0, ref_half_w - d_rb) if d_rb > 0 else ref_half_w + d_cb * 0 + w
            row_tol = max(0, ref_half_h - d_cb) if d_cb > 0 else ref_half_h + d_rb * 0 + h
            # Simpler: within the same band row/col, full tolerance;
            # across bands, shrink proportionally
            if total_d == 0:
                return (w, h)  # full extent for the ref block itself
            col_tol = max(0, ref_half_w + 1 - d_rb)
            row_tol = max(0, ref_half_h + 1 - d_cb)
            return (col_tol, row_tol)

        mask = _analysis.project_through_bands(
            grid, ref_r1, ref_c1, ref_r2, ref_c2, diamond_radius, bg)

        result = g.copy()
        for r in range(h):
            for c in range(w):
                if mask[r][c] and result[r, c] == change_from:
                    result[r, c] = change_to
        return result.tolist()
    return rule


TEMPLATE_REGISTRY = {
    "recolor_map": template_recolor_map,
    "swap_colors": template_swap_colors,
    "recolor_by_size": template_recolor_by_size,
    "fill_enclosed": template_fill_enclosed,
    "gravity": template_gravity,
    "mirror": template_mirror,
    "complete_symmetry": template_complete_symmetry,
    "upscale": template_upscale,
    "tile": template_tile,
    "for_each_object": template_for_each_object,
    "remove_color": template_remove_color,
    "keep_only": template_keep_only,
    "crop_to_object": template_crop_to_object,
    "sort_objects": template_sort_objects,
    "connect_dots": template_connect_dots,
    "extend_lines": template_extend_lines,
    "recolor_enclosing_objects": template_recolor_enclosing_objects,
    "project_diamond": template_project_diamond,
}
