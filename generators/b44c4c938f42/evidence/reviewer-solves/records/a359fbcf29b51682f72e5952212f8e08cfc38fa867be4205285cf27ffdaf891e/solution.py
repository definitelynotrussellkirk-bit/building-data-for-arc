"""Fresh Python solution for the visible post-repair challenge.

Earlier rule exposure is declared in the solve record. This module uses no
generator, reference implementation, hidden answer or external dependency.
"""


def solve(grid):
    height, width = len(grid), len(grid[0])
    dividers = [c for c in range(width)
                if all(grid[r][c] == 0 for r in range(height))]
    starts = [0] + [c + 1 for c in dividers]
    ends = dividers + [width]
    selected = []
    panel_width = ends[0] - starts[0]
    for start, end in zip(starts, ends):
        unseen = {(r, c - start) for r in range(height)
                  for c in range(start, end) if grid[r][c] != 8}
        components = []
        while unseen:
            initial = min(unseen)
            color = grid[initial[0]][initial[1] + start]
            unseen.remove(initial)
            component = [initial]
            frontier = [initial]
            while frontier:
                r, c = frontier.pop()
                for neighbor in ((r - 1, c), (r + 1, c),
                                 (r, c - 1), (r, c + 1)):
                    if (neighbor in unseen and
                            grid[neighbor[0]][neighbor[1] + start] == color):
                        unseen.remove(neighbor)
                        frontier.append(neighbor)
                        component.append(neighbor)
            components.append((color, component))
        selected.append(max(components, key=lambda item: len(item[1])))

    selected.sort(key=lambda item: len(item[1]), reverse=True)
    shifts = ((0, 0), (0, -1), (0, 1), (-1, 0), (1, 0),
              (-1, -1), (-1, 1), (1, -1), (1, 1),
              (0, -2), (0, 2), (-2, 0), (2, 0))
    result = [[8] * panel_width for _ in range(height)]
    for color, cells in selected:
        for dr, dc in shifts:
            placed = [(r + dr, c + dc) for r, c in cells]
            if all(0 <= r < height and 0 <= c < panel_width and
                   result[r][c] == 8 for r, c in placed):
                for r, c in placed:
                    result[r][c] = color
                break
    return result
