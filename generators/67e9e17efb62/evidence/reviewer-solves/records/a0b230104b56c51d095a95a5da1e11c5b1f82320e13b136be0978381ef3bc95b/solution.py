def solve(grid):
    """Expand the input bar into diagonal-length runs and wrap by input width."""
    width = len(grid[0])
    colored = [value for row in grid for value in row if value != 0]
    if not colored:
        return []

    color = colored[0]
    size = len(colored)
    run_lengths = list(range(1, size + 1)) + list(range(size - 1, 0, -1))

    stream = []
    for index, run_length in enumerate(run_lengths):
        stream.extend([color] * run_length)
        if index + 1 < len(run_lengths):
            stream.append(0)

    padding = (-len(stream)) % width
    stream.extend([0] * padding)
    return [stream[start:start + width] for start in range(0, len(stream), width)]
