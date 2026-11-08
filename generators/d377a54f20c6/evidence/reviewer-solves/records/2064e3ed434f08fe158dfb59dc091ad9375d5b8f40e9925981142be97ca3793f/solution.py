from collections import Counter


def solve(grid):
    height, width = len(grid), len(grid[0])
    result = [row[:] for row in grid]
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c]}
    while unseen:
        first = min(unseen)
        unseen.remove(first)
        queue = [first]
        cells = []
        while queue:
            r, c = queue.pop()
            cells.append((r, c))
            for rc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if rc in unseen:
                    unseen.remove(rc)
                    queue.append(rc)
        top = min(r for r, c in cells)
        bottom = max(r for r, c in cells)
        left = min(c for r, c in cells)
        right = max(c for r, c in cells)
        colors = Counter(grid[r][c] for r, c in cells).most_common()
        if len(colors) != 2 or colors[0][1] == colors[1][1]:
            raise ValueError("Expected an independently colored two-color rectangle")
        frame, ink = colors[0][0], colors[1][0]
        for r in range(top, bottom+1):
            for c in range(left, right+1):
                result[r][c] = frame if r in (top, bottom) or c in (left, right) else 0
        top, bottom, left, right = top+1, bottom-1, left+1, right-1
        while top <= bottom and left <= right:
            if bottom-top < 2 or right-left < 2:
                for r in range(top, bottom+1):
                    for c in range(left, right+1):
                        result[r][c] = ink
                break
            for r, c in ((top,left), (top,right), (bottom,left), (bottom,right)):
                result[r][c] = ink
            top, bottom, left, right = top+1, bottom-1, left+1, right-1
    return result
