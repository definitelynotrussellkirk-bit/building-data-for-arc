from collections import Counter


def solve(grid):
    """Move patterned/key rows first, then order plain rows by fill amount.

    The visible tasks use 0 as empty space.  The most frequent non-zero
    color is the structural/fill color.  Rows containing any other color
    are key rows; they are ordered by increasing structural-color count.
    All remaining rows follow in decreasing structural-color count.
    Python's stable sort preserves input order for ties.
    """
    if not grid:
        return []

    counts = Counter(cell for row in grid for cell in row if cell != 0)
    if not counts:
        return [list(row) for row in grid]

    fill = counts.most_common(1)[0][0]

    key_rows = []
    plain_rows = []
    for index, row in enumerate(grid):
        copied = list(row)
        fill_count = copied.count(fill)
        has_key_color = any(cell not in (0, fill) for cell in copied)
        item = (fill_count, index, copied)
        if has_key_color:
            key_rows.append(item)
        else:
            plain_rows.append(item)

    key_rows.sort(key=lambda item: item[0])
    plain_rows.sort(key=lambda item: -item[0])
    return [row for _, _, row in key_rows + plain_rows]
