"""Reassemble the observed monochrome pieces into a filled 3 by 4 board."""

def solve(grid):
    seen = set()
    pieces = []
    height, width = len(grid), len(grid[0])
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            cells = [(row, col)]
            seen.add((row, col))
            for y, x in cells:
                for a, b in ((y-1,x), (y+1,x), (y,x-1), (y,x+1)):
                    if (0 <= a < height and 0 <= b < width
                            and grid[a][b] == color and (a,b) not in seen):
                        seen.add((a,b))
                        cells.append((a,b))
            variants = set()
            for reflection in (1, -1):
                points = [(y, x*reflection) for y,x in cells]
                for _ in range(4):
                    top = min(y for y,x in points)
                    left = min(x for y,x in points)
                    variants.add(tuple(sorted((y-top, x-left) for y,x in points)))
                    points = [(x,-y) for y,x in points]
            pieces.append((len(cells), color, sorted(variants)))
    pieces.sort(key=lambda item: (-item[0], item[1], item[2]))
    board = [[0]*4 for _ in range(3)]

    def place(index):
        if index == len(pieces):
            return all(all(row) for row in board)
        _, color, variants = pieces[index]
        for cells in variants:
            for row in range(3-max(y for y,x in cells)):
                for col in range(4-max(x for y,x in cells)):
                    if any(board[row+y][col+x] for y,x in cells):
                        continue
                    for y,x in cells:
                        board[row+y][col+x] = color
                    if place(index+1):
                        return True
                    for y,x in cells:
                        board[row+y][col+x] = 0
        return False

    if not place(0):
        raise ValueError('Pieces do not tile the observed 3 by 4 output shape')
    return board
