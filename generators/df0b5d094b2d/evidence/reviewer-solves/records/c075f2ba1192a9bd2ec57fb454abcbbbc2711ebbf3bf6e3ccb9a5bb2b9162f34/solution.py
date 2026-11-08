from collections import Counter, deque


def _component(grid, start, color):
    """Return the 4-connected component of *color* containing *start*."""
    h, w = len(grid), len(grid[0])
    todo = deque([start])
    seen = {start}
    while todo:
        r, c = todo.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (
                0 <= nr < h
                and 0 <= nc < w
                and (nr, nc) not in seen
                and grid[nr][nc] == color
            ):
                seen.add((nr, nc))
                todo.append((nr, nc))
    return seen


def solve(grid):
    """Complete each marked rectangle and move it one step toward its 8-corner."""
    h, w = len(grid), len(grid[0])
    background = Counter(cell for row in grid for cell in row).most_common(1)[0][0]
    marker = 8

    markers = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == marker
    ]

    rectangles = []
    used_components = set()

    for mr, mc in markers:
        candidate_colors = []
        for dr, dc in (
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ):
            nr, nc = mr + dr, mc + dc
            if 0 <= nr < h and 0 <= nc < w:
                color = grid[nr][nc]
                if color not in (background, marker) and color not in candidate_colors:
                    candidate_colors.append(color)

        matches = []
        for color in candidate_colors:
            starts = []
            for dr, dc in (
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1),
                (-1, -1),
                (-1, 1),
                (1, -1),
                (1, 1),
            ):
                nr, nc = mr + dr, mc + dc
                if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color:
                    starts.append((nr, nc))
            if not starts:
                continue

            component = _component(grid, starts[0], color)
            key = (color, frozenset(component))
            if key in used_components:
                continue

            cells = set(component)
            cells.add((mr, mc))
            min_r = min(r for r, _ in cells)
            max_r = max(r for r, _ in cells)
            min_c = min(c for _, c in cells)
            max_c = max(c for _, c in cells)
            corners = {
                (min_r, min_c),
                (min_r, max_c),
                (max_r, min_c),
                (max_r, max_c),
            }
            area = (max_r - min_r + 1) * (max_c - min_c + 1)
            if (mr, mc) not in corners or area != len(component) + 1:
                continue

            if any(
                grid[r][c] not in (color, marker)
                for r in range(min_r, max_r + 1)
                for c in range(min_c, max_c + 1)
            ):
                continue
            if sum(
                grid[r][c] == marker
                for r in range(min_r, max_r + 1)
                for c in range(min_c, max_c + 1)
            ) != 1:
                continue

            orthogonal_contacts = sum(
                0 <= mr + dr < h
                and 0 <= mc + dc < w
                and grid[mr + dr][mc + dc] == color
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            )
            matches.append(
                (
                    orthogonal_contacts,
                    area,
                    color,
                    component,
                    min_r,
                    max_r,
                    min_c,
                    max_c,
                )
            )

        if not matches:
            continue
        _, _, color, component, min_r, max_r, min_c, max_c = max(matches)
        used_components.add((color, frozenset(component)))

        dr = -1 if mr == min_r else 1
        dc = -1 if mc == min_c else 1
        rectangles.append((color, min_r + dr, max_r + dr, min_c + dc, max_c + dc))

    result = [row[:] for row in grid]
    for r in range(h):
        for c in range(w):
            if result[r][c] != background:
                result[r][c] = background

    for color, min_r, max_r, min_c, max_c in rectangles:
        for r in range(min_r, max_r + 1):
            for c in range(min_c, max_c + 1):
                if 0 <= r < h and 0 <= c < w:
                    result[r][c] = color

    return result
