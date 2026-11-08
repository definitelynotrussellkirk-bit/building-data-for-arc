from __future__ import annotations
import hashlib, importlib.util, json, os
from pathlib import Path

root = Path(__file__).resolve().parents[3]
repo = root / 'repo'
source = repo / 'generators/04e2ffe8dc8e/generator.py'
spec = importlib.util.spec_from_file_location('audit_generator_04', source)
gen = importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(gen)
kwargs = {'seed': 0, 'sample_index': 0, 'texture': 'decoy', 'small_size': 1}
grid = gen.generate(**kwargs)
assert gen.self_check(grid) == []
assert sum(value not in (0, 3) for row in grid for value in row) == 0

def components(board):
    h, w = len(board), len(board[0]); seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if board[r][c] == 0 or (r, c) in seen:
                continue
            color = board[r][c]; stack = [(r, c)]; seen.add((r, c)); cells = []
            while stack:
                x, y = stack.pop(); cells.append((x, y))
                for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if 0 <= nx < h and 0 <= ny < w and (nx,ny) not in seen and board[nx][ny] == color:
                        seen.add((nx,ny)); stack.append((nx,ny))
            out.append((len(cells), min(cells), cells))
    return out
rival = [row[:] for row in grid]
for r, c in min(components(grid), key=lambda item: (item[0], item[1]))[2]:
    rival[r][c] = 6
here = Path(__file__).resolve().parent
racket = json.loads((here/'racket.json').read_text())
actual = racket['results'][0]['output']
assert actual == rival
assert json.loads((here/'input.json').read_text()) == grid
assert json.loads((here/'rival-smallest-any-color.json').read_text()) == rival
print(json.dumps({'passed': True, 'generator_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'actual_equals_rival': True}))
