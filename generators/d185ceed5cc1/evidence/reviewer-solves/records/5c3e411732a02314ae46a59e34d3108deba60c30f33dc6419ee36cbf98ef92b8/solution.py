"""Visible-example solution for d185ceed5cc1."""


def solve(grid):
    """Pack nonzero cells rightward inside each row segment split by color 8."""
    result = []
    for source in grid:
        row = [0] * len(source)
        column = 0
        while column < len(source):
            if source[column] == 8:
                row[column] = 8
                column += 1
                continue
            end = column
            while end < len(source) and source[end] != 8:
                end += 1
            values = [value for value in source[column:end] if value != 0]
            start = end - len(values)
            for offset, value in enumerate(values):
                row[start + offset] = value
            column = end
        result.append(row)
    return result
