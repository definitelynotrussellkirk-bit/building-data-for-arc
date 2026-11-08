"""Blind solution inferred only from solve-blind/challenge.json."""


def solve(grid):
    """Drop color-1 objects toward the color-2 horizontal barrier.

    One-column-wide objects punch through the barrier and fall to the bottom;
    wider objects come to rest immediately above it.  A punched barrier cell
    becomes background, and a falling pixel that would finish in the barrier
    row is absent there.
    """
    out = [row[:] for row in grid]
    height = len(grid)
    width = len(grid[0])

    # The background is the most frequent color.  The barrier is the full
    # non-background row (color 2 in the visible lessons).
    counts = {}
    for row in grid:
        for value in row:
            counts[value] = counts.get(value, 0) + 1
    background = max(counts, key=counts.get)

    barrier_row = None
    barrier_color = None
    for r, row in enumerate(grid):
        if len(set(row)) == 1 and row[0] != background:
            barrier_row = r
            barrier_color = row[0]
            break
    if barrier_row is None:
        return out

    # The moving color is the remaining non-background/non-barrier color.
    moving_colors = {
        value
        for row in grid[:barrier_row]
        for value in row
        if value not in (background, barrier_color)
    }
    if not moving_colors:
        return out
    moving = min(moving_colors)

    # Four-connected components above the barrier.
    seen = set()
    components = []
    for r in range(barrier_row):
        for c in range(width):
            if grid[r][c] != moving or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            component = []
            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < barrier_row
                        and 0 <= nc < width
                        and grid[nr][nc] == moving
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(component)

    # Remove original objects before placing their fallen copies.
    for component in components:
        for r, c in component:
            out[r][c] = background

    for component in components:
        cols = {c for _, c in component}
        bottom = max(r for r, _ in component)
        penetrates = len(cols) == 1
        target_bottom = height - 1 if penetrates else barrier_row - 1
        shift = target_bottom - bottom

        if penetrates:
            for c in cols:
                out[barrier_row][c] = background

        for r, c in component:
            nr = r + shift
            # The barrier remains a gap where a narrow object passed through.
            if 0 <= nr < height and nr != barrier_row:
                out[nr][c] = moving

    return out
