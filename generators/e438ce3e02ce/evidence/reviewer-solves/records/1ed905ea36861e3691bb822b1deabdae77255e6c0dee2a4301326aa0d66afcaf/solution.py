def solve(grid):
    """Color each cell by its nearest nonzero seed; use 8 for distance ties."""
    seeds = [
        (row, col, color)
        for row, values in enumerate(grid)
        for col, color in enumerate(values)
        if color != 0
    ]

    if not seeds:
        return [row[:] for row in grid]

    output = []
    for row, values in enumerate(grid):
        output_row = []
        for col in range(len(values)):
            distances = [
                (abs(row - seed_row) + abs(col - seed_col), color)
                for seed_row, seed_col, color in seeds
            ]
            nearest_distance = min(distance for distance, _ in distances)
            nearest_colors = {
                color for distance, color in distances if distance == nearest_distance
            }
            output_row.append(next(iter(nearest_colors)) if len(nearest_colors) == 1 else 8)
        output.append(output_row)
    return output
