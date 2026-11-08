"""Fresh episode solution using only standard-library geometry.

Earlier task-rule exposure occurred during generator review. During this solve
phase, only challenge.json was opened; no generator or reference was consulted.
"""
from collections import Counter


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Enlarge each colored L at the outer corner selected by its vertex."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError('expected a nonempty rectangular grid')
    height, width = len(grid), len(grid[0])
    if height != width or height % 2 != 1:
        raise ValueError('expected an odd square grid')
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    answer = [[background] * width for _ in range(height)]
    visited: set[tuple[int, int]] = set()
    occupied_corners: set[tuple[int, int]] = set()
    arm_length = height // 2
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == background or (row, col) in visited:
                continue
            component = {(row, col)}
            stack = [(row, col)]
            visited.add((row, col))
            while stack:
                y, x = stack.pop()
                for yy, xx in ((y-1, x), (y+1, x), (y, x-1), (y, x+1)):
                    if (0 <= yy < height and 0 <= xx < width
                            and (yy, xx) not in visited and grid[yy][xx] == color):
                        component.add((yy, xx))
                        visited.add((yy, xx))
                        stack.append((yy, xx))
            ymin = min(y for y, _ in component)
            ymax = max(y for y, _ in component)
            xmin = min(x for _, x in component)
            xmax = max(x for _, x in component)
            if len(component) != 3 or ymax-ymin != 1 or xmax-xmin != 1:
                raise ValueError('foreground component is not a 2-by-2 L triomino')
            vertices = [(y, x) for y, x in component
                        if sum((yy, xx) in component for yy, xx in
                               ((y-1, x), (y+1, x), (y, x-1), (y, x+1))) == 2]
            if len(vertices) != 1:
                raise ValueError('ambiguous L vertex')
            vy, vx = vertices[0]
            bottom, right = int(vy == ymax), int(vx == xmax)
            corner = (bottom, right)
            if corner in occupied_corners:
                raise ValueError('multiple objects select the same corner')
            occupied_corners.add(corner)
            edge_row = height-1 if bottom else 0
            edge_col = width-1 if right else 0
            dy = -1 if bottom else 1
            dx = -1 if right else 1
            for distance in range(arm_length):
                answer[edge_row][edge_col + dx*distance] = color
                answer[edge_row + dy*distance][edge_col] = color
    return answer
