from collections import Counter


def solve(grid):
    """Return the non-background panel with the fewest non-base-color cells."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    nonzero = [value for row in grid for value in row if value != 0]
    if not nonzero:
        return []
    base_color = Counter(nonzero).most_common(1)[0][0]

    seen = set()
    candidates = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            component = []
            while stack:
                r, c = stack.pop()
                component.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 0
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            rows = [r for r, _ in component]
            cols = [c for _, c in component]
            top, bottom = min(rows), max(rows)
            left, right = min(cols), max(cols)
            crop = [source_row[left : right + 1] for source_row in grid[top : bottom + 1]]
            exceptions = sum(value != base_color for source_row in crop for value in source_row)
            area = len(crop) * len(crop[0])
            candidates.append((exceptions, -area, top, left, crop))

    return min(candidates, key=lambda item: item[:4])[4]
