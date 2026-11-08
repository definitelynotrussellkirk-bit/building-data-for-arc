from collections import deque


def solve(grid):
    """Mark where each asymmetric cross points through the outer frame.

    Every non-frame, non-background color forms one orthogonal cross.  One arm
    is longer than the other three; that arm is the tail.  The cross points in
    the opposite direction.  Put the object's color on the frame in the
    pointing direction and 0 on the frame behind its tail.
    """
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]

    # The examples consistently use the four corners for the frame color and
    # the most frequent interior value for the background.
    frame = grid[0][0]
    interior_counts = {}
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            value = grid[r][c]
            interior_counts[value] = interior_counts.get(value, 0) + 1
    background = max(interior_counts, key=interior_counts.get)

    seen = set()
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for start_r in range(1, h - 1):
        for start_c in range(1, w - 1):
            color = grid[start_r][start_c]
            if color in (frame, background) or (start_r, start_c) in seen:
                continue

            # Collect this same-color component without letting touching
            # differently colored crosses merge.
            component = []
            queue = deque([(start_r, start_c)])
            seen.add((start_r, start_c))
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))

            cells = set(component)
            # The cross centre is the unique cell with all four orthogonal
            # same-color neighbours.  The fallback makes the solver tolerate a
            # minimally clipped/noisy arm by choosing the strongest junction.
            centre = max(
                component,
                key=lambda p: sum((p[0] + dr, p[1] + dc) in cells for dr, dc in directions),
            )
            cr, cc = centre

            arm_lengths = []
            for dr, dc in directions:
                length = 0
                r, c = cr + dr, cc + dc
                while (r, c) in cells:
                    length += 1
                    r += dr
                    c += dc
                arm_lengths.append(length)

            tail_index = max(range(4), key=arm_lengths.__getitem__)
            tail_dr, tail_dc = directions[tail_index]
            point_dr, point_dc = -tail_dr, -tail_dc

            if point_dr < 0:
                out[0][cc] = color
                out[h - 1][cc] = 0
            elif point_dr > 0:
                out[h - 1][cc] = color
                out[0][cc] = 0
            elif point_dc < 0:
                out[cr][0] = color
                out[cr][w - 1] = 0
            else:
                out[cr][w - 1] = color
                out[cr][0] = 0

    return out
