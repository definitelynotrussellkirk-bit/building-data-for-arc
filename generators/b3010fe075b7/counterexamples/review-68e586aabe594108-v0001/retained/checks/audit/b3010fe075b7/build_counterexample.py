#!/usr/bin/env python3
"""Build and score the repeated-color consistency counterexample."""
from __future__ import annotations
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
base = [
 [2,3,0,9,5,7,0,0,0,0,0,0,0],
 [0,3,2,9,0,7,5,0,0,0,0,0,0],
 [2,0,3,9,5,0,7,0,0,0,0,0,0],
 [0,0,0,9,0,0,0,0,0,4,6,0,0],
 [0,0,0,9,0,8,8,0,0,0,6,4,0],
 [0,0,0,9,0,0,8,8,0,4,0,6,0],
 [0,0,0,9,0,8,0,8,0,0,0,0,0],
]
# Board top-left (0,3), full-grid board offset 4. Same zero/nonzero mask as
# the canonical 3x3 template, but every occupied cell uses a distinct color,
# violating the repeated-color equality constraints of the true bijection.
for r, c, value in [
    (0, 7, 1), (0, 8, 2),
    (1, 8, 3), (1, 9, 4),
    (2, 7, 5), (2, 9, 6),
]:
    base[r][c] = value
(HERE / "input.json").write_text(json.dumps(base, indent=2) + "\n")


def crop(panel):
    cells = [(r,c) for r,row in enumerate(panel) for c,v in enumerate(row) if v not in (0,9)]
    r1=min(r for r,_ in cells); r2=max(r for r,_ in cells)
    c1=min(c for _,c in cells); c2=max(c for _,c in cells)
    return [row[c1:c2+1] for row in panel[r1:r2+1]]


def mask_only_rival(grid):
    h=len(grid); sep=next(c for c in range(len(grid[0])) if all(grid[r][c]==9 for r in range(h)))
    template=crop([row[:sep] for row in grid])
    board=[row[sep+1:] for row in grid]
    out=[[0]*len(board[0]) for _ in range(h)]
    th,tw=len(template),len(template[0])
    for r0 in range(h-th+1):
        for c0 in range(len(board[0])-tw+1):
            ok=True
            for r,row in enumerate(template):
                for c,tv in enumerate(row):
                    bv=board[r0+r][c0+c]
                    if (tv==0) != (bv==0):
                        ok=False; break
                if not ok: break
            if ok:
                out[r0+th//2][c0+tw//2]=8
    return out

(HERE / "rival-output.json").write_text(json.dumps(mask_only_rival(base), indent=2) + "\n")
