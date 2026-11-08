"""Decode aligned gray tiles, optionally order by decoded-class frequency.

Outputs here are deterministic claims. Native qualification supplies independent
protected Racket execution and does not grant owner acceptance.
"""
from __future__ import annotations

from collections import Counter
import hashlib
from itertools import combinations
from pathlib import Path
import random

HOME=Path(__file__).resolve().parent
CELLS=tuple((r,c) for r in range(3) for c in range(3))
TOP=frozenset((0,c) for c in range(3))
BOTTOM=frozenset((2,c) for c in range(3))
CORNERS=((0,0),(0,2),(2,0),(2,2))
EDGES=((0,1),(1,0),(1,2),(2,1))
OTHER=tuple(frozenset(p) for p in combinations(CELLS,3) if frozenset(p) not in (TOP,BOTTOM))


def settings_value(settings):
    if type(settings) is not dict or set(settings)!={"order"}:
        raise ValueError("settings must name exactly order")
    value=settings["order"]
    if type(value) is not str or value not in ("input","frequency"):
        raise ValueError("order must be input or frequency")
    return value


def validate_grid(grid):
    if (type(grid) is not list or len(grid)!=3 or type(grid[0]) is not list
            or not 3<=len(grid[0])<=30 or len(grid[0])%3
            or any(type(row) is not list or len(row)!=len(grid[0])
                   or any(type(v) is not int or v not in (0,5) for v in row) for row in grid)):
        raise ValueError("grid must have exactly3list rows, width3..30divisibleby3, exact integer0/5cells")
    return [row[:] for row in grid]


def _decode(grid):
    labels=[]
    for start in range(0,len(grid[0]),3):
        cells={(r,c) for r in range(3) for c in range(3) if grid[r][start+c]==5}
        if len(cells)==1:
            label=4
        elif len(cells)==8:
            label=3
        elif cells==TOP:
            label=6
        elif cells==BOTTOM:
            label=1
        elif len(cells)==3:
            label=9
        else:
            label=0
        labels.append(label)
    return labels


def decode(grid):
    return _decode(validate_grid(grid))


def analyze(grid,settings):
    mode=settings_value(settings)
    labels=decode(grid)
    counts=Counter(labels)
    frequencies=[counts[v] for v in labels]
    permutation=list(range(len(labels)))
    if mode=="frequency":
        permutation.sort(key=lambda i:(-frequencies[i],labels[i],i))
    ordered=[labels[i] for i in permutation]
    output=[[v for label in ordered for v in [label]*3] for _ in range(3)]
    return {"labels":labels,"frequencies":frequencies,"permutation":permutation,
            "ordered_labels":ordered,"output":output}


def first_stage(grid,settings):
    settings_value(settings)
    return decode(grid)


def mirror(grid,settings):
    return analyze(grid,settings)["output"]


def program(settings):
    mode=settings_value(settings)
    return (HOME/("canonical.rkt" if mode=="input" else "frequency.rkt")).read_text()


def _rng(seed,label):
    key=hashlib.sha256(f"abee0b4bed48/frequency-v1/{seed}/{label}".encode()).digest()
    return random.Random(int.from_bytes(key,"big"))


def _cells(kind,rng):
    if kind.startswith("one"):
        pool=((1,1),) if kind=="one_center" else CORNERS if kind=="one_corner" else EDGES if kind=="one_edge" else CELLS
        return {rng.choice(pool)}
    if kind.startswith("eight"):
        pool=((1,1),) if kind=="eight_center" else CORNERS if kind=="eight_corner" else EDGES if kind=="eight_edge" else CELLS
        return set(CELLS)-{rng.choice(pool)}
    if kind=="top":
        return set(TOP)
    if kind=="bottom":
        return set(BOTTOM)
    if kind=="other_middle":
        return {(1,c) for c in range(3)}
    if kind=="other_diagonal":
        return rng.choice(({(0,0),(1,1),(2,2)},{(0,2),(1,1),(2,0)}))
    if kind=="other_vertical":
        c=rng.randrange(3)
        return {(r,c) for r in range(3)}
    if kind=="other_l":
        r,c=rng.randrange(2),rng.randrange(2)
        box={(r,c),(r+1,c),(r,c+1),(r+1,c+1)}
        return box-{rng.choice(sorted(box))}
    if kind=="other":
        return set(rng.choice(OTHER))
    if kind.startswith("fallback"):
        count=rng.choice((0,2,4,5,6,7,9)) if kind=="fallback" else int(kind[8:])
        if count not in (0,2,4,5,6,7,9):
            raise ValueError("fallback must have a non-classified gray count")
        return set(rng.sample(CELLS,count))
    raise ValueError(f"unknown constructive tile {kind}")


def _combine(tiles):
    return [[value for tile in tiles for value in tile[r]] for r in range(3)]


def _scene(seed,label,kinds,tie_guard=False,vertical=None,group_label=None):
    rng=_rng(seed,label)
    tiles=[]
    flip_rows,flip_cols=rng.randrange(2),rng.randrange(2)
    if vertical is not None:
        flip_rows=vertical
    for kind in kinds:
        points=_cells(kind,rng)
        tile=[[5 if (r,c) in points else 0 for c in range(3)] for r in range(3)]
        if flip_rows:
            tile=tile[::-1]
        if flip_cols:
            tile=[row[::-1] for row in tile]
        tiles.append(tile)
    rng.shuffle(tiles)
    if group_label is not None:
        grouped=[tile for tile in tiles if _decode(tile)[0]==group_label]
        others=[tile for tile in tiles if _decode(tile)[0]!=group_label]
        position=rng.randrange(len(others)+1)
        tiles=others[:position]+grouped+others[position:]
    if tie_guard:
        labels=_decode(_combine(tiles))
        assert labels.count(3)==labels.count(4)>0
        a,b=labels.index(3),labels.index(4)
        if a<b:
            tiles[a],tiles[b]=tiles[b],tiles[a]
    return _combine(tiles)


def _core(seed):
    vertical=_rng(seed,"core-vertical").randrange(2)
    return [
        _scene(seed,"core0",("eight_corner",)),
        _scene(seed,"core1",("one_center","one_corner","eight_center","eight_edge",
               "other_middle","other_diagonal","other_l","fallback9","bottom","bottom"),True,vertical,9),
        _scene(seed,"core2",("one_edge","eight_corner","top","other_vertical","fallback0"),True,vertical),
    ]


def _extra(seed):
    return [
        _scene(seed,"extra0",("one","eight","other")),
        _scene(seed,"extra1",("top","bottom","other","fallback")),
        _scene(seed,"extra2",("one","eight","top","bottom","other")),
    ]


def _queries(seed):
    choices=(("one","other"),("eight","top"),("fallback2","bottom"),("top","bottom"))
    small=_rng(seed,"small-kind").choice(choices)
    bank=[
        _scene(seed,"query0",small),
        _scene(seed,"query1",("one","eight","top","bottom","other","other","fallback5")),
        _scene(seed,"query2",("one","one","one","eight","eight","top","bottom","other","fallback4")),
        _scene(seed,"query3",("eight","eight","eight","eight","top","bottom","other","other","one","fallback6")),
    ]
    _rng(seed,"query-order").shuffle(bank)
    return bank


def generate(seed,settings,demos=3,queries=4):
    settings_value(settings)
    for name,value,low,high in (("seed",seed,0,2**63-1),("demos",demos,3,6),("queries",queries,1,4)):
        if type(value) is not int or not low<=value<=high:
            raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    train=_core(seed)+_extra(seed)
    test=_queries(seed)
    if len({str(g) for g in train+test})!=len(train)+len(test):
        raise RuntimeError("Constructive input bank contains duplicates")
    return {"train":[{"input":g,"output":mirror(g,settings)} for g in train[:demos]],
            "test":[{"input":g,"output":mirror(g,settings)} for g in test[:queries]],
            "program_solution":program(settings)}
