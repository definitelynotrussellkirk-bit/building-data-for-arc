def solve(grid):
    """Overlay four equal-height panels, using panel priority 1, 2, 4, 3."""
    if not grid or len(grid) % 4 != 0:
        raise ValueError("expected four equally sized vertical panels")

    panel_h = len(grid) // 4
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("ragged grid")

    panels = [grid[i * panel_h : (i + 1) * panel_h] for i in range(4)]
    out = [[0 for _ in range(width)] for _ in range(panel_h)]

    # Fill low priority first so higher-priority nonzero cells overwrite it.
    for panel_index in (2, 3, 1, 0):
        panel = panels[panel_index]
        for r in range(panel_h):
            for c in range(width):
                if panel[r][c] != 0:
                    out[r][c] = panel[r][c]
    return out
