from __future__ import annotations


def _rectangle_corner_color(grid: list[list[int]]) -> tuple[int, int, int, int, int]:
    """Return (color, top, left, bottom, right) for the four equal corners."""
    positions: dict[int, list[tuple[int, int]]] = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                positions.setdefault(value, []).append((r, c))

    candidates: list[tuple[int, int, int, int, int]] = []
    for color, cells in positions.items():
        if len(cells) != 4:
            continue
        rows = sorted({r for r, _ in cells})
        cols = sorted({c for _, c in cells})
        if len(rows) != 2 or len(cols) != 2:
            continue
        expected = {(r, c) for r in rows for c in cols}
        if set(cells) == expected:
            candidates.append((color, rows[0], cols[0], rows[1], cols[1]))

    if len(candidates) != 1:
        raise ValueError(f"expected one four-corner frame, found {len(candidates)}")
    return candidates[0]


def solve(grid: list[list[int]]) -> list[list[int]]:
    """Move the separate motif into the interior of its corner-marked frame."""
    _marker, top, left, bottom, right = _rectangle_corner_color(grid)
    inner_h = bottom - top - 1
    inner_w = right - left - 1
    if inner_h <= 0 or inner_w <= 0:
        raise ValueError("frame has no interior")

    # Every non-background cell outside the frame rectangle belongs to the motif.
    motif_cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and not (top <= r <= bottom and left <= c <= right)
    ]
    if not motif_cells:
        raise ValueError("no motif outside the frame")

    min_r = min(r for r, _ in motif_cells)
    max_r = max(r for r, _ in motif_cells)
    min_c = min(c for _, c in motif_cells)
    max_c = max(c for _, c in motif_cells)
    if (max_r - min_r + 1, max_c - min_c + 1) != (inner_h, inner_w):
        raise ValueError(
            "motif bounding box does not match frame interior: "
            f"{max_r - min_r + 1}x{max_c - min_c + 1} vs {inner_h}x{inner_w}"
        )

    output = [row[left : right + 1] for row in grid[top : bottom + 1]]
    for dr in range(inner_h):
        for dc in range(inner_w):
            output[dr + 1][dc + 1] = grid[min_r + dr][min_c + dc]
    return output
