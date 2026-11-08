"""Visible-example solution; independent of authoring/runtime modules."""


def components(grid):
    remaining = {(r, c) for r, row in enumerate(grid)
                 for c, value in enumerate(row) if value != 0}
    bodies = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        body = {start}
        queue = [start]
        for r, c in queue:
            for cell in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if cell in remaining:
                    remaining.remove(cell)
                    body.add(cell)
                    queue.append(cell)
        bodies.append(body)
    return bodies


def perimeter(body):
    return sum(neighbor not in body for r, c in body
               for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)))


def solve(grid):
    bodies = components(grid)
    ranked = sorted(bodies, key=perimeter)
    output = [[0 for _ in row] for row in grid]
    for color, body in zip((2, 3, 4), ranked):
        for r, c in body:
            output[r][c] = color
    return output
