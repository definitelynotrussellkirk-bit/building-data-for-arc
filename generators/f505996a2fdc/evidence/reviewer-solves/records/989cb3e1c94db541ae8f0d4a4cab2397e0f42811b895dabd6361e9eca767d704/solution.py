"""Visible-example solver; selector 6 is an explicitly uncertain extrapolation."""


def solve(grid):
    """Remove the corner selector, crop the payload, and transform its rectangle."""
    if not grid or not grid[0]:
        return []

    command = grid[0][0]
    payload = [list(row) for row in grid]
    payload[0][0] = 0
    foreground = [
        (r, c)
        for r, row in enumerate(payload)
        for c, value in enumerate(row)
        if value != 0
    ]
    if not foreground:
        return []

    top = min(r for r, _ in foreground)
    bottom = max(r for r, _ in foreground)
    left = min(c for _, c in foreground)
    right = max(c for _, c in foreground)
    crop = [row[left:right + 1] for row in payload[top:bottom + 1]]

    if command == 1:
        return crop
    if command == 2:
        return [list(column) for column in zip(*crop[::-1])]
    if command == 3:
        return [row[::-1] for row in crop[::-1]]
    if command == 4:
        return [list(column) for column in zip(*crop)]
    if command == 5:
        return [row[::-1] for row in crop]
    if command == 6:
        # No visible example demonstrates this command. Pairing this with the
        # observed left-right reflection for 5 is a hypothesis, not a fact.
        return crop[::-1]
    raise ValueError("Unsupported selector: %r" % (command,))
