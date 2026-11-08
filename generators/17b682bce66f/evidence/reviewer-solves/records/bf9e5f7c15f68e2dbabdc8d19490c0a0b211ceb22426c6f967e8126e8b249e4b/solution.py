"""Visible-example-only solution for the blind ARC episode."""


def _rotate(dr: int, dc: int, quarter_turns_clockwise: int) -> tuple[int, int]:
    """Rotate a row/column offset clockwise in screen coordinates."""
    for _ in range(quarter_turns_clockwise % 4):
        dr, dc = dc, -dr
    return dr, dc


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Stamp the 8-mask around each directional 2/3/4/5 anchor.

    The single 9 cell is the mask origin.  Anchor colors encode clockwise
    quarter-turns (2 -> 0, 3 -> 1, 4 -> 2, 5 -> 3), while stamped 8-cells
    become anchor_color + 2.  Later/higher anchor colors win overlaps, and
    all original anchors are restored after stamping.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [[0 for _ in range(width)] for _ in range(height)]

    origins = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if len(origins) != 1:
        # The visible task family has one origin; preserve the input rather
        # than guessing if a malformed instance violates that contract.
        return [row[:] for row in grid]

    origin_r, origin_c = origins[0]
    mask_offsets = [
        (r - origin_r, c - origin_c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8
    ]
    anchors = [
        (value, r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if 2 <= value <= 5
    ]

    # Ascending source color makes the corresponding ascending fill color
    # establish the observed overlap priority.
    for color, anchor_r, anchor_c in sorted(anchors):
        turns = color - 2
        fill = color + 2
        for dr, dc in mask_offsets:
            rr, cc = _rotate(dr, dc, turns)
            target_r, target_c = anchor_r + rr, anchor_c + cc
            if 0 <= target_r < height and 0 <= target_c < width:
                out[target_r][target_c] = fill

    # Colored anchors are immutable and override any overlapping stamp.
    for color, r, c in anchors:
        out[r][c] = color

    return out
