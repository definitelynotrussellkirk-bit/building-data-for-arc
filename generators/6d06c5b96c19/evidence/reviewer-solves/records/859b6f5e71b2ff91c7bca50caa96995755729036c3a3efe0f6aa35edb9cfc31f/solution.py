def solve(grid):
    """Remove the cue column and rotate payload rows down by the red cue row."""
    if not grid or not grid[0]:
        raise ValueError("grid must be non-empty")
    width = len(grid[0])
    if width < 2 or any(len(row) != width for row in grid):
        raise ValueError("grid must be rectangular with a payload column")

    red_rows = [row_index for row_index, row in enumerate(grid) if row[0] == 2]
    if len(red_rows) != 1:
        raise ValueError("cue column must contain exactly one red cell")

    payload = [list(row[1:]) for row in grid]
    shift = red_rows[0] % len(payload)
    if shift == 0:
        return payload
    return payload[-shift:] + payload[:-shift]
