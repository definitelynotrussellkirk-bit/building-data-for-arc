from collections import Counter, deque


def _components(cells):
    remaining = set(cells)
    groups = []
    while remaining:
        start = remaining.pop()
        group = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for nxt in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if nxt in remaining:
                    remaining.remove(nxt)
                    group.add(nxt)
                    queue.append(nxt)
        groups.append(group)
    return groups


def solve(grid):
    height = len(grid)
    width = len(grid[0]) if height else 0
    counts = Counter(value for row in grid for value in row)
    background = counts.most_common(1)[0][0]
    non_background = [value for value in counts if value != background]
    if len(non_background) < 2:
        return [row[:] for row in grid]

    seam_color = min(non_background, key=lambda value: counts[value])
    occupied = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != background
    }
    output = [[background for _ in range(width)] for _ in range(height)]

    for object_cells in _components(occupied):
        seam = {cell for cell in object_cells if grid[cell[0]][cell[1]] == seam_color}
        body = object_cells - seam
        if not seam:
            for r, c in body:
                output[r][c] = grid[r][c]
            continue

        body_parts = _components(body)
        min_r = min(r for r, _ in object_cells)
        max_r = max(r for r, _ in object_cells)
        min_c = min(c for _, c in object_cells)
        max_c = max(c for _, c in object_cells)
        touches_top_bottom = (
            any(r == min_r for r, _ in seam)
            and any(r == max_r for r, _ in seam)
        )
        touches_left_right = (
            any(c == min_c for _, c in seam)
            and any(c == max_c for _, c in seam)
        )

        if touches_top_bottom and not touches_left_right:
            vertical_seam = True
        elif touches_left_right and not touches_top_bottom:
            vertical_seam = False
        else:
            row_span = max(r for r, _ in seam) - min(r for r, _ in seam)
            col_span = max(c for _, c in seam) - min(c for _, c in seam)
            vertical_seam = row_span >= col_span

        seam_row = sum(r for r, _ in seam) / len(seam)
        seam_col = sum(c for _, c in seam) / len(seam)
        for part in body_parts:
            mean_row = sum(r for r, _ in part) / len(part)
            mean_col = sum(c for _, c in part) / len(part)
            if vertical_seam:
                dr, dc = 0, (-1 if mean_col < seam_col else 1)
            else:
                dr, dc = (-1 if mean_row < seam_row else 1), 0
            for r, c in part:
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width:
                    output[nr][nc] = grid[r][c]

    return output
