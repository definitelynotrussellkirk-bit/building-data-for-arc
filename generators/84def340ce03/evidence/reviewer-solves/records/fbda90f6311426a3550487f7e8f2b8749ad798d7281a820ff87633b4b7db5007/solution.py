def solve(grid):
    """Expand alternating input rows into corner-coloured concentric rings."""
    top_tape = [value for row in grid[0::2] for value in row]
    bottom_tape = [value for row in grid[1::2] for value in row]
    n = len(top_tape)
    half = n // 2

    output = []
    for row_index in range(n):
        tape = top_tape if row_index < half else bottom_tape
        output_row = []
        for column_index in range(n):
            ring = min(
                row_index,
                column_index,
                n - 1 - row_index,
                n - 1 - column_index,
            )
            pair_start = n - 2 - 2 * ring
            tape_index = pair_start + (column_index >= half)
            output_row.append(tape[tape_index])
        output.append(output_row)
    return output
