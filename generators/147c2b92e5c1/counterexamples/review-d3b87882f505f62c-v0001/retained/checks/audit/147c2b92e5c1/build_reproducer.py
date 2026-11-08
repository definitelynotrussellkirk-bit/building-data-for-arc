from __future__ import annotations
import importlib.util
import json
from pathlib import Path

GEN_PATH = Path('generators/147c2b92e5c1/generator.py')
spec = importlib.util.spec_from_file_location('audit_generator_147c2b92e5c1', GEN_PATH)
gen = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gen)

def components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(1, h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a, b = x + dx, y + dy
                    if (1 <= a < h and 0 <= b < w and
                            grid[a][b] == color and (a, b) not in seen):
                        seen.add((a, b))
                        stack.append((a, b))
            result.append((color, cells))
    return result

def crop(color, cells):
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    out = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in cells:
        out[r-r0][c-c0] = color
    return out

def hole_count(grid):
    h, w = len(grid), len(grid[0])
    outside = set()
    stack = []
    for r in range(h):
        for c in range(w):
            if (r in (0, h-1) or c in (0, w-1)) and grid[r][c] == 0:
                outside.add((r, c)); stack.append((r, c))
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            p = (r+dr, c+dc)
            if 0 <= p[0] < h and 0 <= p[1] < w and grid[p[0]][p[1]] == 0 and p not in outside:
                outside.add(p); stack.append(p)
    unseen = {(r,c) for r in range(h) for c in range(w) if grid[r][c] == 0 and (r,c) not in outside}
    count = 0
    while unseen:
        count += 1
        stack = [unseen.pop()]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                p = (r+dr, c+dc)
                if p in unseen:
                    unseen.remove(p); stack.append(p)
    return count

def identity_rival(grid):
    candidates = []
    for color, cells in components(grid):
        shape = crop(color, cells)
        if hole_count(shape) == 1:
            candidates.append(shape)
    assert len(candidates) == 1
    shape = candidates[0]
    return [[value for value in row for _ in range(2)] for row in shape for _ in range(2)]

grids = [gen.generate(60, index, difficulty='easy') for index in range(5)]
Path('../checks/audit/147c2b92e5c1/input.json').write_text(json.dumps(grids, indent=2) + '\n')
Path('../checks/audit/147c2b92e5c1/rival.json').write_text(json.dumps([identity_rival(g) for g in grids], indent=2) + '\n')
Path('../checks/audit/147c2b92e5c1/generation.json').write_text(json.dumps({
    'task_id': '147c2b92e5c1', 'difficulty': 'easy', 'seed': 60,
    'sample_indices': list(range(5)), 'rival': 'always_identity_transform',
    'generator_sha256': '869c76ad7b68565e991b58512d25cefbf2c3846ab2f413313473d1ee65d03552'
}, indent=2) + '\n')
