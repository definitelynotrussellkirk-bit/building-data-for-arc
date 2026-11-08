def solve(grid):
    """Overlay the four 4-column tiles using priority tile 3 > 4 > 1 > 2."""
    separators = [i for i in range(len(grid[0])) if all(row[i] == 3 for row in grid)]
    starts = [0] + [i + 1 for i in separators]
    ends = separators + [len(grid[0])]
    panels = [[row[start:end] for row in grid] for start, end in zip(starts, ends)]
    if len(panels) != 4 or any(len(row) != len(panels[0][0]) for panel in panels for row in panel):
        raise ValueError("expected four equally sized panels separated by solid color-3 columns")

    out = [[0 for _ in panels[0][0]] for _ in panels[0]]
    # Highest-priority panel is inspected first at each aligned cell.
    for r in range(len(out)):
        for c in range(len(out[0])):
            for panel_index in (2, 3, 0, 1):
                value = panels[panel_index][r][c]
                if value != 0:
                    out[r][c] = value
                    break
    return out
