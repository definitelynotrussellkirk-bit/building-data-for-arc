"""Sequential geometric interpretation of the visible transform-script examples."""


def solve(grid):
    cells = [(r, c) for r in range(1, len(grid))
             for c, value in enumerate(grid[r]) if value != 0]
    if not cells:
        raise ValueError("No body to transform")
    top, bottom = min(r for r, c in cells), max(r for r, c in cells)
    left, right = min(c for r, c in cells), max(c for r, c in cells)
    result = [row[left:right + 1] for row in grid[top:bottom + 1]]
    for code in grid[0]:
        if code == 0:
            continue
        if code == 1:
            result = [list(row) for row in zip(*result[::-1])]
        elif code == 2:
            result = [row[::-1] for row in result]
        elif code == 3:
            result = [row[::-1] for row in result[::-1]]
        elif code == 4:
            result = result[::-1]
        else:
            raise ValueError("Unexplained instruction")
    return result
