def solve(grid):
    """Extend each panel's visible motif periodically, preserving its phase."""
    if not grid or not grid[0]:
        return [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    border = grid[0][0]
    answer = [list(row) for row in grid]
    seen = set()
    for row in range(height):
        for col in range(width):
            if grid[row][col] == border or (row, col) in seen:
                continue
            panel = []
            pending = [(row, col)]
            seen.add((row, col))
            while pending:
                r, c = pending.pop()
                panel.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if (0 <= rr < height and 0 <= cc < width
                            and grid[rr][cc] != border and (rr, cc) not in seen):
                        seen.add((rr, cc))
                        pending.append((rr, cc))
            ink = [(r, c) for r, c in panel if grid[r][c] != 0]
            if not ink:
                continue
            top = min(r for r, _ in ink)
            left = min(c for _, c in ink)
            motif_height = max(r for r, _ in ink) - top + 1
            motif_width = max(c for _, c in ink) - left + 1
            for r, c in panel:
                answer[r][c] = grid[top + (r - top) % motif_height][
                    left + (c - left) % motif_width]
    return answer
