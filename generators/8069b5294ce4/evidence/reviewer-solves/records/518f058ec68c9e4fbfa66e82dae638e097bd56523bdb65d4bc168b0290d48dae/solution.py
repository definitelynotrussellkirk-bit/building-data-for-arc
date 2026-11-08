"""Visible-example solution for the blind ARC review task."""


def solve(grid):
    """Return the adjacency matrix of the largest touching object cluster.

    Non-zero cells are split into monochrome 4-connected objects.  Two objects
    are adjacent when cells from the two objects share an edge.  The largest
    connected component of that object graph is retained, its objects are
    ordered by their first cell in row-major order, and the output encodes
    self-identity with 1 and object adjacency with 8.
    """
    height = len(grid)
    width = len(grid[0]) if height else 0
    directions = ((-1, 0), (1, 0), (0, -1), (0, 1))

    # Extract monochrome non-background objects.
    cell_to_object = {}
    objects = []
    seen = set()
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue

            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current_row, current_col = stack.pop()
                cells.append((current_row, current_col))
                for row_delta, col_delta in directions:
                    next_row = current_row + row_delta
                    next_col = current_col + col_delta
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))

            object_index = len(objects)
            objects.append(cells)
            for cell in cells:
                cell_to_object[cell] = object_index

    if not objects:
        return []

    # Build the side-contact graph between differently colored objects.
    adjacency = [set() for _ in objects]
    for object_index, cells in enumerate(objects):
        for row, col in cells:
            for row_delta, col_delta in directions:
                neighbor = (row + row_delta, col + col_delta)
                neighbor_index = cell_to_object.get(neighbor)
                if neighbor_index is None or neighbor_index == object_index:
                    continue
                adjacency[object_index].add(neighbor_index)

    # Find object-graph components and retain the largest one.  The extra
    # deterministic tie-breakers are immaterial to the visible examples but
    # make the solver well-defined for equally large distractor clusters.
    graph_components = []
    unseen = set(range(len(objects)))
    while unseen:
        start = min(unseen)
        stack = [start]
        unseen.remove(start)
        component = []
        while stack:
            object_index = stack.pop()
            component.append(object_index)
            for neighbor_index in adjacency[object_index]:
                if neighbor_index in unseen:
                    unseen.remove(neighbor_index)
                    stack.append(neighbor_index)
        graph_components.append(component)

    def component_key(component):
        total_cells = sum(len(objects[index]) for index in component)
        first_cell = min(min(objects[index]) for index in component)
        return (len(component), total_cells, -first_cell[0], -first_cell[1])

    selected = max(graph_components, key=component_key)
    selected.sort(key=lambda index: min(objects[index]))

    output_size = len(selected)
    output = [[0] * output_size for _ in range(output_size)]
    for row_index, object_index in enumerate(selected):
        output[row_index][row_index] = 1
        for col_index, other_index in enumerate(selected):
            if other_index in adjacency[object_index]:
                output[row_index][col_index] = 8
    return output
