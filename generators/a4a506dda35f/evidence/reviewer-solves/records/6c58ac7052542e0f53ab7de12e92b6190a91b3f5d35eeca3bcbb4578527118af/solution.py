from collections import Counter


def solve(grid):
    counts = Counter(value for row in grid for value in row if value != 0)
    output = []
    for color, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        output.extend([color] * count)
    return [output]
