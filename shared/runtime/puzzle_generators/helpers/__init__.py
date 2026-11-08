"""Helper library for puzzle-instance generators.

These are pure-Python grid construction primitives. None of them call
into the Racket bridge — that's the runner's job. Helpers grow lazily:
add a function only when 2+ generators want it.

This `__init__` curates the most-frequently-imported helpers (~20 of
the 126 public-ish across the submodules). Anything else, import from
the submodule directly:

    from puzzle_generators.helpers.grid import dmirror, occurrences
    from puzzle_generators.helpers.indices import center_of_mass

The curated set is intentionally small. Adding to it should require
the same bar as adding a helper itself: 2+ generators using it from
this top-level path. See `docs/HELPERS.md` for the full grouped index.
"""

# Construction + the two canonical rect helpers (corner-pair) most
# generators use first.
from .grid import (
    full_grid,
    clone_grid,
    is_well_formed,
    fill_box,
    draw_frame,
    paint_at,
    paint_cells,
)

# Named shape constants — appear in dozens of generators.
from .shape import (
    L_TROMINO_NE,
    L_TROMINO_NW,
    L_TROMINO_SE,
    L_TROMINO_SW,
    L_TROMINOES,
    SQUARE_2X2,
    PLUS_5,
    H_LINE_3,
    V_LINE_3,
    T_TETROMINO,
    RING_3X3,
    CARDINAL_DELTAS,
    DIAGONAL_DELTAS,
    ALL_8_DELTAS,
)

# Placement primitives — random_palette + the two random-cell helpers.
from .place import (
    random_position,
    random_free_cell,
    place_no_overlap,
)
from .palette import (
    random_palette,
    non_bg_colors,
)

# Multi-blob layout (used by ~half of multi-component generators).
from .blobs import (
    grow_blob,
    bbox_overlaps,
)


__all__ = [
    # grid (drawing + invariants)
    "full_grid", "clone_grid", "is_well_formed",
    "fill_box", "draw_frame", "paint_at", "paint_cells",
    # shape (constants)
    "L_TROMINO_NE", "L_TROMINO_NW", "L_TROMINO_SE", "L_TROMINO_SW", "L_TROMINOES",
    "SQUARE_2X2", "PLUS_5", "H_LINE_3", "V_LINE_3", "T_TETROMINO", "RING_3X3",
    "CARDINAL_DELTAS", "DIAGONAL_DELTAS", "ALL_8_DELTAS",
    # placement
    "random_position", "random_free_cell", "place_no_overlap",
    "random_palette", "non_bg_colors",
    # blobs
    "grow_blob", "bbox_overlaps",
]
