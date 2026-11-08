from collections import Counter


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < h and 0 <= ny < w and grid[nx][ny] != 0
                            and (nx, ny) not in seen):
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            r0 = min(x for x, _ in cells)
            r1 = max(x for x, _ in cells)
            c0 = min(y for _, y in cells)
            c1 = max(y for _, y in cells)
            crop = [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]
            counts = Counter(value for row in crop for value in row)
            fill = counts.most_common(1)[0][0]
            marker_count = sum(value != fill for row in crop for value in row)
            out.append({
                "crop": crop,
                "shape": (r1 - r0 + 1, c1 - c0 + 1),
                "marker_count": marker_count,
                "origin": (r0, c0),
            })
    return out


def solve(grid):
    components = _components(grid)
    shape_frequency = Counter(item["shape"] for item in components)
    marker_frequency = Counter(item["marker_count"] for item in components)

    # Visible examples identify the member of a repeated-shape family whose
    # marker count is not duplicated by another object.  If a query contains
    # more than one such family, prefer the larger repeated family.
    candidates = [
        item for item in components
        if shape_frequency[item["shape"]] > 1
        and marker_frequency[item["marker_count"]] == 1
    ]
    if not candidates:
        candidates = [item for item in components if marker_frequency[item["marker_count"]] == 1]
    if not candidates:
        candidates = components
    chosen = max(candidates, key=lambda item: (
        item["shape"][0] * item["shape"][1],
        item["shape"][0],
        item["shape"][1],
        -item["origin"][0],
        -item["origin"][1],
    ))
    return chosen["crop"]
