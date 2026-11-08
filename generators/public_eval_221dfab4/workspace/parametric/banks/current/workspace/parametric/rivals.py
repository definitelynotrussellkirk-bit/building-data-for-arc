"""Ten total, explicit semantic shortcuts for the admitted stripe grammar."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import hashlib
import sys
BASE=Path(__file__).resolve().parent
_spec=importlib.util.spec_from_file_location('_rival221_'+hashlib.sha256(str(BASE).encode()).hexdigest()[:12],BASE/'family.py')
f=importlib.util.module_from_spec(_spec);sys.modules[_spec.name]=f;_spec.loader.exec_module(f)


def _eight_cells(grid, frame):
    todo={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v not in (frame['bg'],4)}
    selected=set()
    while todo:
        p=min(todo);todo.remove(p);stack=[p];comp={p};color=grid[p[0]][p[1]]
        while stack:
            r,c=stack.pop()
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    q=(r+dr,c+dc)
                    if q in todo and grid[q[0]][q[1]]==color:
                        todo.remove(q);comp.add(q);stack.append(q)
        if any(f.depth(frame,*q)%6==4 for q in comp):selected.update(comp)
    return selected


def _render(grid, extension, *, kind):
    frame=f.frame(grid)
    if kind=='top_edge_only':frame={**frame,'horizontal':True,'reverse':False}
    selected={p for comp in f.components(grid,frame['bg'])
              if any(f.depth(frame,*p)%6==4 for p in comp) for p in comp}
    if kind=='eight_connected':selected=_eight_cells(grid,frame)
    out=[row[:] for row in grid]
    for r,row in enumerate(grid):
        for c,v in enumerate(row):
            d=f.depth(frame,r,c);t=c if frame['horizontal'] else r
            green=d%6==4
            if kind=='period_four':green=d%4==2
            if kind=='green_phase_zero':green=d%6==0
            inside=frame['lo']<=t<=frame['hi']
            if inside:
                out[r][c]=3 if green else (4 if d%2==0 else (v if kind=='no_erasure' else frame['bg']))
            elif kind=='band_only':pass
            elif kind=='fill_green_lines' and green:out[r][c]=3
            elif kind=='color_global' and v not in (frame['bg'],4):out[r][c]=3
            elif kind=='eight_connected' and (r,c) in selected:out[r][c]=3
            elif kind not in ('color_global','eight_connected'):
                if (extension=='slice' and green and v!=frame['bg']) or (extension=='component' and (r,c) in selected):out[r][c]=3
    return out


def predict(grid, extension):
    out={'identity':[row[:] for row in grid],
         'other_setting':f.solve(grid,'component' if extension=='slice' else 'slice')}
    for kind in ('band_only','color_global','eight_connected','period_four',
                 'green_phase_zero','top_edge_only','no_erasure','fill_green_lines'):
        out[kind]=_render(grid,extension,kind=kind)
    return out
