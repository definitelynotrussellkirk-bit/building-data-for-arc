"""Visible-only solution for ARC task 42f19ef6d600."""

from collections import Counter, deque


def solve(grid):
    """Add a red extrapolated border around each nontrivial square component.

    The border is copied from the component's second-inward row/column: for a
    solid square this colors the whole outside edge; for a hollow square this
    colors only the positions supported by the parallel inner edge.
    """
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    output = [row[:] for row in grid]
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    seen = set()

    for start_r in range(height):
        for start_c in range(width):
            color = grid[start_r][start_c]
            if color == background or (start_r, start_c) in seen:
                continue

            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            component = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            rows = [r for r, _ in component]
            cols = [c for _, c in component]
            r0, r1 = min(rows), max(rows)
            c0, c1 = min(cols), max(cols)
            side = r1 - r0 + 1
            if side < 2 or side != c1 - c0 + 1:
                continue

            cells = set(component)

            # Extrapolate each edge from the parallel row/column one cell inward.
            if r0 > 0:
                for c in range(c0, c1 + 1):
                    if (r0 + 1, c) in cells and output[r0 - 1][c] == background:
                        output[r0 - 1][c] = 2
            if r1 + 1 < height:
                for c in range(c0, c1 + 1):
                    if (r1 - 1, c) in cells and output[r1 + 1][c] == background:
                        output[r1 + 1][c] = 2
            if c0 > 0:
                for r in range(r0, r1 + 1):
                    if (r, c0 + 1) in cells and output[r][c0 - 1] == background:
                        output[r][c0 - 1] = 2
            if c1 + 1 < width:
                for r in range(r0, r1 + 1):
                    if (r, c1 - 1) in cells and output[r][c1 + 1] == background:
                        output[r][c1 + 1] = 2

    return output
