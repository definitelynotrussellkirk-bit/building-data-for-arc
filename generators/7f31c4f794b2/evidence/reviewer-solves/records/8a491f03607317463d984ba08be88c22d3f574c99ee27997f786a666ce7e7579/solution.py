from copy import deepcopy


def solve(grid):
    """Recolor each nonzero 4-connected component that touches the border to 7."""
    if not grid or not grid[0]:
        return deepcopy(grid)

    h, w = len(grid), len(grid[0])
    out = deepcopy(grid)
    seen = set()

    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue

            stack = [(r, c)]
            seen.add((r, c))
            component = []
            touches_border = False

            while stack:
                rr, cc = stack.pop()
                component.append((rr, cc))
                if rr in (0, h - 1) or cc in (0, w - 1):
                    touches_border = True

                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))

            if touches_border:
                for rr, cc in component:
                    out[rr][cc] = 7

    return out
