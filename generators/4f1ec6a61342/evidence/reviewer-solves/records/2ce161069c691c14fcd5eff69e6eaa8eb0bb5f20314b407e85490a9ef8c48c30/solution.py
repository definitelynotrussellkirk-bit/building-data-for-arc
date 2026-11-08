from collections import deque


def solve(grid):
    """Fill the gray-walled region whose blue-cell count matches the corner key."""
    height = len(grid)
    width = len(grid[0])
    key = grid[0][0]

    seen = set()
    regions = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == 5 or (start_r, start_c) in seen:
                continue
            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            region = []
            while queue:
                r, c = queue.popleft()
                region.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] != 5
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            regions.append(region)

    target = None
    for region in regions:
        # A non-gray key is an isolated component at the corner, not a room.
        if (0, 0) in region:
            continue
        blue_count = sum(grid[r][c] == 2 for r, c in region)
        if blue_count == key:
            target = region
            break

    out = [[5 if grid[r][c] == 5 else 0 for c in range(width)] for r in range(height)]
    if target is not None:
        for r, c in target:
            out[r][c] = 8
    return out
