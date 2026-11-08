from collections import Counter


def _components(grid, background):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for start_row in range(height):
        for start_col in range(width):
            if grid[start_row][start_col] == background or (start_row, start_col) in seen:
                continue
            color = grid[start_row][start_col]
            cells = [(start_row, start_col)]
            seen.add((start_row, start_col))
            for row, col in cells:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    point = row + dr, col + dc
                    rr, cc = point
                    if (0 <= rr < height and 0 <= cc < width and point not in seen
                            and grid[rr][cc] == color):
                        seen.add(point)
                        cells.append(point)
            result.append((color, cells))
    return result


def _normalize(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return {(row - top, col - left) for row, col in cells}


def _bbox_size(cells):
    return max(row for row, _ in cells) + 1, max(col for _, col in cells) + 1


def solve(grid):
    background = Counter(value for row in grid for value in row).most_common(1)[0][0]
    objects = sorted(
        _components(grid, background),
        key=lambda item: (-len(item[1]), min(r for r, _ in item[1]), min(c for _, c in item[1])),
    )
    (large_color, large_raw), (_, small_raw) = objects[:2]
    large = _normalize(large_raw)
    small = _normalize(small_raw)
    large_h, large_w = _bbox_size(large)
    small_h, small_w = _bbox_size(small)
    output = [[background] * max(large_w, small_w)
              for _ in range(max(large_h, small_h))]
    for row, col in large - small:
        output[row][col] = large_color
    return output
