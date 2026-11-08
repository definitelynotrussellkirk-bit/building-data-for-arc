"""
Grid builtins — constructors, accessors, mutation, row/col ops, algebra, transforms.
"""

import numpy as np
from collections import Counter

from ..evaluator import Closure
from .helpers import Grid, _unwrap, _wrap, _call, _apply_closure, _make_transform_builtin

# Import transforms and features to trigger decorator registration
from .. import transforms as _transforms_module  # noqa: F401
from ..registry import TRANSFORM_REGISTRY

from .grid_algebra import (
    grid_add, grid_subtract, grid_intersect, grid_xor,
    grid_where, grid_mask_to_cells, cells_to_grid_mask,
    zip_grids, reduce_rows, reduce_cols, map_rows, map_cols,
    grid_eq, grid_diff_mask, broadcast_shape_to_grid,
)


def register(env):
    """Register grid builtins into env."""

    # ============================================================
    # Grid constructors
    # ============================================================
    env.define('grid', lambda rows: Grid(rows))
    env.define('empty-grid', lambda h, w, fill=0: Grid([[fill] * w for _ in range(h)]))
    env.define('grid-from-fn', lambda h, w, fn: Grid(
        [[_call(fn, r, c) for c in range(w)] for r in range(h)]))
    env.define('copy-grid', lambda g: Grid([list(row) for row in _unwrap(g)]))

    # ============================================================
    # Grid accessors
    # ============================================================
    env.define('rows', lambda g: g.height if isinstance(g, Grid) else len(g))
    env.define('cols', lambda g: g.width if isinstance(g, Grid) else (len(g[0]) if g else 0))
    env.define('cell-at', lambda g, r, c: (_unwrap(g))[r][c])
    # safe-at: bounds-checked cell access with default. Prompts teach the
    # model to prefer this over cell-at near edges. Python fallback was
    # missing this primitive — every Kaggle rule using safe-at crashed
    # with "Unbound: safe-at". Added for parity with Racket prelude.
    def _safe_at(g, r, c, default=0):
        grid = _unwrap(g)
        h = len(grid)
        if h == 0: return default
        w = len(grid[0])
        if 0 <= r < h and 0 <= c < w:
            return grid[r][c]
        return default
    env.define('safe-at', _safe_at)
    env.define('row-at', lambda g, r: list(_unwrap(g)[r]))
    env.define('col-at', lambda g, c: [(_unwrap(g))[r][c] for r in range(len(_unwrap(g)))])
    env.define('grid-colors', lambda g, bg=0: sorted(set(
        v for row in _unwrap(g) for v in row if v != bg)))
    env.define('grid-shape', lambda g: [g.height, g.width] if isinstance(g, Grid) else [len(g), len(g[0]) if g else 0])
    env.define('grid->list', lambda g: _unwrap(g))
    env.define('grid-equal?', lambda a, b: _unwrap(a) == _unwrap(b))

    # All cells as (r, c, val) triples
    env.define('grid-cells', lambda g: [
        [r, c, _unwrap(g)[r][c]] for r in range(len(_unwrap(g)))
        for c in range(len(_unwrap(g)[0]))])

    # ============================================================
    # Object detection & flood fill
    # ============================================================
    from ..grid_ops import find_objects as _find_objects, flood_fill_mask as _ffm

    # 8-connected object detection
    env.define('objects-8', lambda g, bg=0: _find_objects(_unwrap(g), bg, connectivity=8))

    # Multicolor object detection (any non-bg neighbors connect regardless of color)
    from ..grid_ops import find_objects_multicolor as _find_mc
    env.define('objects-multicolor', lambda g, bg=0: _find_mc(_unwrap(g), bg))
    env.define('objects-any', lambda g, bg=0: _find_mc(_unwrap(g), bg))

    # Flood fill: from seed (r,c), fill all same-color connected cells with fill_color
    def _flood_fill(g, r, c, fill_color, connectivity=4):
        gg = _unwrap(g)
        h, w = len(gg), len(gg[0])
        src_color = gg[r][c]
        if src_color == fill_color:
            return Grid([list(row) for row in gg])
        mask = _ffm(gg, r, c, connectivity)
        return Grid([[fill_color if mask[ri][ci] else gg[ri][ci]
                      for ci in range(w)] for ri in range(h)])
    env.define('flood-fill', _flood_fill)

    # Flood fill from seed, filling all TOUCHING same-color cells (anchored fill)
    # Like bucket-fill in a paint program
    env.define('bucket-fill', lambda g, r, c, color: _flood_fill(g, r, c, color, 4))
    env.define('bucket-fill-8', lambda g, r, c, color: _flood_fill(g, r, c, color, 8))

    # Fill all enclosed regions of bg with fill_color (cells not reachable from border)
    def _fill_all_enclosed(g, fill_color, bg=0):
        gg = _unwrap(g)
        h, w = len(gg), len(gg[0])
        # BFS from all border bg cells
        border_reachable = set()
        stack = []
        for r in range(h):
            for c in range(w):
                if (r == 0 or r == h-1 or c == 0 or c == w-1) and gg[r][c] == bg:
                    stack.append((r, c))
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in border_reachable or cr < 0 or cr >= h or cc < 0 or cc >= w:
                continue
            if gg[cr][cc] != bg:
                continue
            border_reachable.add((cr, cc))
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                stack.append((cr+dr, cc+dc))
        return Grid([[fill_color if gg[r][c] == bg and (r,c) not in border_reachable
                       else gg[r][c] for c in range(w)] for r in range(h)])
    env.define('fill-all-enclosed', _fill_all_enclosed)

    # BFS shortest path fill: fill cells on any shortest path between two anchor cells
    def _shortest_path_fill(g, anchor_color, fill_color, wall_color=1):
        from collections import deque
        gg = _unwrap(g)
        h, w = len(gg), len(gg[0])
        anchors = [(r,c) for r in range(h) for c in range(w) if gg[r][c] == anchor_color]
        if len(anchors) != 2:
            return Grid([list(row) for row in gg])
        a, b = anchors
        def bfs(start):
            dist = {start: 0}
            q = deque([start])
            while q:
                r,c = q.popleft()
                for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr,nc = r+dr, c+dc
                    if (nr,nc) not in dist and 0<=nr<h and 0<=nc<w and gg[nr][nc] != wall_color:
                        dist[(nr,nc)] = dist[(r,c)] + 1
                        q.append((nr,nc))
            return dist
        da, db = bfs(a), bfs(b)
        total = da.get(b, -1)
        if total < 0:
            return Grid([list(row) for row in gg])
        result = [list(row) for row in gg]
        for r in range(h):
            for c in range(w):
                if gg[r][c] == 0 and (r,c) in da and (r,c) in db and da[(r,c)] + db[(r,c)] == total:
                    result[r][c] = fill_color
        return Grid(result)
    env.define('shortest-path-fill', _shortest_path_fill)

    # Fill bbox interior of each object with a color
    def _fill_object_bboxes(g, fill_color, bg=0):
        gg = _unwrap(g)
        h, w = len(gg), len(gg[0])
        objs = _find_objects(gg, bg)
        result = [list(row) for row in gg]
        for obj in objs:
            r1, c1, r2, c2 = obj['bbox']
            for r in range(r1, r2+1):
                for c in range(c1, c2+1):
                    if result[r][c] == bg:
                        result[r][c] = fill_color
        return Grid(result)
    env.define('fill-object-bboxes', _fill_object_bboxes)
    env.define('fill-object-bboxes-8', lambda g, fc, bg=0:
        (lambda gg, objs: Grid([[fc if any(
            o['bbox'][0] <= r <= o['bbox'][2] and o['bbox'][1] <= c <= o['bbox'][3]
            for o in objs) and gg[r][c] == bg else gg[r][c]
            for c in range(len(gg[0]))] for r in range(len(gg))]))
        (_unwrap(g), _find_objects(_unwrap(g), bg, connectivity=8)))

    def _fill_concavity(g, bg=0):
        gg = _unwrap(g)
        h, w = len(gg), len(gg[0])
        nz = set((r,c) for r in range(h) for c in range(w) if gg[r][c] != bg)
        if not nz: return Grid([list(row) for row in gg])
        color = gg[list(nz)[0][0]][list(nz)[0][1]]

        # Iterative fill: a bg cell becomes filled if it has non-zero (or already filled)
        # in 2+ cardinal directions. Iterate until stable.
        # THEN also add cells that are in the "shadow" of the shape
        # Use iterative approach with 2-of-4-directions rule
        filled = set()
        changed = True
        while changed:
            changed = False
            all_filled = nz | filled
            for r in range(h):
                for c in range(w):
                    if (r,c) in all_filled: continue
                    up = any((rr,c) in all_filled for rr in range(r-1,-1,-1))
                    down = any((rr,c) in all_filled for rr in range(r+1,h))
                    left = any((r,cc) in all_filled for cc in range(c-1,-1,-1))
                    right = any((r,cc) in all_filled for cc in range(c+1,w))
                    # Count only DIRECT line-of-sight (no gaps between)
                    up_direct = r > 0 and (r-1,c) in all_filled
                    down_direct = r < h-1 and (r+1,c) in all_filled
                    left_direct = c > 0 and (r,c-1) in all_filled
                    right_direct = c < w-1 and (r,c+1) in all_filled
                    adjacent = sum([up_direct, down_direct, left_direct, right_direct])
                    if adjacent >= 2:
                        filled.add((r,c))
                        changed = True

        result = [[bg]*w for _ in range(h)]
        for r,c in filled:
            result[r][c] = color
        return Grid(result)
    env.define('fill-concavity', _fill_concavity)

    # Hollow objects: keep only bbox-border cells of each object
    def _hollow_objects(g, bg=0):
        gg = _unwrap(g)
        h, w = len(gg), len(gg[0])
        objs = _find_objects(gg, bg)
        result = [[bg]*w for _ in range(h)]
        for obj in objs:
            r1,c1,r2,c2 = obj['bbox']
            for r,c in obj['cells']:
                if r == r1 or r == r2 or c == c1 or c == c2:
                    result[r][c] = obj['color']
        return Grid(result)
    env.define('hollow-objects', _hollow_objects)

    # Stack objects by width, right-aligned, bottom-up (smallest on top)
    def _stack_objects_right(g, bg=0):
        gg = _unwrap(g)
        h, w = len(gg), len(gg[0])
        objs = _find_objects(gg, bg)
        # Sort by width (bbox width) ascending
        objs_sorted = sorted(objs, key=lambda o: o['bbox'][3] - o['bbox'][1] + 1)
        result = [[bg]*w for _ in range(h)]
        row = h - 1
        for obj in reversed(objs_sorted):  # widest first (bottom)
            bw = obj['bbox'][3] - obj['bbox'][1] + 1
            color = obj['color']
            # Place right-aligned at current row
            for c in range(w - bw, w):
                result[row][c] = color
            row -= 1
        return Grid(result)
    env.define('stack-objects-right', _stack_objects_right)

    # Recolor objects that enclose bg regions (have interior bg cells)
    def _recolor_enclosing_objects(g, new_color, bg=0):
        gg = _unwrap(g)
        h, w = len(gg), len(gg[0])
        objs = _find_objects(gg, bg)
        result = [list(row) for row in gg]
        for obj in objs:
            r1,c1,r2,c2 = obj['bbox']
            border_reach = set()
            stack = [(r,c) for r in range(r1,r2+1) for c in range(c1,c2+1)
                     if gg[r][c]==bg and (r==r1 or r==r2 or c==c1 or c==c2)]
            while stack:
                cr,cc = stack.pop()
                if (cr,cc) in border_reach or cr<r1 or cr>r2 or cc<c1 or cc>c2 or gg[cr][cc]!=bg:
                    continue
                border_reach.add((cr,cc))
                for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    stack.append((cr+dr,cc+dc))
            has_enclosed = any(gg[r][c]==bg and (r,c) not in border_reach
                              for r in range(r1+1,r2) for c in range(c1+1,c2))
            if has_enclosed:
                for r,c in obj['cells']:
                    result[r][c] = new_color
        return Grid(result)
    env.define('recolor-enclosing-objects', _recolor_enclosing_objects)

    # Recolor objects by nearest marker (marker = non-bg cell in row 0)
    def _recolor_by_nearest_marker(g, target_color=5, bg=0):
        gg = _unwrap(g)
        h, w = len(gg), len(gg[0])
        markers = [(c, gg[0][c]) for c in range(w) if gg[0][c] != bg]
        objs = _find_objects(gg, bg)
        result = [list(row) for row in gg]
        for obj in objs:
            if obj['color'] == target_color:
                r1,c1,r2,c2 = obj['bbox']
                center_c = (c1 + c2) / 2
                nearest = min(markers, key=lambda m: abs(m[0] - center_c))
                for r, c in obj['cells']:
                    result[r][c] = nearest[1]
        return Grid(result)
    env.define('recolor-by-nearest-marker', _recolor_by_nearest_marker)

    # Recolor objects by size rank: largest gets colors[0], 2nd gets colors[1], etc.
    def _recolor_by_rank(g, colors, bg=0):
        gg = _unwrap(g)
        h, w = len(gg), len(gg[0])
        objs = _find_objects(gg, bg)
        objs_sorted = sorted(objs, key=lambda o: -o['size'])
        result = [list(row) for row in gg]
        for i, obj in enumerate(objs_sorted):
            color = colors[i] if i < len(colors) else 0
            for r, c in obj['cells']:
                result[r][c] = color
        return Grid(result)
    env.define('recolor-by-rank', _recolor_by_rank)

    # Slide cells of a specific color left/right/up/down until hitting a wall color
    def _slide_color(g, slide_color, wall_color, direction='left', bg=0):
        gg = _unwrap(g)
        h, w = len(gg), len(gg[0])
        result = [list(row) for row in gg]
        if direction in ('left', 'right'):
            for r in range(h):
                slides = [c for c in range(w) if gg[r][c] == slide_color]
                for c in slides:
                    result[r][c] = bg
                for c in (slides if direction == 'left' else reversed(slides)):
                    if direction == 'left':
                        walls = [wc for wc in range(c) if result[r][wc] == wall_color]
                        dest = (max(walls) + 1) if walls else 0
                    else:
                        walls = [wc for wc in range(c+1, w) if result[r][wc] == wall_color]
                        dest = (min(walls) - 1) if walls else w - 1
                    while dest < w and dest >= 0 and result[r][dest] != bg:
                        dest += (1 if direction == 'left' else -1)
                    if 0 <= dest < w:
                        result[r][dest] = slide_color
        return Grid(result)
    env.define('slide-color', _slide_color)

    # ============================================================
    # Grid mutation (functional — returns new grids)
    # ============================================================
    env.define('set-cell', lambda g, r, c, v: Grid(
        [[v if (ri == r and ci == c) else _unwrap(g)[ri][ci]
          for ci in range(len(_unwrap(g)[0]))] for ri in range(len(_unwrap(g)))]))

    env.define('set-cells', lambda g, cells, v: Grid(
        [[v if (ri, ci) in set(map(tuple, cells)) else _unwrap(g)[ri][ci]
          for ci in range(len(_unwrap(g)[0]))] for ri in range(len(_unwrap(g)))]))

    env.define('map-grid', lambda g, fn: Grid(
        [[_call(fn, r, c, _unwrap(g)[r][c]) for c in range(len(_unwrap(g)[0]))]
         for r in range(len(_unwrap(g)))]))

    env.define('filter-cells', lambda g, fn: [
        [r, c, _unwrap(g)[r][c]] for r in range(len(_unwrap(g)))
        for c in range(len(_unwrap(g)[0])) if _call(fn, r, c, _unwrap(g)[r][c])])

    # Find all positions of a color
    env.define('find-color', lambda g, color: [
        [r, c] for r in range(len(_unwrap(g)))
        for c in range(len(_unwrap(g)[0])) if _unwrap(g)[r][c] == color])

    # Count occurrences of a color
    env.define('count-color', lambda g, color: sum(
        1 for r in _unwrap(g) for v in r if v == color))

    # Row/column full-span detection
    env.define('full-rows', lambda g: [
        [r, _unwrap(g)[r][0]] for r in range(len(_unwrap(g)))
        if len(set(_unwrap(g)[r])) == 1 and _unwrap(g)[r][0] != 0])

    env.define('full-cols', lambda g: [
        [c, _unwrap(g)[0][c]] for c in range(len(_unwrap(g)[0]))
        if len(set(_unwrap(g)[r][c] for r in range(len(_unwrap(g))))) == 1
        and _unwrap(g)[0][c] != 0])

    # ============================================================
    # Spatial selection — grab cells matching criteria in a region
    # ============================================================
    env.define('grab-color', lambda g, color: [
        [r, c] for r in range(len(_unwrap(g))) for c in range(len(_unwrap(g)[0]))
        if _unwrap(g)[r][c] == color])

    env.define('grab-color-in-rect', lambda g, color, r1, c1, r2, c2: [
        [r, c] for r in range(r1, r2+1) for c in range(c1, c2+1)
        if _unwrap(g)[r][c] == color])

    env.define('grab-content-in-rect', lambda g, r1, c1, r2, c2, bg=0: [
        [r, c, _unwrap(g)[r][c]] for r in range(r1, r2+1) for c in range(c1, c2+1)
        if _unwrap(g)[r][c] != bg])

    env.define('subgrid', lambda g, r1, c1, r2, c2: Grid(
        [row[c1:c2+1] for row in _unwrap(g)[r1:r2+1]]))

    env.define('paste-subgrid', lambda g, sub, r1, c1: Grid(
        [[(_unwrap(sub)[r-r1][c-c1] if r1 <= r < r1+len(_unwrap(sub)) and c1 <= c < c1+len(_unwrap(sub)[0]) else _unwrap(g)[r][c])
          for c in range(len(_unwrap(g)[0]))] for r in range(len(_unwrap(g)))]))
    env.define('paste', env.lookup('paste-subgrid'))  # alias

    # Gravity: slide non-bg cells in a direction until hitting wall or another cell
    def _gravity(grid, direction, bg=0):
        g = [list(row) for row in _unwrap(grid)]
        h, w = len(g), len(g[0])
        if direction in ("down", "d"):
            for c in range(w):
                col = [g[r][c] for r in range(h)]
                non_bg = [v for v in col if v != bg]
                new_col = [bg] * (h - len(non_bg)) + non_bg
                for r in range(h):
                    g[r][c] = new_col[r]
        elif direction in ("up", "u"):
            for c in range(w):
                col = [g[r][c] for r in range(h)]
                non_bg = [v for v in col if v != bg]
                new_col = non_bg + [bg] * (h - len(non_bg))
                for r in range(h):
                    g[r][c] = new_col[r]
        elif direction in ("right", "r"):
            for r in range(h):
                non_bg = [v for v in g[r] if v != bg]
                g[r] = [bg] * (w - len(non_bg)) + non_bg
        elif direction in ("left", "l"):
            for r in range(h):
                non_bg = [v for v in g[r] if v != bg]
                g[r] = non_bg + [bg] * (w - len(non_bg))
        return Grid(g)
    env.define('gravity', _gravity)

    # Border cells: list of (r, c) on the grid border
    def _border_cells(grid):
        g = _unwrap(grid)
        h, w = len(g), len(g[0])
        cells = set()
        for r in range(h):
            cells.add((r, 0))
            cells.add((r, w - 1))
        for c in range(w):
            cells.add((0, c))
            cells.add((h - 1, c))
        return sorted(cells)
    env.define('border-cells', _border_cells)

    # Count cells matching a predicate
    env.define('count-if', lambda fn, lst: sum(1 for x in lst if _call(fn, x)))

    # ============================================================
    # Axis normalization — work in canonical orientation
    # ============================================================
    def _detect_full_line(grid, color):
        """Find a full-span line of `color`. Returns [0, idx] for row, [1, idx] for col, or None.
        Use (= (first result) 0) for row, (= (first result) 1) for col."""
        g = _unwrap(grid)
        h, w = len(g), len(g[0])
        for r in range(h):
            if all(g[r][c] == color for c in range(w)):
                return [0, r]  # 0 = row axis
        for c in range(w):
            if all(g[r][c] == color for r in range(h)):
                return [1, c]  # 1 = col axis
        return None

    env.define('detect-full-line', _detect_full_line)

    def _normalize_to_vertical(grid):
        """If grid has a horizontal full-span line, transpose it so it becomes vertical.
        Returns (grid, transposed?) tuple."""
        g = _unwrap(grid)
        h, w = len(g), len(g[0])
        # Check for horizontal full-span lines (any color)
        for r in range(h):
            vals = set(g[r])
            if len(vals) == 1 and g[r][0] != 0:
                # Has a horizontal separator → transpose
                return (Grid([list(row) for row in zip(*g)]), True)
        return (Grid(g), False)

    env.define('normalize-to-vertical', _normalize_to_vertical)
    env.define('denormalize', lambda grid, was_transposed:
        Grid([list(row) for row in zip(*_unwrap(grid))]) if was_transposed else grid)

    # ============================================================
    # Vector stamping — repeat a pattern along a direction
    # ============================================================
    def _stamp_along(grid, cells, color, dr, dc, max_steps=50):
        """Stamp a set of cells repeatedly along direction (dr,dc), colored with `color`.
        Only stamps on 0-cells. Returns new grid."""
        g = [list(row) for row in _unwrap(grid)]
        h, w = len(g), len(g[0])
        for step in range(1, max_steps):
            any_placed = False
            for r, c in cells:
                nr = r + dr * step
                nc = c + dc * step
                if 0 <= nr < h and 0 <= nc < w and g[nr][nc] == 0:
                    g[nr][nc] = color
                    any_placed = True
            if not any_placed:
                break
        return Grid(g)

    env.define('stamp-along', _stamp_along)

    def _detect_direction(grid, from_obj, to_obj):
        """Detect direction vector from one object to another. Returns (dr, dc) normalized to -1/0/1."""
        from_cells = from_obj if isinstance(from_obj, list) else getattr(from_obj, 'cells', [])
        to_cells = to_obj if isinstance(to_obj, list) else getattr(to_obj, 'cells', [])

        fr = sum(r for r, c in from_cells) / len(from_cells)
        fc = sum(c for r, c in from_cells) / len(from_cells)
        tr = sum(r for r, c in to_cells) / len(to_cells)
        tc = sum(c for r, c in to_cells) / len(to_cells)

        dr = 0 if abs(tr - fr) < 0.5 else (1 if tr > fr else -1)
        dc = 0 if abs(tc - fc) < 0.5 else (1 if tc > fc else -1)
        return (dr, dc)

    env.define('detect-direction', _detect_direction)

    # ============================================================
    # Noisy grid denoising — majority vote across cell repetitions
    # ============================================================
    def _denoise_grid(grid):
        """Auto-detect grid structure (noisy separators), then majority-vote per cell position."""
        g = _unwrap(grid)
        h, w = len(g), len(g[0])

        def find_cell_ranges(size, data_fn, other_size, thresh=0.7, min_cell_size=2):
            seps = [i for i in range(size) if sum(1 for j in range(other_size) if data_fn(i,j) == 0) > other_size * thresh]
            if not seps: return []
            groups = [[seps[0]]]
            for s in seps[1:]:
                if s == groups[-1][-1] + 1:
                    groups[-1].append(s)
                else:
                    groups.append([s])
            cells = []
            for gi in range(len(groups) - 1):
                start = groups[gi][-1] + 1
                end = groups[gi+1][0] - 1
                if end >= start and (end - start + 1) >= min_cell_size:
                    cells.append((start, end - start + 1))
            return cells

        row_cells = find_cell_ranges(h, lambda r,c: g[r][c] if c < w else 0, w)
        col_cells = find_cell_ranges(w, lambda c,r: g[r][c] if r < h else 0, h)
        nr, nc = len(row_cells), len(col_cells)

        if nr == 0 or nc == 0:
            return Grid(g)

        out = [[0]*w for _ in range(h)]
        for r in range(h):
            for c in range(w):
                cr_idx = lr = cc_idx = lc = -1
                for ci, (start, sz) in enumerate(row_cells):
                    if start <= r < start + sz: cr_idx = ci; lr = r - start; break
                for ci, (start, sz) in enumerate(col_cells):
                    if start <= c < start + sz: cc_idx = ci; lc = c - start; break
                if cr_idx < 0 or cc_idx < 0: continue
                vals = []
                for cri in range(nr):
                    for cci in range(nc):
                        rr = row_cells[cri][0] + lr
                        cc2 = col_cells[cci][0] + lc
                        if rr < h and cc2 < w:
                            vals.append(g[rr][cc2])
                nz = [v for v in vals if v != 0]
                if nz:
                    from collections import Counter as C
                    out[r][c] = C(nz).most_common(1)[0][0]
        return Grid(out)

    env.define('denoise-grid', _denoise_grid)

    # ============================================================
    # Border reachability / enclosed detection
    # ============================================================
    def _border_reachable(grid, r, c, bg=0):
        """Check if cell (r,c) can reach the grid border through bg-colored cells."""
        g = _unwrap(grid)
        h, w = len(g), len(g[0])
        if r == 0 or r == h-1 or c == 0 or c == w-1:
            return True
        visited = set()
        queue = [(r, c)]
        visited.add((r, c))
        while queue:
            cr, cc = queue.pop(0)
            if cr == 0 or cr == h-1 or cc == 0 or cc == w-1:
                return True
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = cr+dr, cc+dc
                if 0 <= nr < h and 0 <= nc < w and (nr,nc) not in visited and g[nr][nc] == bg:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        return False

    env.define('border-reachable?', _border_reachable)
    env.define('enclosed?', lambda g, r, c, bg=0: not _border_reachable(g, r, c, bg))

    # ============================================================
    # Gap runs — find contiguous runs of a value in a row
    # ============================================================
    def _gap_runs(grid, row, val=0):
        """Find contiguous runs of `val` in the given row. Returns list of (start, length)."""
        g = _unwrap(grid)
        w = len(g[0])
        runs = []
        c = 0
        while c < w:
            if g[row][c] == val:
                start = c
                while c < w and g[row][c] == val:
                    c += 1
                runs.append((start, c - start))
            else:
                c += 1
        return runs

    env.define('gap-runs', _gap_runs)
    env.define('gap-runs-col', lambda g, col, val=0: _gap_runs_col(_unwrap(g), col, val))

    def _gap_runs_col(g, col, val=0):
        h = len(g)
        runs = []
        r = 0
        while r < h:
            if g[r][col] == val:
                start = r
                while r < h and g[r][col] == val:
                    r += 1
                runs.append((start, r - start))
            else:
                r += 1
        return runs

    # ============================================================
    # Overlay multiple grids (non-zero wins, later overrides)
    # ============================================================
    def _overlay_all(grids, bg=0):
        """Overlay list of grids. Non-bg values from later grids override earlier."""
        result = [list(row) for row in _unwrap(grids[0])]
        h, w = len(result), len(result[0])
        for g in grids[1:]:
            gg = _unwrap(g)
            for r in range(min(h, len(gg))):
                for c in range(min(w, len(gg[0]))):
                    if gg[r][c] != bg:
                        result[r][c] = gg[r][c]
        return Grid(result)

    env.define('overlay-all', _overlay_all)

    # ============================================================
    # Detect repeating period of a grid
    # ============================================================
    def _detect_period(grid):
        """Find smallest period P such that grid[r][c] == grid[r%P][c%P] for all non-zero cells."""
        g = _unwrap(grid)
        h, w = len(g), len(g[0])
        for p in range(2, max(h, w) + 1):
            if p > h and p > w:
                break
            ok = True
            for r in range(h):
                for c in range(w):
                    v = g[r][c]
                    if v != 0 and r < p and c < p:
                        continue  # reference cell
                    if v != 0:
                        rr, cc = r % p, c % p
                        if rr < h and cc < w and g[rr][cc] != 0 and g[rr][cc] != v:
                            ok = False
                            break
                if not ok:
                    break
            if ok:
                return p
        return max(h, w)

    env.define('detect-period', _detect_period)

    # ============================================================
    # Row/column run detection (non-zero segments)
    # ============================================================
    def _row_segments(grid, row, bg=0):
        """Find contiguous non-bg segments in a row. Returns [(start, end, color), ...]."""
        g = _unwrap(grid)
        w = len(g[0])
        segs = []
        c = 0
        while c < w:
            if g[row][c] != bg:
                start = c
                color = g[row][c]
                while c < w and g[row][c] != bg:
                    c += 1
                segs.append((start, c - 1, color))
            else:
                c += 1
        return segs

    env.define('row-segments', _row_segments)

    def _col_segments(grid, col, bg=0):
        """Find contiguous non-bg segments in a column."""
        g = _unwrap(grid)
        h = len(g)
        segs = []
        r = 0
        while r < h:
            if g[r][col] != bg:
                start = r
                color = g[r][col]
                while r < h and g[r][col] != bg:
                    r += 1
                segs.append((start, r - 1, color))
            else:
                r += 1
        return segs

    env.define('col-segments', _col_segments)

    # ============================================================
    # Object sliding — move object in direction until hitting wall
    # ============================================================
    def _slide_object(grid, obj, direction, bg=0):
        """Slide an object in a direction until it hits another non-bg cell or edge."""
        direction = str(direction).strip('"')  # handle StrLit
        g = [list(row) for row in _unwrap(grid)]
        h, w = len(g), len(g[0])
        cells = obj if isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], (list, tuple)) else getattr(obj, 'cells', [])

        # Direction deltas
        dr, dc = {'up': (-1,0), 'down': (1,0), 'left': (0,-1), 'right': (0,1),
                  'u': (-1,0), 'd': (1,0), 'l': (0,-1), 'r': (0,1)}[direction]

        # Get cell positions and their colors
        cell_set = set()
        cell_colors = {}
        for cell in cells:
            r, c = (cell[0], cell[1]) if isinstance(cell, (list, tuple)) else (cell.r, cell.c)
            cell_set.add((r, c))
            cell_colors[(r, c)] = g[r][c]

        # Clear original positions
        for r, c in cell_set:
            g[r][c] = bg

        # Slide until blocked
        offset = 0
        while True:
            offset += 1
            blocked = False
            for r, c in cell_set:
                nr, nc = r + dr * offset, c + dc * offset
                if nr < 0 or nr >= h or nc < 0 or nc >= w:
                    blocked = True
                    break
                if (nr, nc) not in cell_set and g[nr][nc] != bg:
                    blocked = True
                    break
            if blocked:
                offset -= 1
                break

        # Place at new positions
        for r, c in cell_set:
            nr, nc = r + dr * offset, c + dc * offset
            g[nr][nc] = cell_colors[(r, c)]

        return Grid(g)

    env.define('slide-object', _slide_object)

    env.define('colors-in-rect', lambda g, r1, c1, r2, c2: sorted(set(
        _unwrap(g)[r][c] for r in range(r1, r2+1) for c in range(c1, c2+1))))

    env.define('color-counts-in-rect', lambda g, r1, c1, r2, c2: dict(Counter(
        _unwrap(g)[r][c] for r in range(r1, r2+1) for c in range(c1, c2+1))))

    env.define('recolor-in-rect', lambda g, r1, c1, r2, c2, src, dst: Grid(
        [[dst if (r1 <= r <= r2 and c1 <= c <= c2 and _unwrap(g)[r][c] == src) else _unwrap(g)[r][c]
          for c in range(len(_unwrap(g)[0]))] for r in range(len(_unwrap(g)))]))

    # ============================================================
    # Higher-level grid analysis (find-0-regions, rect-enclosed?)
    # ============================================================
    def _find_0_regions(grid):
        """Find connected components of 0s. Returns list of cell-lists."""
        g = np.array(_unwrap(grid))
        h, w = g.shape
        visited = np.zeros_like(g, dtype=bool)
        regions = []
        for r in range(h):
            for c in range(w):
                if g[r, c] == 0 and not visited[r, c]:
                    queue = [(r, c)]
                    visited[r, c] = True
                    cells = []
                    while queue:
                        cr, cc = queue.pop(0)
                        cells.append([cr, cc])
                        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                            nr, nc = cr+dr, cc+dc
                            if 0 <= nr < h and 0 <= nc < w and g[nr, nc] == 0 and not visited[nr, nc]:
                                visited[nr, nc] = True
                                queue.append((nr, nc))
                    regions.append(cells)
        return regions

    def _is_rect_enclosed(grid, cells, wall_color=5):
        """Check if a 0-region is enclosed by a rectangle of wall_color."""
        g = np.array(_unwrap(grid))
        h, w = g.shape
        rs = [p[0] for p in cells]
        cs = [p[1] for p in cells]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        fr1, fr2, fc1, fc2 = r1-1, r2+1, c1-1, c2+1

        real_walls = 0

        if fr1 >= 0:
            for fc in range(max(0, fc1), min(w, fc2+1)):
                if g[fr1, fc] != wall_color:
                    return False
            real_walls += 1

        if fr2 < h:
            for fc in range(max(0, fc1), min(w, fc2+1)):
                if g[fr2, fc] != wall_color:
                    return False
            real_walls += 1

        if fc1 >= 0:
            for fr in range(max(0, fr1), min(h, fr2+1)):
                if g[fr, fc1] != wall_color:
                    return False
            real_walls += 1

        if fc2 < w:
            for fr in range(max(0, fr1), min(h, fr2+1)):
                if g[fr, fc2] != wall_color:
                    return False
            real_walls += 1

        return real_walls >= 3

    env.define('find-0-regions', _find_0_regions)
    env.define('rect-enclosed?', _is_rect_enclosed)

    # ============================================================
    # Holey object cells — return cells of objects whose bbox has interior bg cells
    # ============================================================
    def _holey_object_cells(grid, bg=0):
        """Return list of (r,c) cells belonging to objects that have holes
        (i.e., their bounding box interior contains bg-colored cells).
        Uses 4-connected object detection."""
        g = _unwrap(grid)
        from ..grid_ops import find_objects
        objs = find_objects(g, bg)
        result = []
        for obj in objs:
            cells = obj['cells']
            rs = [r for r,c in cells]
            cs = [c for r,c in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            has_hole = False
            for r in range(r0+1, r1):
                for c in range(c0+1, c1):
                    if g[r][c] == bg:
                        has_hole = True
                        break
                if has_hole:
                    break
            if has_hole:
                result.extend(cells)
        return result

    env.define('holey-object-cells', _holey_object_cells)

    # ============================================================
    # Multi-color connected components (8-connected, all non-bg as one group)
    # ============================================================
    def _objects_multicolor(grid, bg=0):
        """Find 8-connected components treating all non-bg cells as connected."""
        g = _unwrap(grid)
        h, w = len(g), len(g[0]) if g else 0
        visited = [[False]*w for _ in range(h)]
        components = []
        for r in range(h):
            for c in range(w):
                if g[r][c] != bg and not visited[r][c]:
                    # BFS 8-connected
                    queue = [(r, c)]
                    visited[r][c] = True
                    cells = []
                    while queue:
                        cr, cc = queue.pop(0)
                        cells.append((cr, cc))
                        for dr in [-1, 0, 1]:
                            for dc in [-1, 0, 1]:
                                if dr == 0 and dc == 0:
                                    continue
                                nr, nc = cr+dr, cc+dc
                                if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and g[nr][nc] != bg:
                                    visited[nr][nc] = True
                                    queue.append((nr, nc))
                    # Build object dict (compatible with objects format)
                    colors = set(g[cr][cc] for cr, cc in cells)
                    components.append({
                        'color': max(colors, key=lambda c: sum(1 for cr,cc in cells if g[cr][cc]==c)),
                        'colors': sorted(colors),
                        'size': len(cells),
                        'cells': cells,
                    })
        return components

    env.define('objects-multicolor', _objects_multicolor)

    # ============================================================
    # BFS shortest path through grid
    # ============================================================
    def _bfs_path(grid, start_r, start_c, end_r, end_c, walkable=0):
        """Find shortest 4-connected path from start to end through walkable-colored cells.
        Returns list of (r,c) positions along the path (including start and end), or empty list if no path."""
        g = _unwrap(grid)
        h, w = len(g), len(g[0]) if g else 0
        start_r, start_c, end_r, end_c = int(start_r), int(start_c), int(end_r), int(end_c)
        if not (0 <= start_r < h and 0 <= start_c < w and 0 <= end_r < h and 0 <= end_c < w):
            return []
        visited = {}
        queue = [(start_r, start_c)]
        visited[(start_r, start_c)] = None
        while queue:
            cr, cc = queue.pop(0)
            if cr == end_r and cc == end_c:
                # Reconstruct path
                path = []
                pos = (cr, cc)
                while pos is not None:
                    path.append(list(pos))
                    pos = visited[pos]
                return path[::-1]
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = cr+dr, cc+dc
                if 0 <= nr < h and 0 <= nc < w and (nr,nc) not in visited:
                    cell_val = g[nr][nc]
                    if cell_val == walkable or (nr == end_r and nc == end_c):
                        visited[(nr,nc)] = (cr, cc)
                        queue.append((nr, nc))
        return []

    def _bfs_fill_path(grid, start_r, start_c, end_r, end_c, color, walkable=0):
        """Find shortest path and fill it with color. Returns new grid."""
        g = _unwrap(grid)
        path = _bfs_path(grid, start_r, start_c, end_r, end_c, walkable)
        if not path:
            return Grid(g)
        result = [row[:] for row in g]
        for r, c in path:
            result[r][c] = color
        return Grid(result)

    env.define('bfs-path', _bfs_path)
    env.define('bfs-fill-path', _bfs_fill_path)

    # ============================================================
    # Flood fill from a specific starting cell
    # ============================================================
    def _flood_from(grid, start_r, start_c, new_color, connectivity=4):
        """Flood fill from (start_r, start_c), replacing the starting cell's color
        with new_color in all connected cells of the same color."""
        g = _unwrap(grid)
        h, w = len(g), len(g[0]) if g else 0
        start_r, start_c = int(start_r), int(start_c)
        if not (0 <= start_r < h and 0 <= start_c < w):
            return Grid(g)
        old_color = g[start_r][start_c]
        if old_color == new_color:
            return Grid(g)
        result = [row[:] for row in g]
        visited = set()
        queue = [(start_r, start_c)]
        visited.add((start_r, start_c))
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        if connectivity == 8:
            dirs += [(-1,-1),(-1,1),(1,-1),(1,1)]
        while queue:
            cr, cc = queue.pop(0)
            result[cr][cc] = new_color
            for dr, dc in dirs:
                nr, nc = cr+dr, cc+dc
                if 0 <= nr < h and 0 <= nc < w and (nr,nc) not in visited and g[nr][nc] == old_color:
                    visited.add((nr,nc))
                    queue.append((nr, nc))
        return Grid(result)

    env.define('flood-from', _flood_from)

    # ============================================================
    # Best orientation — try all 8 rotations/flips to match anchors
    # ============================================================
    def _best_orientation(grid, anchor_pairs):
        """Given a grid and a list of (src_r, src_c, dst_r, dst_c) anchor pairs,
        try all 8 orientations of the grid and return (oriented_grid, translation_dr, translation_dc)
        for the first orientation where all anchors match after translation.
        Returns #f if no orientation matches."""
        g = np.array(_unwrap(grid))
        h, w = g.shape

        def apply_transform(g, t):
            if t == 0: return g
            if t == 1: return np.rot90(g, -1)   # 90 CW
            if t == 2: return np.rot90(g, 2)     # 180
            if t == 3: return np.rot90(g, 1)     # 90 CCW
            if t == 4: return np.flipud(g)
            if t == 5: return np.fliplr(g)
            if t == 6: return np.flipud(np.rot90(g, -1))
            if t == 7: return np.fliplr(np.rot90(g, -1))

        def transform_point(r, c, h, w, t):
            """Transform a point (r,c) according to transform t on a h×w grid."""
            if t == 0: return (r, c)
            if t == 1: return (c, h-1-r)       # 90 CW
            if t == 2: return (h-1-r, w-1-c)   # 180
            if t == 3: return (w-1-c, r)        # 90 CCW
            if t == 4: return (h-1-r, c)        # flip-ud
            if t == 5: return (r, w-1-c)        # flip-lr
            if t == 6: tr, tc = c, h-1-r; return (h-1-tr if False else tr, tc)  # complex
            if t == 7: tr, tc = c, h-1-r; return (tr, w-1-tc if False else tc)

        # Parse anchor pairs
        pairs = []
        for ap in anchor_pairs:
            if isinstance(ap, (list, tuple)) and len(ap) >= 4:
                pairs.append((int(ap[0]), int(ap[1]), int(ap[2]), int(ap[3])))

        if len(pairs) < 1:
            return False

        for t in range(8):
            tg = apply_transform(g, t)
            th, tw = tg.shape

            # Transform source points
            src_transformed = [transform_point(sr, sc, h, w, t) for sr, sc, _, _ in pairs]

            # Compute translation from first pair
            tr0 = pairs[0][2] - src_transformed[0][0]
            tc0 = pairs[0][3] - src_transformed[0][1]

            # Check all pairs match
            all_match = True
            for i, (sr, sc, dr, dc) in enumerate(pairs):
                expected_r = src_transformed[i][0] + tr0
                expected_c = src_transformed[i][1] + tc0
                if expected_r != dr or expected_c != dc:
                    all_match = False
                    break

            if all_match:
                return [Grid(tg.tolist()), tr0, tc0]

        return False

    env.define('best-orientation', _best_orientation)

    # ============================================================
    # Largest solid rectangle of a given color
    # ============================================================
    def _largest_rect(grid, color):
        """Find the largest axis-aligned rectangle consisting entirely of `color`.
        Returns (r1, c1, r2, c2, area) or None."""
        g = _unwrap(grid)
        h, w = len(g), len(g[0]) if g else 0
        # Use histogram approach (maximal rectangle in histogram)
        heights = [0] * w
        best = (0, 0, 0, 0, 0)
        for r in range(h):
            for c in range(w):
                heights[c] = heights[c] + 1 if g[r][c] == color else 0
            # Find max rectangle in histogram
            stack = []
            for c in range(w + 1):
                cur_h = heights[c] if c < w else 0
                start = c
                while stack and stack[-1][1] > cur_h:
                    sc, sh = stack.pop()
                    area = sh * (c - sc)
                    if area > best[4]:
                        best = (r - sh + 1, sc, r, c - 1, area)
                    start = sc
                stack.append((start, cur_h))
        if best[4] == 0:
            return None
        return list(best)

    env.define('largest-rect', _largest_rect)

    def _tallest_rect(grid, color, min_h=2):
        """Find the largest rectangle of a given color with height >= min_h.

        Returns [r1, c1, r2, c2, area] or None.
        """
        g = _unwrap(grid)
        h, w = len(g), len(g[0]) if g else 0
        best = None
        best_area = 0
        for r1 in range(h):
            valid = [True] * w
            for r2 in range(r1, h):
                for c in range(w):
                    if g[r2][c] != color:
                        valid[c] = False
                height = r2 - r1 + 1
                if height < min_h:
                    continue
                run_start = None
                for c in range(w + 1):
                    if c < w and valid[c]:
                        if run_start is None:
                            run_start = c
                    elif run_start is not None:
                        run_len = c - run_start
                        area = height * run_len
                        if area > best_area:
                            best = [r1, run_start, r2, c - 1, area]
                            best_area = area
                        run_start = None
        return best

    env.define('tallest-rect', _tallest_rect)

    def _line_z_order(grid, bg=7):
        """Find overlapping lines and return colors sorted by z-order (bottom to top).

        Each non-bg color forms a line (horizontal, vertical, diagonal, or anti-diagonal).
        Where lines overlap, the visible color is "above" the obscured one.
        Returns list of colors from bottom (most obscured) to top (least obscured).
        Sort key: (obscured_count DESC, color_value DESC).
        """
        g = _unwrap(grid)
        h, w = len(g), len(g[0]) if g else 0
        color_info = {}
        for color in range(10):
            if color == bg:
                continue
            positions = [(r, c) for r in range(h) for c in range(w) if g[r][c] == color]
            if not positions:
                continue
            shown = len(positions)
            # Count cells per row, col, diag (r-c), anti-diag (r+c)
            from collections import Counter as Cnt
            row_c = Cnt(p[0] for p in positions)
            col_c = Cnt(p[1] for p in positions)
            diag_c = Cnt(p[0] - p[1] for p in positions)
            adiag_c = Cnt(p[0] + p[1] for p in positions)
            max_r = max(row_c.values())
            max_c = max(col_c.values())
            max_d = max(diag_c.values())
            max_a = max(adiag_c.values())
            m = max(max_r, max_c, max_d, max_a)
            if m == max_r:
                expected = w
            elif m == max_c:
                expected = h
            elif m == max_d:
                best_d = max(diag_c, key=diag_c.get)
                # Diagonal length for r-c=d in h×w grid
                r_lo, r_hi = max(0, best_d), min(h - 1, w - 1 + best_d)
                expected = max(0, r_hi - r_lo + 1)
            else:
                best_a = max(adiag_c, key=adiag_c.get)
                r_lo = max(0, best_a - w + 1)
                r_hi = min(h - 1, best_a)
                expected = max(0, r_hi - r_lo + 1)
            obscured = expected - shown
            color_info[color] = obscured
        # Sort: obscured DESC, color DESC
        return sorted(color_info.keys(), key=lambda c: (-color_info[c], -c))

    env.define('line-z-order', _line_z_order)

    def _find_largest_frame(grid):
        """Find the largest rectangular frame border in the grid.

        Scans for matching horizontal runs connected by filled vertical borders.
        Returns [r1, c1, r2, c2, interior_h, interior_w, color] of the frame with
        the largest interior, or None if no frame found.
        """
        g = _unwrap(grid)
        h, w = len(g), len(g[0]) if g else 0
        best = None
        best_area = 0
        for color in range(1, 10):
            # Find horizontal runs of this color >= 4
            runs = []
            for r in range(h):
                start = None
                for c in range(w + 1):
                    v = g[r][c] if c < w else -1
                    if v == color:
                        if start is None:
                            start = c
                    elif start is not None:
                        if c - start >= 4:
                            runs.append((r, start, c - 1))
                        start = None
            # Match pairs of runs with same start/end columns
            for i in range(len(runs)):
                r1, c1, c2 = runs[i]
                for j in range(i + 1, len(runs)):
                    r2, c1b, c2b = runs[j]
                    if c1b != c1 or c2b != c2:
                        continue
                    if r2 - r1 < 3:
                        continue
                    # Check left/right borders
                    left_ok = all(g[r][c1] == color for r in range(r1, r2 + 1))
                    right_ok = all(g[r][c2] == color for r in range(r1, r2 + 1))
                    if left_ok and right_ok:
                        area = (r2 - r1 - 1) * (c2 - c1 - 1)
                        if area > best_area:
                            best = [r1, c1, r2, c2, r2 - r1 - 1, c2 - c1 - 1, color]
                            best_area = area
        return best

    env.define('find-largest-frame', _find_largest_frame)

    # ============================================================
    # Grid algebra — matrix-style operations
    # ============================================================
    env.define('grid+', lambda g1, g2, bg=0: Grid(grid_add(_unwrap(g1), _unwrap(g2), bg)))
    env.define('grid-', lambda g1, g2, bg=0: Grid(grid_subtract(_unwrap(g1), _unwrap(g2), bg)))
    env.define('grid*', lambda g, mask: Grid(grid_intersect(_unwrap(g), _unwrap(mask))))
    env.define('grid-xor', lambda g1, g2, bg=0: Grid(grid_xor(_unwrap(g1), _unwrap(g2), bg)))

    env.define('grid-where', lambda g, fn: grid_where(
        _unwrap(g), fn if callable(fn) else (lambda v: _apply_closure(fn, [v]))))
    env.define('grid==', lambda g1, g2: grid_eq(_unwrap(g1), _unwrap(g2)))
    env.define('grid!=', lambda g1, g2: grid_diff_mask(_unwrap(g1), _unwrap(g2)))

    env.define('mask->cells', lambda m: grid_mask_to_cells(m if not isinstance(m, Grid) else _unwrap(m)))
    env.define('cells->mask', lambda cells, h, w: cells_to_grid_mask(cells, h, w))

    env.define('zip-grids', lambda g1, g2, fn: Grid(zip_grids(
        _unwrap(g1), _unwrap(g2), fn if callable(fn) else (lambda a, b: _apply_closure(fn, [a, b])))))

    env.define('map-rows', lambda g, fn: Grid(map_rows(
        _unwrap(g), fn if callable(fn) else (lambda row: _apply_closure(fn, [row])))))
    env.define('map-cols', lambda g, fn: Grid(map_cols(
        _unwrap(g), fn if callable(fn) else (lambda col: _apply_closure(fn, [col])))))
    env.define('reduce-rows', lambda g, fn, init=None: reduce_rows(
        _unwrap(g), fn if callable(fn) else (lambda acc, row: _apply_closure(fn, [acc, row])), init))
    env.define('reduce-cols', lambda g, fn, init=None: reduce_cols(
        _unwrap(g), fn if callable(fn) else (lambda acc, col: _apply_closure(fn, [acc, col])), init))

    env.define('broadcast', lambda pattern, h, w, bg=0: Grid(broadcast_shape_to_grid(
        _unwrap(pattern) if isinstance(pattern, Grid) else pattern, h, w, bg)))

    env.define('grid->numpy', lambda g: np.array(_unwrap(g)))
    env.define('numpy->grid', lambda a: Grid(a.tolist() if hasattr(a, 'tolist') else a))

    # ============================================================
    # All transforms (auto-registered from TRANSFORM_REGISTRY)
    # ============================================================
    for name, entry in TRANSFORM_REGISTRY.items():
        env.define(name, _make_transform_builtin(entry.fn))

    # Kebab-case aliases for common transforms
    _aliases = {
        'rotate-cw': 'rotate_cw', 'rotate-ccw': 'rotate_ccw',
        'flip-lr': 'flip_lr', 'flip-ud': 'flip_ud',
        'swap-colors': 'swap_colors', 'fill-color': 'fill_color',
        'recolor-map': 'recolor_map', 'remove-color': 'remove_color',
        'keep-only': 'keep_only', 'invert-colors': 'invert_colors',
        'crop-to-content': 'crop_to_content',
        'fill-enclosed': 'fill_enclosed', 'fill-region': 'fill_region',
        'gravity-fill': 'gravity_fill', 'fill-bbox': 'fill_bbox',
        'fill-row': 'fill_row', 'fill-col': 'fill_col',
        'fill-border': 'fill_border', 'fill-between': 'fill_between',
        'draw-line': 'draw_line', 'draw-rect': 'draw_rect',
        'draw-cross': 'draw_cross', 'extend-line': 'extend_line',
        'connect-dots': 'connect_dots', 'trace-outline': 'trace_outline',
        'mirror-region': 'mirror_region', 'complete-symmetry': 'complete_symmetry',
        'move-object': 'move_object', 'remove-object': 'remove_object',
        'copy-object': 'copy_object', 'recolor-object': 'recolor_object',
        'grow-object': 'grow_object', 'shrink-object': 'shrink_object',
        'center-object': 'center_object',
        'for-each-object': 'for_each_object',
        'apply-to-region': 'apply_to_region', 'apply-with-mask': 'apply_with_mask',
        'swap-rows': 'swap_rows', 'swap-cols': 'swap_cols',
        'permute-rows': 'permute_rows', 'permute-cols': 'permute_cols',
        'reverse-rows': 'reverse_rows', 'reverse-cols': 'reverse_cols',
    }
    for alias, original in _aliases.items():
        if original in TRANSFORM_REGISTRY:
            env.define(alias, _make_transform_builtin(TRANSFORM_REGISTRY[original].fn))
