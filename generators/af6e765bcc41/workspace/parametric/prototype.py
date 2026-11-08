"""Opt-in frame completion: simultaneous repair, then component recognition.

Python outputs are deterministic claims. Native qualification executes the
selected Racket program independently; this module grants no acceptance.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import random

HOME = Path(__file__).resolve().parent
MODES = ("none", "single_gap")


def settings_value(settings):
    if type(settings) is not dict or set(settings) != {"completion"}:
        raise ValueError("settings must name exactly completion")
    mode = settings["completion"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError("completion must be none or single_gap")
    return mode


def validate_grid(grid):
    if (type(grid) is not list or not 3 <= len(grid) <= 30
            or type(grid[0]) is not list or not 3 <= len(grid[0]) <= 30
            or any(type(row) is not list or len(row) != len(grid[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row)
                   for row in grid)):
        raise ValueError("grid must have exact list rows, dimensions 3..30 and integer colors 0..9")
    return [row[:] for row in grid]


def components(grid):
    remaining = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 7}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        found, stack = {start}, [start]
        while stack:
            r,c = stack.pop()
            for p in ((r-1,c),(r+1,c),(r,c-1),(r,c+1)):
                if p in remaining:
                    remaining.remove(p)
                    found.add(p)
                    stack.append(p)
        result.append(found)
    return result


def box(cells):
    return min(r for r,c in cells), min(c for r,c in cells), max(r for r,c in cells), max(c for r,c in cells)


def perimeter(bounds):
    r0,c0,r1,c1 = bounds
    return {(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)
            if r in (r0,r1) or c in (c0,c1)}


def _repair(grid):
    repaired = [row[:] for row in grid]
    added = []
    for comp in components(grid):
        bounds = box(comp)
        r0,c0,r1,c1 = bounds
        border = perimeter(bounds)
        missing = border - comp
        if r1-r0 >= 2 and c1-c0 >= 2 and comp <= border and len(missing) == 1:
            r,c = next(iter(missing))
            if grid[r][c] == 0:
                added.append([r,c])
                repaired[r][c] = 7
    return repaired, sorted(added)


def _fill(grid):
    out = [row[:] for row in grid]
    selected = []
    for comp in components(grid):
        bounds = box(comp)
        if comp == perimeter(bounds):
            selected.append(list(bounds))
            r0,c0,r1,c1 = bounds
            for r in range(r0+1,r1):
                for c in range(c0+1,c1):
                    if grid[r][c] == 0:
                        out[r][c] = 8
    return out, selected


def analyze(grid, settings):
    mode = settings_value(settings)
    source = validate_grid(grid)
    intermediate, added = _repair(source) if mode == "single_gap" else (source, [])
    output, eligible = _fill(intermediate)
    return {"intermediate":intermediate, "added_cells":added,
            "eligible_boxes":eligible, "output":output}


def first_stage(grid, settings):
    return analyze(grid,settings)["intermediate"]


def mirror(grid, settings):
    return analyze(grid,settings)["output"]


def program(settings):
    mode=settings_value(settings)
    return (HOME / ("canonical.rkt" if mode == "none" else "single_gap.rkt")).read_text()


def _rng(seed, label):
    raw=hashlib.sha256(f"af6e765bcc41/frames-v1/{seed}/{label}".encode()).digest()
    return random.Random(int.from_bytes(raw,"big"))


def _span(n, count):
    total = n-(count-1)
    lengths=[total//count+(i<total%count) for i in range(count)]
    offset=0
    result=[]
    for length in lengths:
        result.append((offset,length))
        offset += length+1
    return result


def _motif(kind, sh, sw, rng, dense=False, size=None):
    canvas=[[0]*sw for _ in range(sh)]
    top=1 if kind in ("blocked","diagonal") else 0
    left=1 if kind == "diagonal" else 0
    min_h=5 if kind == "inside_orange" else (4 if kind in ("colored","colored_gap") else 3)
    min_w=5 if kind == "inside_orange" else (4 if kind in ("two_gap","colored","colored_gap") else 3)
    mh,mw=sh-top,sw-left
    if mh<min_h or mw<min_w:
        raise ValueError(f"motif {kind} does not fit {sh}x{sw}")
    h=mh if dense or kind == "exact_edge" else rng.randint(min_h,mh)
    w=mw if dense or kind == "exact_edge" else rng.randint(min_w,mw)
    if kind == "exact_small":
        h=w=3
    if size is not None:
        h,w=size
        if not min_h<=h<=mh or not min_w<=w<=mw:
            raise ValueError(f"required teaching size does not fit {kind}")
    r0=top if kind in ("blocked","diagonal","exact_edge") else rng.randint(0,sh-h)
    c0=left if kind in ("diagonal","exact_edge") else rng.randint(0,sw-w)
    r1,c1=r0+h-1,c0+w-1
    color=rng.choice((1,2,3,4,5,6,9)) if kind in ("nonorange","nonorange_gap") else 7
    for r,c in perimeter((r0,c0,r1,c1)):
        canvas[r][c]=color
    gaps={"gap_top":(r0,c0+w//2),"gap_bottom":(r1,c0+w//2),
          "gap_left":(r0+h//2,c0),"gap_right":(r0+h//2,c1),
          "gap_corner":rng.choice(((r0,c0),(r0,c1),(r1,c0),(r1,c1))),
          "blocked":(r0,c0+w//2),"colored_gap":(r0,c0+w//2),
          "nonorange_gap":(r0,c0+w//2),"mixed_border":(r0,c0+w//2)}
    if kind in gaps:
        r,c=gaps[kind]
        canvas[r][c]=rng.choice((1,3,5,8)) if kind == "mixed_border" else 0
    if kind == "blocked":
        canvas[r0-1][c0+w//2]=7
    elif kind == "diagonal":
        canvas[r0-1][c0-1]=7
    elif kind == "two_gap":
        canvas[r0][c0+1]=canvas[r0][c0+2]=0
    elif kind == "tail":
        canvas[r0+1][c0+1]=7
    elif kind == "solid":
        for r in range(r0,r1+1):
            for c in range(c0,c1+1):
                canvas[r][c]=7
    elif kind == "inside_orange":
        canvas[r0+2][c0+2]=7
    if kind in ("colored","colored_gap"):
        canvas[r0+1][c0+1]=rng.choice((1,2,3,4,5,6,9))
        canvas[r1-1][c1-1]=8
    return canvas


def _scene(seed, label, h, w, rows, cols, kinds, dense=False, sizes=None):
    rng=_rng(seed,label)
    kinds=list(kinds)
    rng.shuffle(kinds)
    grid=[[0]*w for _ in range(h)]
    slots=[(r,c,sh,sw) for r,sh in _span(h,rows) for c,sw in _span(w,cols)]
    if len(slots) != len(kinds):
        raise ValueError("one constructive motif is required per slot")
    for kind,(r0,c0,sh,sw) in zip(kinds,slots):
        tile=_motif(kind,sh,sw,rng,dense,(sizes or {}).get(kind))
        for r,row in enumerate(tile):
            grid[r0+r][c0:c0+sw]=row
    if rng.randrange(2):
        grid=grid[::-1]
    if rng.randrange(2):
        grid=[row[::-1] for row in grid]
    if rng.randrange(2):
        grid=[list(row) for row in zip(*grid)]
    return grid


def _core(seed):
    return [
        _scene(seed,"core0",5,7,1,1,("exact_edge",),sizes={"exact_edge":(3,5)}),
        _scene(seed,"core1",5,5,1,1,("gap_corner",),sizes={"gap_corner":(3,3)}),
        _scene(seed,"core2",27,27,4,4,
               ("gap_top","gap_bottom","gap_left","gap_right","blocked","tail",
                "inside_orange","diagonal","nonorange","nonorange_gap","two_gap",
                "colored","colored_gap","exact_edge","mixed_border","exact_small"),
               sizes={"gap_top":(3,6)}),
    ]


def _extra(seed):
    return [
        _scene(seed,"extra0",9,11,2,2,("exact_small","gap_corner","nonorange","two_gap")),
        _scene(seed,"extra1",13,15,2,3,("exact_edge","gap_top","gap_right","two_gap","colored","mixed_border")),
        _scene(seed,"extra2",19,21,3,3,("exact_edge","gap_top","gap_bottom","gap_left","gap_right","gap_corner","nonorange","colored_gap","diagonal")),
    ]


def _queries(seed):
    small_rng=_rng(seed,"small")
    sh,sw=3,3+small_rng.randrange(2)
    kind=small_rng.choice(("exact_small","gap_corner","gap_top","nonorange","mixed_border"))
    small=_motif(kind,sh,sw,small_rng,True)
    bank=[small,
          _scene(seed,"query1",13,17,2,3,("blocked","gap_left","exact_edge","two_gap","colored_gap","nonorange")),
          _scene(seed,"query2",23,27,3,3,("exact_edge","gap_top","gap_bottom","gap_corner","blocked","tail","inside_orange","nonorange_gap","mixed_border")),
          _scene(seed,"query3",30,30,3,3,("exact_edge","gap_corner","gap_top","blocked","tail","colored","inside_orange","two_gap","nonorange"),True)]
    _rng(seed,"query-order").shuffle(bank)
    return bank


def generate(seed, settings, demos=3, queries=4):
    settings_value(settings)
    for name,value,lo,hi in (("seed",seed,0,2**63-1),("demos",demos,3,6),("queries",queries,1,4)):
        if type(value) is not int or not lo<=value<=hi:
            raise ValueError(f"{name} must be an exact integer in {lo}..{hi}")
    train=_core(seed)+_extra(seed)
    test=_queries(seed)
    all_inputs=train+test
    if len({str(g) for g in all_inputs}) != len(all_inputs):
        raise RuntimeError("Constructive bank contains duplicate inputs")
    return {"train":[{"input":g,"output":mirror(g,settings)} for g in train[:demos]],
            "test":[{"input":g,"output":mirror(g,settings)} for g in test[:queries]],
            "program_solution":program(settings)}
