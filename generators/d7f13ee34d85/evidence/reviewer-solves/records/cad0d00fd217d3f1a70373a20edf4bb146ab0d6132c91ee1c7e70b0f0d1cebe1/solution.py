"""Solve the visible frame-and-shape examples without project imports."""

def solve(grid):
    height, width = len(grid), len(grid[0])
    visited = set()
    frames, motifs = [], []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in visited:
                continue
            work = [(row, col)]
            visited.add((row, col))
            pixels = []
            while work:
                r, c = work.pop()
                pixels.append((r, c))
                for nr, nc in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                    if (0 <= nr < height and 0 <= nc < width and
                            (nr,nc) not in visited and grid[nr][nc] == color):
                        visited.add((nr,nc))
                        work.append((nr,nc))
            top = min(r for r,c in pixels)
            bottom = max(r for r,c in pixels)
            left = min(c for r,c in pixels)
            right = max(c for r,c in pixels)
            h, w = bottom-top+1, right-left+1
            item = (pixels, color, top, left, h, w)
            is_frame = (h >= 3 and w >= 3 and len(pixels) == 2*h+2*w-4
                        and all(r in (top,bottom) or c in (left,right) for r,c in pixels))
            (frames if is_frame else motifs).append(item)
    frames.sort(key=lambda x: (x[4]-2)*(x[5]-2))
    motifs.sort(key=lambda x: len(x[0]))
    output = [[0]*width for _ in range(height)]
    for pixels, color, top, left, h, w in frames:
        for r,c in pixels:
            output[r][c] = color
    for frame, motif in zip(frames, motifs):
        pixels, color, old_top, old_left, h, w = motif
        top = frame[2]+1+(frame[4]-2-h)//2
        left = frame[3]+1+(frame[5]-2-w)//2
        for r,c in pixels:
            nr, nc = top+r-old_top, left+c-old_left
            if 0 <= nr < height and 0 <= nc < width:
                output[nr][nc] = color
    return output
