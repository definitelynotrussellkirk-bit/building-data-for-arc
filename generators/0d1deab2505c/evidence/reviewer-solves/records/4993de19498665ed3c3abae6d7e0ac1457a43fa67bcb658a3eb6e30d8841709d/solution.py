"""Post-repair solver inferred from the visible examples only."""


def solve(grid):
    if not grid:
        return []
    height, width = len(grid), len(grid[0])
    background, stem_color, center_color = 8, 1, 4
    foreground = {(r, c) for r in range(height) for c in range(width)
                  if grid[r][c] != background}
    components = []
    remaining = set(foreground)
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        component = {first}
        pending = [first]
        while pending:
            r, c = pending.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    neighbor = (r + dr, c + dc)
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        component.add(neighbor)
                        pending.append(neighbor)
        components.append(component)

    result = [[background] * width for _ in range(height)]
    for component in components:
        centers = [(r, c) for r, c in component if grid[r][c] == center_color]
        if len(centers) != 1:
            raise ValueError('Expected one colored-cross center per figure')
        cr, cc = centers[0]
        directions = []
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            point = (cr + 2 * dr, cc + 2 * dc)
            if point in component and grid[point[0]][point[1]] == stem_color:
                directions.append((dr, dc))
        if len(directions) != 1:
            raise ValueError('Expected one axial blue stem per figure')
        dr, dc = directions[0]
        nr = 1 if dr == 1 else height - 2 if dr == -1 else cr
        nc = 1 if dc == 1 else width - 2 if dc == -1 else cc
        shift_r, shift_c = nr - cr, nc - cc
        for r, c in sorted(component):
            if abs(r - cr) + abs(c - cc) <= 1:
                tr, tc = nr - (r - cr), nc - (c - cc)
            else:
                tr, tc = r + shift_r, c + shift_c
            if not (0 <= tr < height and 0 <= tc < width):
                raise ValueError('A transformed figure leaves the grid')
            if result[tr][tc] != background:
                raise ValueError('Transformed figures overlap')
            result[tr][tc] = grid[r][c]
    return result
