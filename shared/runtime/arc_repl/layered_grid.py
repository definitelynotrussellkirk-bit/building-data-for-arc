"""
LayeredGrid — ARC grids as stacks of 10 binary layers (one per color).

A LayeredGrid is 10 boolean masks stacked. Each layer[c] is a (H,W) binary
matrix indicating where color c appears.

This representation makes color-specific operations natural:
  - Select a color: lg.layer(3) → mask of green cells
  - Move a color: lg.shift_layer(1, dr=0, dc=2) → shift blue right 2
  - Swap colors: lg.swap_layers(2, 3) → swap red and green
  - Add pattern as color: lg.set_layer(5, mask) → set gray cells
  - Boolean ops on layers: AND, OR, NOT, dilate, erode
  - Flatten back to Grid: priority-based composition

Contract:
  - 10 layers, indexed 0-9 (matching ARC colors)
  - Each layer is (H, W) of {0, 1}
  - At most ONE layer is 1 at each position (the cell's color)
    - Exception: during construction/manipulation, overlaps allowed
    - flatten() resolves conflicts (highest color index wins, or explicit)
  - Layer 0 = background (cells with no other color)

Operations:
  - layer(c) → Mask
  - set_layer(c, mask) → new LayeredGrid
  - clear_layer(c) → new LayeredGrid
  - swap_layers(c1, c2) → new LayeredGrid
  - shift_layer(c, dr, dc) → new LayeredGrid
  - layer_and(c1, c2) → Mask (where both colors present — overlap)
  - layer_or(c1, c2) → Mask
  - flatten(priority="highest") → Grid
  - from_grid(grid) → LayeredGrid
  - apply_to_layer(c, fn) → new LayeredGrid (fn: Mask → Mask)
"""

import numpy as np
from copy import deepcopy


class LayeredGrid:
    """10-layer binary representation of an ARC grid."""

    __slots__ = ('layers', 'height', 'width')

    def __init__(self, height, width):
        self.height = height
        self.width = width
        self.layers = [np.zeros((height, width), dtype=np.int8) for _ in range(10)]

    @classmethod
    def from_grid(cls, grid):
        """Convert a standard grid (list-of-lists) to LayeredGrid."""
        g = np.array(grid)
        h, w = g.shape
        lg = cls(h, w)
        for c in range(10):
            lg.layers[c] = (g == c).astype(np.int8)
        return lg

    def to_grid(self, priority="highest"):
        """Flatten layers back to a standard grid.

        priority:
          "highest" — highest color index wins on overlap (default)
          "lowest"  — lowest non-zero color wins
          "last"    — layer 9 checked first, then 8, etc (same as highest)
          list      — explicit priority order, e.g. [3, 1, 2] = green wins over blue over red
        """
        result = np.zeros((self.height, self.width), dtype=int)

        if priority == "highest" or priority == "last":
            for c in range(10):
                result[self.layers[c] != 0] = c
        elif priority == "lowest":
            for c in range(9, -1, -1):
                result[self.layers[c] != 0] = c
        elif isinstance(priority, list):
            # Lower priority first, higher priority overwrites
            for c in reversed(priority):
                result[self.layers[c] != 0] = c
        return result.tolist()

    # ============================================================
    # Layer access
    # ============================================================

    def layer(self, color):
        """Get binary mask for a specific color."""
        return self.layers[color].copy()

    def set_layer(self, color, mask):
        """Set a color's layer to a mask. Returns new LayeredGrid."""
        lg = self._copy()
        lg.layers[color] = np.array(mask, dtype=np.int8)
        return lg

    def clear_layer(self, color):
        """Clear all cells of a color. Returns new LayeredGrid."""
        lg = self._copy()
        lg.layers[color] = np.zeros((self.height, self.width), dtype=np.int8)
        return lg

    # ============================================================
    # Color operations
    # ============================================================

    def swap_layers(self, c1, c2):
        """Swap two color layers."""
        lg = self._copy()
        lg.layers[c1], lg.layers[c2] = lg.layers[c2].copy(), lg.layers[c1].copy()
        return lg

    def recolor(self, src, dst):
        """Move all cells from layer src to layer dst."""
        lg = self._copy()
        lg.layers[dst] = lg.layers[dst] | lg.layers[src]
        lg.layers[src] = np.zeros((self.height, self.width), dtype=np.int8)
        return lg

    def recolor_map(self, mapping):
        """Apply {old: new} color mapping across layers."""
        lg = LayeredGrid(self.height, self.width)
        for c in range(10):
            target = mapping.get(c, c)
            lg.layers[target] = lg.layers[target] | self.layers[c]
        return lg

    # ============================================================
    # Spatial operations on individual layers
    # ============================================================

    def shift_layer(self, color, dr, dc, wrap=False):
        """Shift a single color's layer by (dr, dc)."""
        lg = self._copy()
        layer = self.layers[color]
        shifted = np.zeros_like(layer)
        h, w = self.height, self.width

        for r in range(h):
            for c in range(w):
                if layer[r, c]:
                    nr, nc = r + dr, c + dc
                    if wrap:
                        nr, nc = nr % h, nc % w
                    if 0 <= nr < h and 0 <= nc < w:
                        shifted[nr, nc] = 1

        lg.layers[color] = shifted
        return lg

    def apply_to_layer(self, color, fn):
        """Apply a mask→mask function to a specific layer."""
        lg = self._copy()
        mask = self.layers[color]
        new_mask = np.array(fn(mask.tolist()), dtype=np.int8)
        lg.layers[color] = new_mask
        return lg

    def rotate_layer(self, color, k=1):
        """Rotate a layer 90°×k clockwise."""
        lg = self._copy()
        lg.layers[color] = np.rot90(self.layers[color], -k).astype(np.int8)
        return lg

    def flip_layer(self, color, axis="lr"):
        """Flip a layer left-right or up-down."""
        lg = self._copy()
        if axis == "lr":
            lg.layers[color] = np.fliplr(self.layers[color]).astype(np.int8)
        elif axis == "ud":
            lg.layers[color] = np.flipud(self.layers[color]).astype(np.int8)
        return lg

    # ============================================================
    # Boolean layer operations
    # ============================================================

    def layer_and(self, c1, c2):
        """Mask where BOTH colors are present."""
        return (self.layers[c1] & self.layers[c2]).astype(np.int8)

    def layer_or(self, c1, c2):
        """Mask where EITHER color is present."""
        return (self.layers[c1] | self.layers[c2]).astype(np.int8)

    def layer_not(self, color):
        """Mask where color is NOT present."""
        return (1 - self.layers[color]).astype(np.int8)

    def any_color_mask(self):
        """Mask where ANY non-background color is present."""
        result = np.zeros((self.height, self.width), dtype=np.int8)
        for c in range(1, 10):
            result = result | self.layers[c]
        return result

    def no_color_mask(self):
        """Mask of background cells (no color)."""
        return 1 - self.any_color_mask()

    # ============================================================
    # LayeredGrid arithmetic
    # ============================================================

    def __add__(self, other):
        """LG1 + LG2: overlay (other's non-bg layers overwrite self's)."""
        if isinstance(other, LayeredGrid):
            lg = self._copy()
            other_active = other.any_color_mask()
            # Clear self where other has content
            for c in range(10):
                lg.layers[c] = lg.layers[c] & (~other_active).astype(np.int8)
            # Add other's layers
            for c in range(10):
                lg.layers[c] = lg.layers[c] | other.layers[c]
            return lg
        raise TypeError(f"Cannot add LayeredGrid and {type(other)}")

    def __sub__(self, other):
        """LG1 - LG2: remove (clear self wherever other has content)."""
        if isinstance(other, LayeredGrid):
            lg = self._copy()
            other_active = other.any_color_mask()
            for c in range(10):
                lg.layers[c] = lg.layers[c] & (~other_active).astype(np.int8)
            # Set background where cleared
            lg.layers[0] = lg.layers[0] | other_active
            return lg
        raise TypeError(f"Cannot subtract {type(other)} from LayeredGrid")

    def __mul__(self, other):
        """LG * mask: keep only where mask is 1. LG * int: upscale."""
        if isinstance(other, int):
            # Upscale
            lg = LayeredGrid(self.height * other, self.width * other)
            for c in range(10):
                lg.layers[c] = np.kron(self.layers[c],
                                       np.ones((other, other), dtype=np.int8))
            return lg
        if isinstance(other, np.ndarray) or isinstance(other, list):
            # Mask
            m = np.array(other, dtype=np.int8)
            lg = self._copy()
            for c in range(1, 10):  # don't mask background
                lg.layers[c] = lg.layers[c] & m
            # Recompute background
            lg.layers[0] = 1 - lg.any_color_mask()
            return lg
        raise TypeError(f"Cannot multiply LayeredGrid by {type(other)}")

    # ============================================================
    # Utilities
    # ============================================================

    def _copy(self):
        lg = LayeredGrid(self.height, self.width)
        lg.layers = [l.copy() for l in self.layers]
        return lg

    def colors_present(self):
        """Set of colors that appear in the grid."""
        return {c for c in range(10) if self.layers[c].any()}

    def color_count(self, color):
        """Count cells of a specific color."""
        return int(self.layers[color].sum())

    def cell_at(self, r, c):
        """Get color at position (r, c)."""
        for color in range(9, -1, -1):
            if self.layers[color][r, c]:
                return color
        return 0

    def __repr__(self):
        colors = self.colors_present() - {0}
        return f"LayeredGrid({self.height}x{self.width}, colors={sorted(colors)})"

    def __eq__(self, other):
        if isinstance(other, LayeredGrid):
            return all(np.array_equal(a, b) for a, b in zip(self.layers, other.layers))
        return False

    # ============================================================
    # LayerMask — select across multiple layers as one unit
    # ============================================================

    def select(self, colors):
        """Select a group of colors as a combined mask.

        colors: list of ints, or callable(color) -> bool

        Returns a LayerMask (combined binary mask + the source colors).
        """
        if callable(colors):
            color_list = [c for c in range(10) if colors(c)]
        else:
            color_list = list(colors)

        combined = np.zeros((self.height, self.width), dtype=np.int8)
        for c in color_list:
            combined = combined | self.layers[c]

        return LayerMask(combined, color_list, self)

    def select_all(self):
        """Select all non-background colors."""
        return self.select(lambda c: c > 0)

    # ============================================================
    # Movement with collision detection
    # ============================================================

    def move_layer(self, color, dr, dc, collision="overwrite", blocker=None):
        """Move a color layer with collision handling.

        collision modes:
          "overwrite"  — moving color overwrites whatever is there
          "block"      — stop before hitting any non-bg cell (or blocker colors)
          "behind"     — move but go behind existing content (don't overwrite)
          "destroy"    — on collision, BOTH cells become bg

        blocker: set of colors that block movement (default: all non-bg non-self).
                 Only used with "block" mode.

        Returns new LayeredGrid.
        """
        if collision == "overwrite":
            return self.shift_layer(color, dr, dc)

        lg = self._copy()
        layer = self.layers[color]
        h, w = self.height, self.width

        if blocker is None:
            blocker = set(range(10)) - {0, color}

        if collision == "block":
            # Find the blocking mask
            block_mask = np.zeros((h, w), dtype=np.int8)
            for bc in blocker:
                block_mask = block_mask | self.layers[bc]

            # For each cell in the layer, check if destination is blocked
            new_layer = np.zeros_like(layer)
            for r in range(h):
                for c in range(w):
                    if layer[r, c]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w and not block_mask[nr, nc]:
                            new_layer[nr, nc] = 1
                        else:
                            new_layer[r, c] = 1  # stay in place

            lg.layers[color] = new_layer
            return lg

        elif collision == "behind":
            # Move but don't overwrite existing non-bg content
            existing = self.any_color_mask() & (~self.layers[color]).astype(np.int8)
            new_layer = np.zeros_like(layer)
            for r in range(h):
                for c in range(w):
                    if layer[r, c]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            if not existing[nr, nc]:
                                new_layer[nr, nc] = 1
                            else:
                                new_layer[nr, nc] = 1  # behind: still place but will be hidden
                        # Out of bounds: cell disappears

            lg.layers[color] = new_layer
            return lg

        elif collision == "destroy":
            existing = self.any_color_mask() & (~self.layers[color]).astype(np.int8)
            new_layer = np.zeros_like(layer)
            for r in range(h):
                for c in range(w):
                    if layer[r, c]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < h and 0 <= nc < w:
                            if existing[nr, nc]:
                                # Collision: destroy both
                                for bc in range(10):
                                    lg.layers[bc][nr, nc] = 0
                                # Don't place the moving cell either
                            else:
                                new_layer[nr, nc] = 1

            lg.layers[color] = new_layer
            return lg

        return lg

    def gravity_layer(self, color, direction="down", collision="block", blocker=None):
        """Apply gravity to a single color layer.

        Each cell of the color slides in `direction` until hitting
        an obstacle or the grid edge.

        direction: "down", "up", "left", "right"
        collision: only "block" is currently implemented (cells stop
                   before obstacles). Other modes use block behavior.
        blocker: set of colors that block movement (default: all non-bg non-self).
        """
        dr, dc = {"down": (1,0), "up": (-1,0), "left": (0,-1), "right": (0,1)}[direction]

        lg = self._copy()
        layer = self.layers[color]
        h, w = self.height, self.width

        if blocker is None:
            blocker = set(range(10)) - {0, color}

        block_mask = np.zeros((h, w), dtype=np.int8)
        for bc in blocker:
            block_mask = block_mask | self.layers[bc]

        # Process cells in the right order (bottom-up for down gravity, etc.)
        cells = list(zip(*np.where(layer != 0)))
        if dr > 0:
            cells.sort(key=lambda p: -p[0])  # bottom first
        elif dr < 0:
            cells.sort(key=lambda p: p[0])   # top first
        elif dc > 0:
            cells.sort(key=lambda p: -p[1])  # right first
        elif dc < 0:
            cells.sort(key=lambda p: p[1])   # left first

        new_layer = np.zeros_like(layer)
        occupied = block_mask.copy()  # track where things have settled

        for r, c in cells:
            nr, nc = r, c
            while True:
                nnr, nnc = nr + dr, nc + dc
                if not (0 <= nnr < h and 0 <= nnc < w):
                    break  # hit grid edge
                if occupied[nnr, nnc]:
                    break  # hit obstacle
                nr, nc = nnr, nnc

            new_layer[nr, nc] = 1
            occupied[nr, nc] = 1

        lg.layers[color] = new_layer
        return lg


class LayerMask:
    """A selection across multiple layers — operable as a unit.

    Created by LayeredGrid.select(). Holds the combined mask
    and knows which colors are selected.
    """

    __slots__ = ('mask', 'colors', 'source')

    def __init__(self, mask, colors, source):
        self.mask = mask          # (H, W) binary
        self.colors = colors      # list of selected color indices
        self.source = source      # the LayeredGrid this came from

    def count(self):
        return int(self.mask.sum())

    def positions(self):
        """List of [r, c] positions in the selection."""
        return [[int(r), int(c)] for r, c in zip(*np.where(self.mask != 0))]

    def bbox(self):
        """Bounding box (r1, c1, r2, c2) of the selection."""
        pos = np.argwhere(self.mask != 0)
        if len(pos) == 0:
            return None
        return (int(pos[:,0].min()), int(pos[:,1].min()),
                int(pos[:,0].max()), int(pos[:,1].max()))

    def to_mask(self):
        """Get the raw binary mask."""
        return self.mask.tolist()

    def move(self, dr, dc, collision="block"):
        """Move the entire selection as a unit."""
        lg = self.source._copy()
        for c in self.colors:
            lg = lg.move_layer(c, dr, dc, collision)
        return lg

    def remove(self):
        """Remove all selected cells (set to bg)."""
        lg = self.source._copy()
        for c in self.colors:
            lg.layers[c] = lg.layers[c] & (~self.mask).astype(np.int8)
        return lg

    def recolor(self, new_color):
        """Recolor all selected cells to new_color."""
        lg = self.source._copy()
        for c in self.colors:
            affected = lg.layers[c] & self.mask
            lg.layers[c] = lg.layers[c] & (~self.mask).astype(np.int8)
            lg.layers[new_color] = lg.layers[new_color] | affected
        return lg

    def __and__(self, other):
        """Intersection of two LayerMasks."""
        if isinstance(other, LayerMask):
            combined = (self.mask & other.mask).astype(np.int8)
            colors = list(set(self.colors) | set(other.colors))
            return LayerMask(combined, colors, self.source)
        return NotImplemented

    def __or__(self, other):
        """Union of two LayerMasks."""
        if isinstance(other, LayerMask):
            combined = (self.mask | other.mask).astype(np.int8)
            colors = list(set(self.colors) | set(other.colors))
            return LayerMask(combined, colors, self.source)
        return NotImplemented

    def __invert__(self):
        """Invert the mask."""
        return LayerMask((1 - self.mask).astype(np.int8), self.colors, self.source)

    def __repr__(self):
        return f"LayerMask(colors={self.colors}, cells={self.count()})"
