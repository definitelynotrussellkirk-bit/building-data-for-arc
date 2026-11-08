"""
Shape builtins — Shape type, algebra, placement.
"""

from ..shape import Shape
from ..grid_ops import find_objects
from .helpers import Grid, _unwrap, _call


def register(env):
    """Register shape builtins into env."""

    # ============================================================
    # Shape constructors
    # ============================================================
    env.define('shape', lambda text, color=1: Shape.define(text, color))
    env.define('shape-from-pattern', lambda pattern, bg=0: Shape.from_pattern(pattern, bg))
    env.define('place-shape', lambda s, g, r, c: Grid(s.place(_unwrap(g), r, c)))
    env.define('upscale-shape', lambda s, factor: s.upscale(factor))

    # ============================================================
    # Shape algebra — grab, combine, compare shapes
    # ============================================================
    env.define('grab-shape', lambda g, *colors: Shape.from_cells(
        _unwrap(g), [(r, c) for r in range(len(_unwrap(g))) for c in range(len(_unwrap(g)[0]))
                     if _unwrap(g)[r][c] in colors]))

    env.define('grab-region-shape', lambda g, r1, c1, r2, c2, bg=0: Shape.from_bbox(
        _unwrap(g), r1, c1, r2, c2, bg))

    env.define('shape-union', lambda a, b: Shape(list(set(a.pixels) | set(b.pixels))))

    env.define('shape-subtract', lambda a, b: Shape(
        [(dr, dc, c) for dr, dc, c in a.pixels
         if not any(dr == dr2 and dc == dc2 for dr2, dc2, _ in b.pixels)]))

    env.define('shape-intersect', lambda a, b: Shape(
        [(dr, dc, c) for dr, dc, c in a.pixels
         if any(dr == dr2 and dc == dc2 for dr2, dc2, _ in b.pixels)]))

    env.define('shape-solid', lambda s, color: s.recolor_all(color))

    env.define('object-shape', lambda g, obj: Shape.from_object(_unwrap(g), obj))

    env.define('shapes-same-pattern?', lambda a, b: a.same_pattern(b, ignore_color=True))

    env.define('shape-at', lambda g, r, c, radius=1, bg=0: Shape.from_cells(
        _unwrap(g), [(r+dr, c+dc) for dr in range(-radius, radius+1)
                     for dc in range(-radius, radius+1)
                     if 0 <= r+dr < len(_unwrap(g)) and 0 <= c+dc < len(_unwrap(g)[0])
                     and _unwrap(g)[r+dr][c+dc] != bg]))

    env.define('all-shapes', lambda g, bg=0: [
        Shape.from_object(_unwrap(g), obj) for obj in find_objects(_unwrap(g), bg)])

    # ============================================================
    # Shape placement / stamping
    # ============================================================
    def _place_shape_mode(g, shape, r, c, mode="overwrite", bg=0, target_color=None, transparent=0):
        gd = [list(row) for row in _unwrap(g)]
        h, w = len(gd), len(gd[0])
        for dr, dc, color in shape.pixels:
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and color != transparent:
                if mode == "overwrite":
                    gd[nr][nc] = color
                elif mode == "add":
                    if gd[nr][nc] == bg:
                        gd[nr][nc] = color
                elif mode == "mask":
                    if target_color is not None and gd[nr][nc] == target_color:
                        gd[nr][nc] = color
                elif mode == "xor":
                    if gd[nr][nc] == bg:
                        gd[nr][nc] = color
                    elif gd[nr][nc] == color:
                        gd[nr][nc] = bg
        return Grid(gd)

    env.define('place-shape-at', _place_shape_mode)

    def _stamp_everywhere(g, shape, condition_fn, mode="overwrite", bg=0):
        gd = _unwrap(g)
        h, w = len(gd), len(gd[0])
        result = [list(row) for row in gd]
        for r in range(h):
            for c in range(w):
                if _call(condition_fn, r, c, gd[r][c]):
                    for dr, dc, color in shape.pixels:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            if mode == "overwrite":
                                result[nr][nc] = color
                            elif mode == "add" and result[nr][nc] == bg:
                                result[nr][nc] = color
        return Grid(result)

    env.define('stamp-everywhere', _stamp_everywhere)

    def _stamp_at_pos_impl(g, shape, positions, mode="overwrite", bg=0):
        gd = [list(row) for row in _unwrap(g)]
        h, w = len(gd), len(gd[0])
        for pr, pc in positions:
            for dr, dc, color in shape.pixels:
                nr, nc = pr + dr, pc + dc
                if 0 <= nr < h and 0 <= nc < w and color != 0:
                    if mode == "overwrite":
                        gd[nr][nc] = color
                    elif mode == "add" and gd[nr][nc] == bg:
                        gd[nr][nc] = color
        return Grid(gd)

    env.define('stamp-at-positions', _stamp_at_pos_impl)

    def _tile_shape_impl(g, shape, r1, c1, r2, c2):
        gd = [list(row) for row in _unwrap(g)]
        h, w = len(gd), len(gd[0])
        sg = shape.as_grid()
        sh, sw = len(sg), len(sg[0])
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                sr, sc = (r - r1) % sh, (c - c1) % sw
                if sg[sr][sc] != 0:
                    if 0 <= r < h and 0 <= c < w:
                        gd[r][c] = sg[sr][sc]
        return Grid(gd)

    env.define('tile-shape-in-rect', _tile_shape_impl)
