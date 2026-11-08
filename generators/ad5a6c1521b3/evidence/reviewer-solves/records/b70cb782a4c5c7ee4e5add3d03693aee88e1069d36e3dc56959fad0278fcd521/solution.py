from collections import Counter, deque


def _components(grid, color):
    rows, cols = len(grid), len(grid[0])
    seen = set()
    found = []
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] != color or (r, c) in seen:
                continue
            comp = []
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                cr, cc = queue.popleft()
                comp.append((cr, cc))
                for nr, nc in ((cr - 1, cc), (cr + 1, cc),
                               (cr, cc - 1), (cr, cc + 1)):
                    if (0 <= nr < rows and 0 <= nc < cols
                            and (nr, nc) not in seen
                            and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            found.append(comp)
    return found


def solve(grid):
    """Consolidate repeated foreground colors around their winning component."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    counts = Counter(cell for row in grid for cell in row)
    background = max(counts, key=counts.get)
    result = [row[:] for row in grid]
    colors = sorted(color for color in counts if color != background)

    for color in colors:
        components = _components(grid, color)
        if len(components) < 2:
            continue

        # Prefer the largest component.  The visible equal-size example keeps
        # the component located farther down/right; top-left row+column is a
        # compact, translation-invariant expression of that tie break.
        def winner_key(component):
            min_row = min(r for r, _ in component)
            min_col = min(c for _, c in component)
            return len(component), min_row + min_col

        winner = max(components, key=winner_key)
        min_row = min(r for r, _ in winner)
        max_row = max(r for r, _ in winner)
        min_col = min(c for _, c in winner)
        max_col = max(c for _, c in winner)

        # Remove every old component of this color, then replace the winner by
        # its solid bounding rectangle plus one additional column on the left.
        for r in range(len(grid)):
            for c in range(len(grid[0])):
                if result[r][c] == color:
                    result[r][c] = background
        for r in range(min_row, max_row + 1):
            for c in range(max(0, min_col - 1), max_col + 1):
                result[r][c] = color

    return result
