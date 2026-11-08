"""Visible-only solution for the blind ARC episode."""


def solve(grid):
    """Mark candidate panels contained in the pixels added to panel 2.

    The input is a horizontal strip of equally shaped panels separated by
    all-9 columns.  The first panel is a base mask and the second is the same
    object with extra pixels.  Each remaining panel is a candidate mask.
    Emit 8 exactly when every non-background cell of that candidate lies in
    the set of pixels added from the first panel to the second.
    """
    if not grid or not grid[0]:
        return [[]]

    height = len(grid)
    width = len(grid[0])
    separators = {c for c in range(width) if all(grid[r][c] == 9 for r in range(height))}

    spans = []
    start = 0
    for c in range(width + 1):
        if c == width or c in separators:
            if start < c:
                spans.append((start, c))
            start = c + 1

    def occupied(span):
        left, right = span
        return {
            (r, c - left)
            for r in range(height)
            for c in range(left, right)
            if grid[r][c] != 0
        }

    if len(spans) < 3:
        return [[]]

    base = occupied(spans[0])
    expanded = occupied(spans[1])
    added = expanded - base

    answer = []
    for span in spans[2:]:
        candidate = occupied(span)
        answer.append(8 if candidate and candidate <= added else 0)
    return [answer]
