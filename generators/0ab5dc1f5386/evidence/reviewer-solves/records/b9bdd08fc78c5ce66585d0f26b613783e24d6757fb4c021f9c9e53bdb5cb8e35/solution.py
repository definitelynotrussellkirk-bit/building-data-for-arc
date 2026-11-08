from collections import deque


def _components(grid, predicate):
    """Return 4-connected components whose cells satisfy predicate(value)."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    out = []
    for r in range(h):
        for c in range(w):
            if seen[r][c] or not predicate(grid[r][c]):
                continue
            seen[r][c] = True
            q = deque([(r, c)])
            cells = []
            while q:
                rr, cc = q.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and not seen[nr][nc]
                        and predicate(grid[nr][nc])
                    ):
                        seen[nr][nc] = True
                        q.append((nr, nc))
            out.append(cells)
    return out


def _bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    return min(rs), min(cs), max(rs), max(cs)


def _is_hollow_azure_frame(grid, box, cells):
    r0, c0, r1, c1 = box
    if r1 - r0 < 2 or c1 - c0 < 2:
        return False
    expected = set()
    for c in range(c0, c1 + 1):
        expected.add((r0, c))
        expected.add((r1, c))
    for r in range(r0, r1 + 1):
        expected.add((r, c0))
        expected.add((r, c1))
    return set(cells) == expected and all(grid[r][c] == 8 for r, c in expected)


def solve(grid):
    """
    Scan objects in reading order.

    Hollow azure rectangles open a pending slot.  A later non-azure object is
    copied into the earliest pending slot whose interior has exactly the same
    height and width as the object's bounding box.  Earlier objects cannot fill
    rectangles that appear later in reading order.
    """
    result = [row[:] for row in grid]

    frames = []
    for cells in _components(grid, lambda v: v == 8):
        box = _bbox(cells)
        if _is_hollow_azure_frame(grid, box, cells):
            r0, c0, r1, c1 = box
            frames.append(
                {
                    "kind": "frame",
                    "key": (r0, c0),
                    "box": box,
                    "shape": (r1 - r0 - 1, c1 - c0 - 1),
                    "used": False,
                }
            )

    objects = []
    for cells in _components(grid, lambda v: v not in (0, 8)):
        r0, c0, r1, c1 = _bbox(cells)
        objects.append(
            {
                "kind": "object",
                "key": (r0, c0),
                "box": (r0, c0, r1, c1),
                "shape": (r1 - r0 + 1, c1 - c0 + 1),
            }
        )

    events = sorted(frames + objects, key=lambda item: item["key"])
    pending = []
    for event in events:
        if event["kind"] == "frame":
            pending.append(event)
            continue

        target = next(
            (frame for frame in pending if not frame["used"] and frame["shape"] == event["shape"]),
            None,
        )
        if target is None:
            continue

        sr0, sc0, sr1, sc1 = event["box"]
        tr0, tc0, _, _ = target["box"]
        for dr in range(sr1 - sr0 + 1):
            for dc in range(sc1 - sc0 + 1):
                result[tr0 + 1 + dr][tc0 + 1 + dc] = grid[sr0 + dr][sc0 + dc]
        target["used"] = True

    return result
