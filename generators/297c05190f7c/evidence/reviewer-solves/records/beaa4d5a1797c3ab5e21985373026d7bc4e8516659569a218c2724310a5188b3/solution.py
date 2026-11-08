from collections import defaultdict


def solve(grid):
    """Complete every monochromatic 2x2 block missing exactly one corner.

    The completion is applied repeatedly because one repaired corner can expose
    another three-corner block (for example, an L-shaped rectangle border).
    Existing nonzero cells are never overwritten.  Ambiguous cells proposed by
    different colors in the same round are left unchanged.
    """
    out = [row[:] for row in grid]
    height = len(out)
    width = len(out[0]) if height else 0

    while True:
        proposals = defaultdict(set)

        for row in range(height - 1):
            for col in range(width - 1):
                cells = (
                    (row, col),
                    (row, col + 1),
                    (row + 1, col),
                    (row + 1, col + 1),
                )
                values = [out[r][c] for r, c in cells]
                zero_positions = [i for i, value in enumerate(values) if value == 0]
                if len(zero_positions) != 1:
                    continue

                present = [value for value in values if value != 0]
                if len(present) == 3 and present[0] == present[1] == present[2]:
                    missing = cells[zero_positions[0]]
                    proposals[missing].add(present[0])

        updates = {
            position: next(iter(colors))
            for position, colors in proposals.items()
            if len(colors) == 1 and out[position[0]][position[1]] == 0
        }
        if not updates:
            return out

        for (row, col), color in updates.items():
            out[row][col] = color
