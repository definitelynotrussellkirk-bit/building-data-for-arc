"""Visible-example solution for the generated 71e2e99645f4 episode."""


def solve(grid):
    """Classify each fixed 4-column section by its zero-cell signature."""
    starts = (0, 5, 10)
    classes = {
        frozenset(): 2,
        frozenset({(1, 1), (1, 2), (2, 1), (2, 2)}): 8,
        frozenset({(2, 1), (2, 2), (3, 1), (3, 2)}): 4,
        frozenset({(1, 0), (1, 3), (2, 0), (2, 3)}): 3,
    }
    output = []
    for start in starts:
        holes = frozenset(
            (row, col)
            for row in range(4)
            for col in range(4)
            if grid[row][start + col] == 0
        )
        if holes not in classes:
            raise ValueError(f"unrecognized section hole pattern: {sorted(holes)}")
        label = classes[holes]
        output.append([label, label, label])
    return output
