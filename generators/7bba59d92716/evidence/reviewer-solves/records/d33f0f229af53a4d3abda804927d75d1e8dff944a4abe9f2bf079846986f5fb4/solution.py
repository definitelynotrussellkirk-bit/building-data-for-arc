from collections import deque


def _components(grid, color):
    h = len(grid)
    w = len(grid[0]) if h else 0
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = deque([(r, c)])
            seen.add((r, c))
            comp = []
            while q:
                rr, cc = q.popleft()
                comp.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append(comp)
    return out


def _is_straight_contiguous(comp):
    rows = {r for r, _ in comp}
    cols = {c for _, c in comp}
    if len(rows) == 1:
        ordered = sorted(c for _, c in comp)
        return ordered == list(range(ordered[0], ordered[-1] + 1))
    if len(cols) == 1:
        ordered = sorted(r for r, _ in comp)
        return ordered == list(range(ordered[0], ordered[-1] + 1))
    return False


def solve(grid):
    result = [row[:] for row in grid]
    components = _components(grid, 1)

    # The top horizontal 1-segment is the exemplar.  Match its shape under
    # rotation among the remaining monochrome-1 components.
    references = [
        comp
        for comp in components
        if any(r == 0 for r, _ in comp) and _is_straight_contiguous(comp)
    ]
    if not references:
        return result
    reference = min(references, key=lambda comp: min(c for _, c in comp))
    target_size = len(reference)
    reference_cells = set(reference)

    for comp in components:
        if set(comp) == reference_cells:
            continue
        if len(comp) != target_size or not _is_straight_contiguous(comp):
            continue
        rows = {r for r, _ in comp}
        if len(rows) == 1:
            ordered = sorted(comp, key=lambda p: p[1])
        else:
            ordered = sorted(comp, key=lambda p: p[0])
        r, c = ordered[len(ordered) // 2]
        result[r][c] = 2

    return result
