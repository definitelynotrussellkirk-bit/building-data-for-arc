"""Visible-example solution for the blind ARC task.

The isolated cell at (0, 0) is an instruction.  The remaining non-zero
cells form a rectangular payload; crop it and apply the indicated dihedral
transform.
"""


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _rotate_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _anti_transpose(grid):
    """Reflect across the anti-diagonal (the paired diagonal transform)."""
    transposed = _transpose(grid)
    return [row[::-1] for row in transposed[::-1]]


def solve(grid):
    instruction = grid[0][0]

    # Exclude the isolated instruction pixel and crop the payload tightly.
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) != (0, 0)
    ]
    if not points:
        return []

    top = min(r for r, _ in points)
    bottom = max(r for r, _ in points)
    left = min(c for _, c in points)
    right = max(c for _, c in points)
    payload = [row[left : right + 1] for row in grid[top : bottom + 1]]

    transforms = {
        1: _rotate_cw,
        2: _rotate_180,
        3: _transpose,
        # Color 4 is absent from the demonstrations.  The least-assumptive
        # completion of the observed two rotations + one diagonal reflection
        # is the other diagonal reflection.
        4: _anti_transpose,
    }
    return transforms.get(instruction, lambda x: x)(payload)
