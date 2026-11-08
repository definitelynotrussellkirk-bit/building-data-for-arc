from collections import Counter

def solve(grid):
    h, w = len(grid), len(grid[0])
    bg = Counter(v for row in grid for v in row).most_common(1)[0][0]
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != bg}
    panels = []
    while unseen:
        seed = min(unseen)
        unseen.remove(seed)
        todo, cells = [seed], []
        while todo:
            r, c = todo.pop()
            cells.append((r, c))
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in unseen:
                    unseen.remove(p)
                    todo.append(p)
        r0, r1 = min(r for r,c in cells), max(r for r,c in cells)
        c0, c1 = min(c for r,c in cells), max(c for r,c in cells)
        panels.append((r0, c0, [row[c0:c1+1] for row in grid[r0:r1+1]]))
    panels.sort(key=lambda x: (x[0], x[1]))
    if not panels:
        return []
    ph, pw = len(panels[0][2]), len(panels[0][2][0])
    out = [[0] * pw for _ in range(ph)]
    for _, _, panel in panels:
        if len(panel) != ph or any(len(row) != pw for row in panel):
            raise ValueError("Panel shapes differ")
        for r in range(ph):
            for c in range(pw):
                if out[r][c] == 0 and panel[r][c] != 0:
                    out[r][c] = panel[r][c]
    return out
