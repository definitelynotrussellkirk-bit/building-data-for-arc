"""Infer a pixelwise analogy from the five visible panels in one input."""


def solve(grid):
    height, width = len(grid), len(grid[0])
    separators = [c for c in range(width) if all(row[c] == 5 for row in grid)]
    bounds = [-1] + separators + [width]
    panels = [[row[left + 1:right] for row in grid]
              for left, right in zip(bounds, bounds[1:])]
    if len(panels) != 5 or len({len(p[0]) for p in panels}) != 1:
        raise ValueError("Expected five equally sized panels divided by gray columns")
    left, right, example, new_left, new_right = panels
    panel_width = len(left[0])
    choices = {}
    for r in range(height):
        for c in range(panel_width):
            a, b, result = left[r][c], right[r][c], example[r][c]
            state = (bool(a), bool(b))
            possible = {("constant", result)}
            if a and result == a:
                possible.add(("left", None))
            if b and result == b:
                possible.add(("right", None))
            choices[state] = choices.get(state, possible) & possible
    operations = {}
    for state, possible in choices.items():
        if not possible:
            raise ValueError("The demonstrated operation is not cellwise consistent")
        operations[state] = min(possible, key=lambda x: {"left": 0, "right": 1, "constant": 2}[x[0]])
    output = []
    for r in range(height):
        row = []
        for c in range(panel_width):
            a, b = new_left[r][c], new_right[r][c]
            state = (bool(a), bool(b))
            if state not in operations:
                raise ValueError("A query cell state was not demonstrated in the analogy")
            role, value = operations[state]
            row.append(a if role == "left" else b if role == "right" else value)
        output.append(row)
    return output
