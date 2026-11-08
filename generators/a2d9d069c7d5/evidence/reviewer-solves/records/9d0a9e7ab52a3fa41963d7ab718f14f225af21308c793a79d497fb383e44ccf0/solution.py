from collections import Counter, deque


def _is_five_cell_plus(cells):
    if len(cells) != 5:
        return False
    cell_set = set(cells)
    for r, c in cells:
        expected = {(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)}
        if cell_set == expected:
            return True
    return False


def solve(grid):
    """Stamp the marker color into the center of each odd-by-odd rectangle."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]

    height = len(grid)
    width = len(grid[0])
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]

    positions = {
        color: [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
        for color in counts
        if color != background
    }
    marker_candidates = [color for color, cells in positions.items() if _is_five_cell_plus(cells)]
    if marker_candidates:
        marker = marker_candidates[0]
    else:
        # Visible examples always contain a five-cell plus. This fallback keeps the
        # program deterministic if a malformed query reaches it.
        marker = min(positions, key=lambda color: (len(positions[color]), color))

    result = [row[:] for row in grid]
    seen = set()
    for color in positions:
        if color == marker:
            continue
        for start in positions[color]:
            if start in seen:
                continue
            queue = deque([start])
            seen.add(start)
            component = []
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
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
            box_height = r1 - r0 + 1
            box_width = c1 - c0 + 1
            is_filled_rectangle = len(component) == box_height * box_width
            if is_filled_rectangle and box_height % 2 == 1 and box_width % 2 == 1:
                result[(r0 + r1) // 2][(c0 + c1) // 2] = marker

    return result
