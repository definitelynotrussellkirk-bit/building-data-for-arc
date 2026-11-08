"""Visible-example solution for the generated arrow-sweep puzzle."""

DIRS = {
    1: (-1, 0),
    2: (0, 1),
    3: (1, 0),
    4: (0, -1),
}


def solve(grid):
    h = len(grid)
    w = len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    seen = set()

    for r0 in range(h):
        for c0 in range(w):
            color = grid[r0][c0]
            if color < 5 or (r0, c0) in seen:
                continue

            # Collect the 4-connected same-color object.
            stack = [(r0, c0)]
            seen.add((r0, c0))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in DIRS.values():
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            # The adjacent small digit is a direction code:
            # 1=up, 2=right, 3=down, 4=left.
            code = None
            for r, c in cells:
                for dr, dc in DIRS.values():
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] in DIRS:
                        code = grid[nr][nc]
                        break
                if code is not None:
                    break
            if code is None:
                raise ValueError("object has no adjacent direction code")

            dr, dc = DIRS[code]
            for r, c in cells:
                while 0 <= r < h and 0 <= c < w:
                    out[r][c] = color
                    r += dr
                    c += dc

    return out
