"""Blind solution inferred only from the visible examples."""


def solve(grid):
    """Propagate each bottom-row 2 upward, sidestepping right around 5s.

    A beam advances one cell upward through non-5 cells.  When the cell directly
    above is a 5, it moves one cell right on its current row and then resumes
    upward.  A beam stops when that one-cell right move is outside the grid or
    occupied by a 5.  Existing colors are preserved; traversed zero cells become
    2.  Painted 2 paths may be shared by multiple beams.
    """
    out = [row[:] for row in grid]
    if not out or not out[0]:
        return out

    height = len(out)
    width = len(out[0])
    starts = [c for c, value in enumerate(grid[-1]) if value == 2]

    for c in starts:
        r = height - 1
        while r > 0:
            if out[r - 1][c] != 5:
                r -= 1
                if out[r][c] == 0:
                    out[r][c] = 2
                continue

            # The beam is blocked above: make exactly one rightward step on
            # the current row.  If that cell is unavailable, this beam ends.
            next_c = c + 1
            if next_c >= width or out[r][next_c] == 5:
                break
            c = next_c
            if out[r][c] == 0:
                out[r][c] = 2

    return out
