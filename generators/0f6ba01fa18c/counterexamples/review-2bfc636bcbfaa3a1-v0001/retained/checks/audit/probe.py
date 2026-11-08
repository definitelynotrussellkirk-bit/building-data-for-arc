#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, deque
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
sys.path[:0] = [str(REPO / "shared/runtime"), str(REPO / "src")]


def load(task):
    path = REPO / "generators" / task / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module, hashlib.sha256(path.read_bytes()).hexdigest()


def comps(grid):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r,c) in seen: continue
            q=[(r,c)]; seen.add((r,c)); cells=set()
            while q:
                rr,cc=q.pop(); cells.add((rr,cc))
                for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    p=(rr+dr,cc+dc)
                    if 0<=p[0]<h and 0<=p[1]<w and p not in seen and grid[p[0]][p[1]]==color:
                        seen.add(p);q.append(p)
            out.append((color,cells))
    return out


def bbox(cells):
    rs=[r for r,c in cells]; cs=[c for r,c in cells]
    return min(rs),min(cs),max(rs),max(cs)


def is_frame(cells):
    r0,c0,r1,c1=bbox(cells)
    expected={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)
              if r in (r0,r1) or c in (c0,c1)}
    return cells==expected


def bbox_count(grid):
    cs=comps(grid); h=len(grid); w=len(grid[0]); out=[[0]*w for _ in range(h)]
    for _,cells in cs:
        r0,c0,r1,c1=bbox(cells)
        for r in range(r0,r1+1):
            for c in range(c0,c1+1): out[r][c]+=1
    return out


def frame_only(grid):
    cs=comps(grid); h=len(grid); w=len(grid[0]); out=[[0]*w for _ in range(h)]
    for _,cells in cs:
        points=set(cells)
        if is_frame(cells):
            r0,c0,r1,c1=bbox(cells)
            points={(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)}
        for r,c in points: out[r][c]+=1
    return out


def norm(grid,color):
    pts={(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==color}
    r0=min(r for r,c in pts); c0=min(c for r,c in pts)
    return {(r-r0,c-c0) for r,c in pts}


def bool_result(grid, key_override=None):
    a=norm(grid,1); b=norm(grid,2)
    key=key_override or next(v for v in (3,4,6) if sum(x==v for row in grid for x in row)==1)
    cells={3:a|b,4:a&b,6:a^b}[key]
    if not cells:return [[0]]
    r0=min(r for r,c in cells); c0=min(c for r,c in cells)
    cells={(r-r0,c-c0) for r,c in cells}
    out=[[0]*(max(c for r,c in cells)+1) for _ in range(max(r for r,c in cells)+1)]
    for r,c in cells:out[r][c]=8
    return out


def main():
    g0,h0=load("0f6ba01fa18c"); g5,h5=load("59a9a5c505fb")
    report={"schema":"audit-probe-v1","tasks":{}}
    bands=("easy","medium","hard")
    op_counts={}; union_fit={}
    for band in bands:
        counts=Counter(); fit=0
        for i in range(200):
            grid=g0.generate(70000+i,i,difficulty=band)
            key=next(v for v in (3,4,6) if sum(x==v for row in grid for x in row)==1)
            counts[key]+=1
            fit += bool_result(grid,3)==bool_result(grid)
        op_counts[band]=dict(counts); union_fit[band]=fit
    inp0=json.load(open(ROOT/'checks/audit/0f6ba01fa18c/input.json'))
    report['tasks']['0f6ba01fa18c']={
        'generator_sha256':h0,'samples_per_band':200,'op_key_counts':op_counts,
        'always_union_matches':union_fit,'manual_counterexample_self_check':g0.self_check(inp0),
    }
    frame_counts={}; rival_matches={}; nested_counts={}
    for band in bands:
        frames=matches=nested=0
        for i in range(200):
            grid=g5.generate(80000+i,i,difficulty=band)
            objects=comps(grid)
            frames += all(is_frame(cells) for _,cells in objects)
            boxes=[bbox(cells) for _,cells in objects]
            ordered=sorted(boxes,key=lambda b:(b[0],b[1],-b[2],-b[3]))
            nested += all(a[0]<b[0] and a[1]<b[1] and b[2]<a[2] and b[3]<a[3]
                          for a,b in zip(ordered,ordered[1:]))
            matches += frame_only(grid)==bbox_count(grid)
        frame_counts[band]=frames; rival_matches[band]=matches; nested_counts[band]=nested
    inp5=json.load(open(ROOT/'checks/audit/59a9a5c505fb/input.json'))
    canonical_row = next(
        json.loads(line)
        for line in (REPO / 'shared/data/canonical/puzzles.jsonl').read_text().splitlines()
        if json.loads(line).get('task_id') == '59a9a5c505fb'
    )
    canonical_pairs = [*canonical_row['train'], canonical_row['test']]
    def decode(rows):
        return [[int(value) for value in row] for row in rows]
    canonical_inputs = [decode(pair['input']) for pair in canonical_pairs]
    canonical_outputs = [decode(pair['output']) for pair in canonical_pairs]
    report['tasks']['59a9a5c505fb']={
        'generator_sha256':h5,'samples_per_band':200,
        'all_components_complete_frames':frame_counts,
        'all_bboxes_strictly_nested':nested_counts,
        'frame_only_rival_matches':rival_matches,
        'canonical_pairs':len(canonical_pairs),
        'canonical_all_components_complete_frames':sum(
            all(is_frame(cells) for _, cells in comps(grid)) for grid in canonical_inputs
        ),
        'canonical_all_bboxes_strictly_nested':sum(
            all(
                a[0] < b[0] and a[1] < b[1] and b[2] < a[2] and b[3] < a[3]
                for a, b in zip(
                    sorted((bbox(cells) for _, cells in comps(grid)), key=lambda box: (box[0], box[1], -box[2], -box[3])),
                    sorted((bbox(cells) for _, cells in comps(grid)), key=lambda box: (box[0], box[1], -box[2], -box[3]))[1:],
                )
            )
            for grid in canonical_inputs
        ),
        'canonical_frame_only_rival_matches':sum(
            frame_only(grid) == output for grid, output in zip(canonical_inputs, canonical_outputs)
        ),
        'manual_counterexample_self_check':g5.self_check(inp5),
        'manual_counterexample_rival_differs':frame_only(inp5)!=bbox_count(inp5),
    }
    out=ROOT/'checks/audit/audit-probe.json';out.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=='__main__':main()
