from collections import Counter
from copy import deepcopy


def solve(grid):
    """Write the bar-derived digit in the column marked by the top-row 5."""
    out = deepcopy(grid)
    marker_col = grid[0].index(5)

    bars = []
    eligible_lengths = []
    for row_index, row in enumerate(grid[1:], start=1):
        length = sum(value != 0 for value in row)
        if length == 0:
            continue
        contains_five = any(value == 5 for value in row)
        bars.append((row_index, length))
        if not contains_five:
            eligible_lengths.append(length)

    counts = Counter(eligible_lengths)
    duplicate_length = next(
        (length for length in eligible_lengths if counts[length] > 1),
        None,
    )

    for row_index, length in bars:
        if duplicate_length is not None and length != duplicate_length:
            base = length - duplicate_length
        else:
            base = length - 1
        out[row_index][marker_col] = (base * base) % 10

    return out
