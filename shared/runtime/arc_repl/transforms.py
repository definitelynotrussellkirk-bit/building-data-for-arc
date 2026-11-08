"""
Grid transform primitives — the macros the model can call via transform!

Every transform is registered with metadata for help/discovery.
Each function takes a grid (list of lists) and returns a new grid.
"""

import numpy as np
from copy import deepcopy
from .registry import register_transform, TRANSFORM_REGISTRY
from .grid_ops import (find_objects, find_enclosed, neighbors_4, neighbors_8,
                       bounding_box, flood_fill_mask, where_color,
                       where_adjacent_to, dilate_mask, erode_mask)


# ============================================================
# Geometric
# ============================================================

@register_transform("geometric", "rotate_cw <grid>", "Rotate 90° clockwise", "transform! rotate_cw @1")
def rotate_cw(grid):
    return np.rot90(np.array(grid), -1).tolist()

@register_transform("geometric", "rotate_ccw <grid>", "Rotate 90° counter-clockwise")
def rotate_ccw(grid):
    return np.rot90(np.array(grid), 1).tolist()

@register_transform("geometric", "rotate_180 <grid>", "Rotate 180°")
def rotate_180(grid):
    return np.rot90(np.array(grid), 2).tolist()

@register_transform("geometric", "flip_lr <grid>", "Mirror left-right", "transform! flip_lr @1")
def flip_lr(grid):
    return np.fliplr(np.array(grid)).tolist()

@register_transform("geometric", "flip_ud <grid>", "Mirror up-down")
def flip_ud(grid):
    return np.flipud(np.array(grid)).tolist()

@register_transform("geometric", "transpose <grid>", "Swap rows and columns")
def transpose(grid):
    return np.array(grid).T.tolist()


# ============================================================
# Color
# ============================================================

@register_transform("color", "recolor <grid> <src> <dst>", "Replace all src cells with dst", "transform! recolor @1 8 7")
def recolor(grid, src, dst):
    g = np.array(grid)
    g[g == src] = dst
    return g.tolist()

@register_transform("color", "swap_colors <grid> <c1> <c2>", "Swap two colors")
def swap_colors(grid, c1, c2):
    g = np.array(grid)
    m1, m2 = g == c1, g == c2
    g[m1] = c2
    g[m2] = c1
    return g.tolist()

@register_transform("color", "fill_color <grid> <r> <c> <color>", "Set a single cell")
def fill_color(grid, r, c, color):
    g = deepcopy(grid)
    g[r][c] = color
    return g

@register_transform("color", "recolor_map <grid> <mapping>", "Apply dict {old: new} for multiple colors", "transform! recolor_map @1 {8:7,1:0}")
def recolor_map(grid, mapping):
    g = np.array(grid)
    for old, new in mapping.items():
        g[g == old] = new
    return g.tolist()

@register_transform("color", "remove_color <grid> <color>", "Set all cells of color to background (0)")
def remove_color(grid, color, bg=0):
    g = np.array(grid)
    g[g == color] = bg
    return g.tolist()

@register_transform("color", "keep_only <grid> <color>", "Keep only this color, zero everything else")
def keep_only(grid, color, bg=0):
    g = np.array(grid)
    g[g != color] = bg
    return g.tolist()

@register_transform("color", "invert_colors <grid>", "Invert colors: c → 9-c for non-zero cells")
def invert_colors(grid):
    g = np.array(grid)
    mask = g != 0
    g[mask] = 9 - g[mask]
    return g.tolist()


# ============================================================
# Spatial
# ============================================================

@register_transform("spatial", "crop <grid> <r1> <c1> <r2> <c2>", "Extract subgrid [r1:r2+1, c1:c2+1]", "transform! crop @1 2 3 8 9")
def crop(grid, r1, c1, r2, c2):
    return np.array(grid)[r1:r2+1, c1:c2+1].tolist()

@register_transform("spatial", "crop_to_content <grid>", "Crop to bounding box of all non-zero cells")
def crop_to_content(grid, bg=0):
    g = np.array(grid)
    mask = g != bg
    if not mask.any():
        return grid
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    r1, r2 = np.where(rows)[0][[0, -1]]
    c1, c2 = np.where(cols)[0][[0, -1]]
    return g[r1:r2+1, c1:c2+1].tolist()

@register_transform("spatial", "pad <grid> <top> <bot> <left> <right> [color]", "Add padding around grid")
def pad(grid, top=0, bottom=0, left=0, right=0, color=0):
    return np.pad(np.array(grid), ((top, bottom), (left, right)), constant_values=color).tolist()

@register_transform("spatial", "tile <grid> <nr> <nc>", "Repeat grid nr×nc times", "transform! tile @1 2 3")
def tile(grid, n_rows, n_cols):
    return np.tile(np.array(grid), (n_rows, n_cols)).tolist()

@register_transform("spatial", "shift <grid> <dr> <dc> [fill]", "Translate grid by (dr, dc)")
def shift(grid, dr, dc, fill=0):
    g = np.array(grid)
    h, w = g.shape
    result = np.full_like(g, fill)
    src_r = (max(0, -dr), min(h, h - dr))
    src_c = (max(0, -dc), min(w, w - dc))
    dst_r = (max(0, dr), min(h, h + dr))
    dst_c = (max(0, dc), min(w, w + dc))
    result[dst_r[0]:dst_r[1], dst_c[0]:dst_c[1]] = g[src_r[0]:src_r[1], src_c[0]:src_c[1]]
    return result.tolist()

@register_transform("spatial", "overlay <base> <top> [r_off] [c_off] [transparent]", "Place top grid onto base")
def overlay(base, top, r_offset=0, c_offset=0, transparent=0):
    result = deepcopy(base)
    for r in range(len(top)):
        for c in range(len(top[0])):
            if top[r][c] != transparent:
                nr, nc = r + r_offset, c + c_offset
                if 0 <= nr < len(result) and 0 <= nc < len(result[0]):
                    result[nr][nc] = top[r][c]
    return result

@register_transform("spatial", "upscale <grid> <factor>", "Scale grid up by integer factor (each cell → NxN block)", "transform! upscale @1 3")
def upscale(grid, factor):
    return np.kron(np.array(grid), np.ones((factor, factor), dtype=int)).tolist()

@register_transform("spatial", "downscale <grid> <factor>", "Reduce grid by factor (mode of each block)")
def downscale(grid, factor):
    from collections import Counter
    g = np.array(grid)
    h, w = g.shape
    nh, nw = h // factor, w // factor
    result = np.zeros((nh, nw), dtype=int)
    for r in range(nh):
        for c in range(nw):
            block = g[r*factor:(r+1)*factor, c*factor:(c+1)*factor]
            result[r, c] = Counter(block.flatten().tolist()).most_common(1)[0][0]
    return result.tolist()


# ============================================================
# Permutation
# ============================================================

@register_transform("geometric", "permute_rows <grid> <order>", "Rearrange rows by index list")
def permute_rows(grid, order):
    return [grid[i] for i in order]

@register_transform("geometric", "permute_cols <grid> <order>", "Rearrange columns by index list")
def permute_cols(grid, order):
    return [[row[i] for i in order] for row in grid]

@register_transform("geometric", "swap_rows <grid> <r1> <r2>", "Swap two rows")
def swap_rows(grid, r1, r2):
    g = [list(row) for row in grid]
    g[r1], g[r2] = g[r2], g[r1]
    return g

@register_transform("geometric", "swap_cols <grid> <c1> <c2>", "Swap two columns")
def swap_cols(grid, c1, c2):
    g = [list(row) for row in grid]
    for row in g:
        row[c1], row[c2] = row[c2], row[c1]
    return g

@register_transform("geometric", "reverse_rows <grid>", "Reverse row order")
def reverse_rows(grid):
    return list(reversed([list(r) for r in grid]))

@register_transform("geometric", "reverse_cols <grid>", "Reverse column order")
def reverse_cols(grid):
    return [list(reversed(row)) for row in grid]


# ============================================================
# Object-level
# ============================================================

@register_transform("object", "move_object <grid> <cells> <dr> <dc>", "Translate an object by (dr, dc)")
def move_object(grid, cells, dr, dc, fill=0):
    g = deepcopy(grid)
    vals = [(r, c, g[r][c]) for r, c in cells]
    for r, c, _ in vals:
        g[r][c] = fill
    for r, c, v in vals:
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(g) and 0 <= nc < len(g[0]):
            g[nr][nc] = v
    return g

@register_transform("object", "remove_object <grid> <cells>", "Delete an object (fill with bg)")
def remove_object(grid, cells, fill=0):
    g = deepcopy(grid)
    for r, c in cells:
        g[r][c] = fill
    return g

@register_transform("object", "copy_object <grid> <cells> <dr> <dc>", "Duplicate object to new position")
def copy_object(grid, cells, dr, dc):
    g = deepcopy(grid)
    for r, c in cells:
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(g) and 0 <= nc < len(g[0]):
            g[nr][nc] = g[r][c]
    return g

@register_transform("object", "recolor_object <grid> <cells> <color>", "Change all cells of object to new color")
def recolor_object(grid, cells, new_color):
    g = deepcopy(grid)
    for r, c in cells:
        g[r][c] = new_color
    return g

@register_transform("object", "grow_object <grid> <cells> [amount]", "Expand object boundary by N cells")
def grow_object(grid, cells, amount=1, color=None):
    g = np.array(grid)
    h, w = g.shape
    if color is None:
        color = int(g[cells[0][0], cells[0][1]])
    cell_set = set(cells)
    for _ in range(amount):
        new_cells = set()
        for r, c in cell_set:
            for nr, nc in neighbors_4(r, c, h, w):
                if (nr, nc) not in cell_set and g[nr, nc] == 0:
                    new_cells.add((nr, nc))
        cell_set.update(new_cells)
    result = deepcopy(grid)
    for r, c in cell_set:
        result[r][c] = color
    return result

@register_transform("object", "shrink_object <grid> <cells> [amount]", "Erode object boundary by N cells")
def shrink_object(grid, cells, amount=1, bg=0):
    g = np.array(grid)
    h, w = g.shape
    cell_set = set(cells)
    for _ in range(amount):
        boundary = set()
        for r, c in cell_set:
            for nr, nc in neighbors_4(r, c, h, w):
                if (nr, nc) not in cell_set:
                    boundary.add((r, c))
                    break
        cell_set -= boundary
    result = deepcopy(grid)
    removed = set(cells) - cell_set
    for r, c in removed:
        result[r][c] = bg
    return result

@register_transform("object", "center_object <grid> <cells>", "Center an object within the grid")
def center_object(grid, cells, bg=0):
    g = np.array(grid)
    h, w = g.shape
    r1, c1, r2, c2 = bounding_box(cells)
    oh, ow = r2 - r1 + 1, c2 - c1 + 1
    target_r = (h - oh) // 2
    target_c = (w - ow) // 2
    dr = target_r - r1
    dc = target_c - c1
    return move_object(grid, cells, dr, dc, fill=bg)


# ============================================================
# Fill
# ============================================================

@register_transform("fill", "fill_enclosed <grid> [color]", "Flood-fill all enclosed background regions", "transform! fill_enclosed @1")
def fill_enclosed(grid, color=None, bg=0):
    g = np.array(grid)
    enclosed = find_enclosed(grid, bg)
    if color is not None:
        g[enclosed] = color
    else:
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
                        for nr, nc in neighbors_4(cr, cc, h, w):
                            if enclosed[nr, nc] and not visited[nr, nc]:
                                visited[nr, nc] = True
                                queue.append((nr, nc))
                            elif g[nr, nc] != bg:
                                boundary.append(int(g[nr, nc]))
                    if boundary:
                        fc = Counter(boundary).most_common(1)[0][0]
                        for pr, pc in region:
                            g[pr, pc] = fc
    return g.tolist()

@register_transform("fill", "fill_region <grid> <r> <c> <color>", "Flood-fill from seed point with color")
def fill_region(grid, seed_r, seed_c, color):
    g = deepcopy(grid)
    h, w = len(g), len(g[0])
    old_color = g[seed_r][seed_c]
    if old_color == color:
        return g
    queue = [(seed_r, seed_c)]
    g[seed_r][seed_c] = color
    while queue:
        cr, cc = queue.pop(0)
        for nr, nc in neighbors_4(cr, cc, h, w):
            if g[nr][nc] == old_color:
                g[nr][nc] = color
                queue.append((nr, nc))
    return g

@register_transform("fill", "gravity_fill <grid> <direction>", "Drop all non-bg cells in direction", "transform! gravity_fill @1 down")
def gravity_fill(grid, direction, bg=0):
    g = np.array(grid)
    h, w = g.shape
    if direction in ("down", "up"):
        for c in range(w):
            vals = [g[r, c] for r in range(h) if g[r, c] != bg]
            col = [bg] * h
            if direction == "down":
                for i, v in enumerate(reversed(vals)):
                    col[h - 1 - i] = v
            else:
                for i, v in enumerate(vals):
                    col[i] = v
            for r in range(h):
                g[r, c] = col[r]
    elif direction in ("left", "right"):
        for r in range(h):
            vals = [g[r, c] for c in range(w) if g[r, c] != bg]
            row = [bg] * w
            if direction == "right":
                for i, v in enumerate(reversed(vals)):
                    row[w - 1 - i] = v
            else:
                for i, v in enumerate(vals):
                    row[i] = v
            for c in range(w):
                g[r, c] = row[c]
    return g.tolist()

@register_transform("fill", "fill_bbox <grid> <r1> <c1> <r2> <c2> <color>", "Fill rectangular region with color")
def fill_bbox(grid, r1, c1, r2, c2, color):
    g = deepcopy(grid)
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if 0 <= r < len(g) and 0 <= c < len(g[0]):
                g[r][c] = color
    return g

@register_transform("fill", "fill_row <grid> <row> <color>", "Fill entire row with color")
def fill_row(grid, row, color):
    g = deepcopy(grid)
    for c in range(len(g[0])):
        g[row][c] = color
    return g

@register_transform("fill", "fill_col <grid> <col> <color>", "Fill entire column with color")
def fill_col(grid, col, color):
    g = deepcopy(grid)
    for r in range(len(g)):
        g[r][col] = color
    return g

@register_transform("fill", "fill_border <grid> <color>", "Fill grid border with color")
def fill_border(grid, color):
    g = deepcopy(grid)
    h, w = len(g), len(g[0])
    for c in range(w):
        g[0][c] = color
        g[h-1][c] = color
    for r in range(h):
        g[r][0] = color
        g[r][w-1] = color
    return g

@register_transform("fill", "fill_between <grid> <c1> <c2> <fill>", "Fill cells between two colored regions")
def fill_between(grid, color1, color2, fill_color):
    g = np.array(grid)
    h, w = g.shape
    result = deepcopy(grid)
    # Fill rows where both colors appear, between their positions
    for r in range(h):
        row = g[r, :]
        pos1 = np.where(row == color1)[0]
        pos2 = np.where(row == color2)[0]
        if len(pos1) > 0 and len(pos2) > 0:
            start = min(pos1.min(), pos2.min())
            end = max(pos1.max(), pos2.max())
            for c in range(start + 1, end):
                if result[r][c] == 0:
                    result[r][c] = fill_color
    # Same for columns
    for c in range(w):
        col = g[:, c]
        pos1 = np.where(col == color1)[0]
        pos2 = np.where(col == color2)[0]
        if len(pos1) > 0 and len(pos2) > 0:
            start = min(pos1.min(), pos2.min())
            end = max(pos1.max(), pos2.max())
            for r in range(start + 1, end):
                if result[r][c] == 0:
                    result[r][c] = fill_color
    return result


# ============================================================
# Structural
# ============================================================

@register_transform("structural", "draw_line <grid> <r1> <c1> <r2> <c2> <color>", "Draw line between two points (Bresenham)")
def draw_line(grid, r1, c1, r2, c2, color):
    g = deepcopy(grid)
    dr = abs(r2 - r1)
    dc = abs(c2 - c1)
    sr = 1 if r1 < r2 else -1
    sc = 1 if c1 < c2 else -1
    err = dr - dc
    r, c = r1, c1
    while True:
        if 0 <= r < len(g) and 0 <= c < len(g[0]):
            g[r][c] = color
        if r == r2 and c == c2:
            break
        e2 = 2 * err
        if e2 > -dc:
            err -= dc
            r += sr
        if e2 < dr:
            err += dr
            c += sc
    return g

@register_transform("structural", "draw_rect <grid> <r1> <c1> <r2> <c2> <color> [fill]", "Draw rectangle outline or filled")
def draw_rect(grid, r1, c1, r2, c2, color, fill=False):
    g = deepcopy(grid)
    if fill:
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if 0 <= r < len(g) and 0 <= c < len(g[0]):
                    g[r][c] = color
    else:
        for c in range(c1, c2 + 1):
            if 0 <= r1 < len(g) and 0 <= c < len(g[0]):
                g[r1][c] = color
            if 0 <= r2 < len(g) and 0 <= c < len(g[0]):
                g[r2][c] = color
        for r in range(r1, r2 + 1):
            if 0 <= r < len(g) and 0 <= c1 < len(g[0]):
                g[r][c1] = color
            if 0 <= r < len(g) and 0 <= c2 < len(g[0]):
                g[r][c2] = color
    return g

@register_transform("structural", "draw_cross <grid> <r> <c> <color> [size]", "Draw + centered at (r,c)")
def draw_cross(grid, r, c, color, size=None):
    g = deepcopy(grid)
    h, w = len(g), len(g[0])
    sz = size if size is not None else max(h, w)
    for i in range(1, sz + 1):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr * i, c + dc * i
            if 0 <= nr < h and 0 <= nc < w:
                g[nr][nc] = color
    return g

@register_transform("structural", "extend_line <grid> <r> <c> <dr> <dc> <color>", "Extend from point in direction until hitting edge or non-bg")
def extend_line(grid, r, c, dr, dc, color, bg=0):
    g = deepcopy(grid)
    h, w = len(g), len(g[0])
    nr, nc = r + dr, c + dc
    while 0 <= nr < h and 0 <= nc < w:
        if g[nr][nc] != bg:
            break
        g[nr][nc] = color
        nr += dr
        nc += dc
    return g

@register_transform("structural", "connect_dots <grid> <color> [line_color]", "Draw lines between all cells of a color (same row/col)")
def connect_dots(grid, color, line_color=None):
    g = np.array(grid)
    lc = line_color if line_color is not None else color
    positions = list(zip(*np.where(g == color)))
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            r1, c1 = positions[i]
            r2, c2 = positions[j]
            if r1 == r2:
                for c in range(min(c1, c2), max(c1, c2) + 1):
                    if g[r1, c] == 0:
                        g[r1, c] = lc
            elif c1 == c2:
                for r in range(min(r1, r2), max(r1, r2) + 1):
                    if g[r, c1] == 0:
                        g[r, c1] = lc
    return g.tolist()

@register_transform("structural", "trace_outline <grid> <color> [outline_color]", "Draw outline around all cells of a color")
def trace_outline(grid, color, outline_color=None):
    g = np.array(grid)
    h, w = g.shape
    oc = outline_color if outline_color is not None else color
    result = g.copy()
    for r in range(h):
        for c in range(w):
            if g[r, c] == color:
                for nr, nc in neighbors_4(r, c, h, w):
                    if g[nr, nc] == 0:
                        result[nr, nc] = oc
    return result.tolist()

@register_transform("structural", "mirror_region <grid> <r1> <c1> <r2> <c2> <axis>", "Mirror a subregion across axis (lr/ud)")
def mirror_region(grid, r1, c1, r2, c2, axis):
    g = np.array(grid)
    sub = g[r1:r2+1, c1:c2+1]
    if axis == "lr":
        sub = np.fliplr(sub)
    elif axis == "ud":
        sub = np.flipud(sub)
    result = g.copy()
    result[r1:r2+1, c1:c2+1] = sub
    return result.tolist()

@register_transform("structural", "complete_symmetry <grid> <axis>", "Complete partial symmetry by mirroring denser half")
def complete_symmetry(grid, axis):
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


# ============================================================
# Composition (higher-order)
# ============================================================

@register_transform("composition", "for_each_object <grid> <fn>", "Apply fn(grid, obj) to each object")
def for_each_object(grid, fn, bg=0):
    objs = find_objects(grid, bg=bg)
    current = deepcopy(grid)
    for obj in objs:
        current = fn(current, obj)
    return current

@register_transform("composition", "apply_to_region <grid> <r1> <c1> <r2> <c2> <fn>", "Apply transform to a subregion only")
def apply_to_region(grid, r1, c1, r2, c2, transform_fn):
    g = np.array(grid)
    sub = g[r1:r2+1, c1:c2+1].tolist()
    transformed = transform_fn(sub)
    result = g.copy()
    result[r1:r2+1, c1:c2+1] = np.array(transformed)
    return result.tolist()

@register_transform("composition", "apply_with_mask <grid> <mask> <fn>", "Apply transform only where mask is True", accepts_mask=True)
def apply_with_mask(grid, mask, transform_fn):
    g = np.array(grid)
    m = np.array(mask, dtype=bool)
    transformed = np.array(transform_fn(grid))
    result = g.copy()
    result[m] = transformed[m]
    return result.tolist()
