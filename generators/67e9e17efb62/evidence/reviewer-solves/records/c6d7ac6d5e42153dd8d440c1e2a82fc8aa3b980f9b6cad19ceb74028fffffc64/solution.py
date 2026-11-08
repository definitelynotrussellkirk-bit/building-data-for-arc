"""Visible-example solution for the post-repair reviewer episode."""


def solve(grid):
    width = len(grid[0])
    top = grid[0]
    color = next(value for value in top if value != 0)
    length = sum(value != 0 for value in top)
    run_lengths = [*range(1, length + 1), *range(length - 1, 0, -1)]

    stream = []
    for index, run_length in enumerate(run_lengths):
        stream.extend([color] * run_length)
        if index + 1 < len(run_lengths):
            stream.append(0)

    output_height = (len(stream) + width - 1) // width
    stream.extend([0] * (output_height * width - len(stream)))
    return [stream[offset:offset + width] for offset in range(0, len(stream), width)]
