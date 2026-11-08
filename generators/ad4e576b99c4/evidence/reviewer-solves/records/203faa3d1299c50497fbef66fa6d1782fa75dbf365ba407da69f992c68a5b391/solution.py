"""Visible-example solution for the reviewer-authored ARC challenge."""


def solve(grid):
    """Move the color-5 stencil to the opposite edge and draw its wake."""
    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]

    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    if not cells:
        return out

    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    patch_width = right - left + 1
    patch_height = bottom - top + 1

    # The visible examples place the source stencil flush against one side.
    source_is_left = left == 0
    source_is_right = right == width - 1
    if source_is_left == source_is_right:
        raise ValueError("expected a color-5 stencil flush with exactly one edge")

    # Remove the source before placing an unchanged copy on the opposite side.
    for r, c in cells:
        out[r][c] = 1

    for r, c in cells:
        row_offset = r - top
        local_c = c - left
        inward_shift = max(0, row_offset - 2)
        if source_is_right:
            target_c = inward_shift + local_c
        else:
            target_c = width - patch_width - inward_shift + local_c
        out[r][target_c] = 5

    # The first color-6 row becomes a color-9 wake, stopping one step beyond
    # the final inward shift on the side toward which the stencil travelled.
    boundary = min(r for r, row in enumerate(grid) if 6 in row)
    final_shift = max(0, patch_height - 3)
    if source_is_right:
        for c in range(final_shift + 1, width):
            out[boundary][c] = 9
    else:
        for c in range(0, width - final_shift - 1):
            out[boundary][c] = 9

    return out
