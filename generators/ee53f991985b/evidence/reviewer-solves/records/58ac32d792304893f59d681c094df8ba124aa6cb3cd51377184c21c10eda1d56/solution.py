from __future__ import annotations


def solve(grid):
    """Fill the interiors of complete monochrome rectangular frames."""
    if not grid:
        return []

    height = len(grid)
    width = len(grid[0])
    out = [row[:] for row in grid]
    seen: set[tuple[int, int]] = set()

    for start_r in range(height):
        for start_c in range(width):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue

            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            component: set[tuple[int, int]] = set()

            while stack:
                r, c = stack.pop()
                component.add((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            rows = [r for r, _ in component]
            cols = [c for _, c in component]
            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)

            border = {
                (r, c)
                for r in range(top, bottom + 1)
                for c in range(left, right + 1)
                if r in (top, bottom) or c in (left, right)
            }
            if component != border:
                continue

            for r in range(top + 1, bottom):
                for c in range(left + 1, right):
                    if out[r][c] == 0:
                        out[r][c] = color

    return out
