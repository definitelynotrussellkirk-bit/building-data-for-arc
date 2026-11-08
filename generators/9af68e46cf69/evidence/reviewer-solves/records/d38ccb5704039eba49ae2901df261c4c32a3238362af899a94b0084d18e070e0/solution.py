from collections import deque


def solve(grid):
    """Recolor each 4-connected 1-object that encloses a hole from 1 to 8."""
    height = len(grid)
    width = len(grid[0]) if height else 0
    out = [row[:] for row in grid]
    seen = set()
    directions = ((1, 0), (-1, 0), (0, 1), (0, -1))

    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] != 1 or (start_r, start_c) in seen:
                continue

            # Collect one 4-connected foreground object.
            component = set()
            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            while queue:
                r, c = queue.popleft()
                component.add((r, c))
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and grid[nr][nc] == 1
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            min_r = min(r for r, _ in component)
            max_r = max(r for r, _ in component)
            min_c = min(c for _, c in component)
            max_c = max(c for _, c in component)

            # Put a one-cell empty frame around the object's bounding box.  Flood
            # the complement from that frame while treating only this component
            # as a wall.  Any complement cell not reached is an enclosed cavity.
            local_h = max_r - min_r + 3
            local_w = max_c - min_c + 3
            walls = {(r - min_r + 1, c - min_c + 1) for r, c in component}
            exterior = set()
            queue = deque()

            for lr in range(local_h):
                for lc in (0, local_w - 1):
                    if (lr, lc) not in exterior:
                        exterior.add((lr, lc))
                        queue.append((lr, lc))
            for lc in range(local_w):
                for lr in (0, local_h - 1):
                    if (lr, lc) not in exterior:
                        exterior.add((lr, lc))
                        queue.append((lr, lc))

            while queue:
                lr, lc = queue.popleft()
                for dr, dc in directions:
                    nr, nc = lr + dr, lc + dc
                    if (
                        0 <= nr < local_h
                        and 0 <= nc < local_w
                        and (nr, nc) not in walls
                        and (nr, nc) not in exterior
                    ):
                        exterior.add((nr, nc))
                        queue.append((nr, nc))

            has_hole = any(
                (lr, lc) not in walls and (lr, lc) not in exterior
                for lr in range(1, local_h - 1)
                for lc in range(1, local_w - 1)
            )
            if has_hole:
                for r, c in component:
                    out[r][c] = 8

    return out
