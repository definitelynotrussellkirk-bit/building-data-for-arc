"""
Shape — a portable, relative-position representation of a pattern.

Extract from grid → manipulate → place back at any position or scale.

A Shape is a set of (dr, dc, color) offsets from a center point.
Center is (0,0). Negative offsets = above/left of center.

Usage:
    # Extract from grid
    shape = Shape.from_grid(grid, cells)           # from specific cells
    shape = Shape.from_object(grid, obj)           # from an object dict
    shape = Shape.from_bbox(grid, r1, c1, r2, c2) # from a bounding box region

    # Inspect
    shape.width, shape.height
    shape.pixels        # [(dr, dc, color), ...]
    shape.as_grid()     # renders to a minimal grid with bg=0
    shape.print()       # compact display

    # Transform
    shape.upscale(2)    # each pixel becomes 2x2 block
    shape.upscale(3)    # each pixel becomes 3x3 block
    shape.rotate_cw()   # 90° clockwise
    shape.flip_lr()     # mirror
    shape.recolor(mapping)  # {old: new}

    # Place onto a grid
    result = shape.place(grid, center_r, center_c, transparent=0)
"""

import numpy as np
from copy import deepcopy


class Shape:
    """Portable pattern: list of (dr, dc, color) offsets from center."""

    def __init__(self, pixels: list[tuple[int, int, int]]):
        """pixels: list of (dr, dc, color) relative to center (0,0)."""
        self.pixels = list(pixels)

    # ============================================================
    # Extraction
    # ============================================================

    @classmethod
    def from_cells(cls, grid, cells):
        """Extract shape from specific cells. Center = centroid."""
        g = np.array(grid)
        rs = [r for r, c in cells]
        cs = [c for r, c in cells]
        center_r = (min(rs) + max(rs)) / 2
        center_c = (min(cs) + max(cs)) / 2
        # Snap to int for even centering
        cr = round(center_r)
        cc = round(center_c)
        pixels = []
        for r, c in cells:
            pixels.append((r - cr, c - cc, int(g[r, c])))
        return cls(pixels)

    @classmethod
    def from_object(cls, grid, obj):
        """Extract from an object dict (as returned by features.objects)."""
        return cls.from_cells(grid, obj["cells"])

    @classmethod
    def from_bbox(cls, grid, r1, c1, r2, c2, bg=0):
        """Extract all non-background cells in a bounding box."""
        g = np.array(grid)
        cells = []
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                if g[r, c] != bg:
                    cells.append((r, c))
        if not cells:
            # Include all cells even if background
            cells = [(r, c) for r in range(r1, r2 + 1) for c in range(c1, c2 + 1)]
        return cls.from_cells(grid, cells)

    @classmethod
    def from_mask(cls, grid, mask, center_r=None, center_c=None):
        """Extract from a boolean mask. Optionally specify center."""
        g = np.array(grid)
        m = np.array(mask)
        cells = list(zip(*np.where(m)))
        if center_r is not None and center_c is not None:
            pixels = [(r - center_r, c - center_c, int(g[r, c])) for r, c in cells]
            return cls(pixels)
        return cls.from_cells(grid, cells)

    @classmethod
    def from_pattern(cls, pattern, bg=0, center=None):
        """Create shape from a small grid (list of lists). bg cells are transparent.

        center: (r, c) within the pattern to use as origin.
                Defaults to geometric center.

        Examples:
            # L-shape, center at corner
            Shape.from_pattern([
                [1, 0],
                [1, 0],
                [1, 1],
            ], center=(2, 0))

            # Plus/cross, center auto
            Shape.from_pattern([
                [0, 1, 0],
                [1, 1, 1],
                [0, 1, 0],
            ])

            # Custom with colors
            Shape.from_pattern([
                [0, 2, 0],
                [2, 3, 2],
                [0, 2, 0],
            ])
        """
        rows = len(pattern)
        cols = len(pattern[0]) if rows else 0
        if center is not None:
            cr, cc = center
        else:
            cr = rows // 2
            cc = cols // 2
        pixels = []
        for r in range(rows):
            for c in range(cols):
                if pattern[r][c] != bg:
                    pixels.append((r - cr, c - cc, pattern[r][c]))
        return cls(pixels)

    @classmethod
    def define(cls, text, color=1, center_char="X", bg_char="."):
        """Define a shape from ASCII art. X marks the center.

        Examples:
            # T-shape with center at junction
            Shape.define('''
                ###
                .X.
            ''')

            # Arrow pointing right
            Shape.define('''
                .#
                X#
                .#
            ''')

            # Diamond
            Shape.define('''
                .#.
                #X#
                .#.
            ''')
        """
        lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
        if not lines:
            return cls([])

        # Find center (X)
        cr, cc = None, None
        for r, line in enumerate(lines):
            for c, ch in enumerate(line):
                if ch == center_char:
                    cr, cc = r, c
                    break
            if cr is not None:
                break

        if cr is None:
            # No center marker — use geometric center
            cr = len(lines) // 2
            cc = max(len(l) for l in lines) // 2

        pixels = []
        for r, line in enumerate(lines):
            for c, ch in enumerate(line):
                if ch != bg_char and ch != center_char:
                    pixels.append((r - cr, c - cc, color))
                elif ch == center_char:
                    pixels.append((r - cr, c - cc, color))  # center is also a pixel

        return cls(pixels)

    # ============================================================
    # Properties
    # ============================================================

    @property
    def height(self):
        if not self.pixels:
            return 0
        rs = [p[0] for p in self.pixels]
        return max(rs) - min(rs) + 1

    @property
    def width(self):
        if not self.pixels:
            return 0
        cs = [p[1] for p in self.pixels]
        return max(cs) - min(cs) + 1

    @property
    def size(self):
        return len(self.pixels)

    @property
    def colors(self):
        return sorted(set(p[2] for p in self.pixels))

    @property
    def bounds(self):
        """(min_dr, min_dc, max_dr, max_dc)"""
        rs = [p[0] for p in self.pixels]
        cs = [p[1] for p in self.pixels]
        return (min(rs), min(cs), max(rs), max(cs))

    # ============================================================
    # Rendering
    # ============================================================

    def as_grid(self, bg=0):
        """Render to a minimal grid."""
        if not self.pixels:
            return [[bg]]
        min_r, min_c, max_r, max_c = self.bounds
        h = max_r - min_r + 1
        w = max_c - min_c + 1
        grid = [[bg] * w for _ in range(h)]
        for dr, dc, color in self.pixels:
            grid[dr - min_r][dc - min_c] = color
        return grid

    def print(self, bg=0):
        """Compact display."""
        g = self.as_grid(bg)
        for row in g:
            print(" ".join(f"{v:2d}" if v != bg else " ." for v in row))
        print(f"  [{self.height}x{self.width}, {self.size}px, colors={self.colors}]")

    def place(self, grid, center_r, center_c, transparent=0):
        """Place shape onto grid at (center_r, center_c). Returns new grid."""
        result = deepcopy(grid)
        h, w = len(result), len(result[0]) if result else 0
        for dr, dc, color in self.pixels:
            r, c = center_r + dr, center_c + dc
            if 0 <= r < h and 0 <= c < w:
                result[r][c] = color
        return result

    def place_topleft(self, grid, top_r, left_c, transparent=0):
        """Place shape with top-left corner at (top_r, left_c)."""
        min_r, min_c, _, _ = self.bounds
        return self.place(grid, top_r - min_r, left_c - min_c, transparent)

    # ============================================================
    # Transforms (return new Shape)
    # ============================================================

    def upscale(self, factor):
        """Scale up: each pixel becomes a factor×factor block."""
        new_pixels = []
        for dr, dc, color in self.pixels:
            for fr in range(factor):
                for fc in range(factor):
                    new_pixels.append((dr * factor + fr, dc * factor + fc, color))
        return Shape(new_pixels)

    def rotate_cw(self):
        """Rotate 90° clockwise: (dr, dc) → (dc, -dr)."""
        return Shape([(dc, -dr, c) for dr, dc, c in self.pixels])

    def rotate_ccw(self):
        """Rotate 90° counter-clockwise: (dr, dc) → (-dc, dr)."""
        return Shape([(-dc, dr, c) for dr, dc, c in self.pixels])

    def rotate_180(self):
        """Rotate 180°."""
        return Shape([(-dr, -dc, c) for dr, dc, c in self.pixels])

    def flip_lr(self):
        """Mirror left-right."""
        return Shape([(dr, -dc, c) for dr, dc, c in self.pixels])

    def flip_ud(self):
        """Mirror up-down."""
        return Shape([(-dr, dc, c) for dr, dc, c in self.pixels])

    def recolor(self, mapping):
        """Apply color mapping. mapping = {old_color: new_color}."""
        return Shape([(dr, dc, mapping.get(c, c)) for dr, dc, c in self.pixels])

    def recolor_all(self, color):
        """Set all pixels to one color."""
        return Shape([(dr, dc, color) for dr, dc, c in self.pixels])

    def translate(self, dr, dc):
        """Shift center."""
        return Shape([(r + dr, c + dc, color) for r, c, color in self.pixels])

    # ============================================================
    # Comparison
    # ============================================================

    def normalized(self):
        """Return shape with min offset at (0,0) for comparison."""
        if not self.pixels:
            return Shape([])
        min_r = min(p[0] for p in self.pixels)
        min_c = min(p[1] for p in self.pixels)
        return Shape(sorted([(r - min_r, c - min_c, color) for r, c, color in self.pixels]))

    def same_pattern(self, other, ignore_color=False):
        """Check if two shapes have the same pattern (ignoring position)."""
        a = self.normalized()
        b = other.normalized()
        if ignore_color:
            return (set((r, c) for r, c, _ in a.pixels) ==
                    set((r, c) for r, c, _ in b.pixels))
        return set(a.pixels) == set(b.pixels)

    def __repr__(self):
        return f"Shape({self.height}x{self.width}, {self.size}px, colors={self.colors})"
