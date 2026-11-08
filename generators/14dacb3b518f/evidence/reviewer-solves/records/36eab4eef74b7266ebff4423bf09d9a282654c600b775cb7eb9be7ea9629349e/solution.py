from __future__ import annotations


_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            color = grid[start_row][start_col]
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in _DIR4:
                    nr, nc = row + dr, col + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append(cells)
    return result


def _has_enclosed_hole(cells):
    min_row = min(row for row, _ in cells)
    max_row = max(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    max_col = max(col for _, col in cells)
    height = max_row - min_row + 1
    width = max_col - min_col + 1
    occupied = {(row - min_row, col - min_col) for row, col in cells}
    seen = set()

    for start_row in range(height):
        for start_col in range(width):
            start = (start_row, start_col)
            if start in occupied or start in seen:
                continue
            stack = [start]
            seen.add(start)
            touches_edge = False
            while stack:
                row, col = stack.pop()
                if row in (0, height - 1) or col in (0, width - 1):
                    touches_edge = True
                for dr, dc in _DIR4:
                    nr, nc = row + dr, col + dc
                    neighbor = (nr, nc)
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in occupied
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            if not touches_edge:
                return True
    return False


def solve(grid):
    output = [[0 for _ in row] for row in grid]
    for component in _components(grid):
        recolor = 8 if _has_enclosed_hole(component) else 2
        for row, col in component:
            output[row][col] = recolor
    return output
