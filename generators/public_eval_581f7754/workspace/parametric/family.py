"""Authoring family for ARC public parent 581f7754.

Border singleton cells define colored horizontal or vertical target lines.
Every other foreground component contains a rare marker color.  The canonical
setting sends the marker to the line with the same color; the alternate sends
it to the geometrically nearest anchor line.
"""
from __future__ import annotations
from collections import Counter, deque
import copy
import hashlib
import json
import random

SETTINGS = ("matching_color", "nearest_line")
RIVALS = (
    "opposite_assignment",
    "all_to_first",
    "all_to_middle",
    "all_to_last",
    "no_block_nudge",
    "marker_only",
    "identity",
)
D4 = ((-1,0),(1,0),(0,-1),(0,1))
SHAPES = (
    ((-1,0),(-1,1),(0,0),(0,1),(1,0),(1,1)),
    ((-1,-1),(-1,0),(0,-1),(0,0),(0,1),(1,-1),(1,0)),
    tuple((r,c) for r in (-1,0,1) for c in (-1,0,1)),
    ((-1,0),(0,-1),(0,0),(0,1),(1,0),(1,1)),
    ((-1,-1),(-1,0),(-1,1),(0,-1),(0,0),(1,-1),(1,0)),
)
MARKER_COLORS = (2,4,6)
FILL_COLORS = (1,3,5,7,9)


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in [{low}, {high}]")
    return value


def _grid(grid):
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    w=len(grid[0])
    if any(type(row) is not list or len(row)!=w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(v) is not int or not 0<=v<=9 for row in grid for v in row):
        raise ValueError("grid cells must be integers 0..9")
    return grid


def _components(cells):
    rem=set(cells);out=[]
    while rem:
        start=min(rem);rem.remove(start);q=deque([start]);comp={start}
        while q:
            r,c=q.popleft()
            for dr,dc in D4:
                p=(r+dr,c+dc)
                if p in rem:
                    rem.remove(p);comp.add(p);q.append(p)
        out.append(comp)
    return sorted(out,key=lambda x:min(x))


def _side(point,h,w):
    r,c=point
    if c==0:return "left"
    if c==w-1:return "right"
    if r==0:return "top"
    if r==h-1:return "bottom"
    raise ValueError("anchor is not on the border")


def _full_centered_three(cells, marker):
    rs=[r for r,c in cells];cs=[c for r,c in cells]
    return (len(cells)==9 and max(rs)-min(rs)==2 and max(cs)-min(cs)==2
            and len(cells)==9
            and marker==((min(rs)+max(rs))//2,(min(cs)+max(cs))//2))


def analyze(grid):
    g=_grid(grid);h=len(g);w=len(g[0]);bg=Counter(v for row in g for v in row).most_common(1)[0][0]
    foreground={(r,c) for r in range(h) for c in range(w) if g[r][c]!=bg}
    comps=_components(foreground)
    anchors=[];objects=[]
    for cells in comps:
        if len(cells)==1:
            p=next(iter(cells))
            if p[0] in (0,h-1) or p[1] in (0,w-1):
                anchors.append({"point":p,"color":g[p[0]][p[1]],"side":_side(p,h,w)})
                continue
        objects.append(cells)
    anchors.sort(key=lambda a:a["point"])
    if not anchors or not objects:
        raise ValueError("expected border anchors and movable objects")
    anchor_colors={a["color"] for a in anchors}
    records=[]
    for cells in objects:
        counts=Counter(g[r][c] for r,c in cells if g[r][c] in anchor_colors)
        if not counts:
            raise ValueError("movable object lacks an anchor-colored marker")
        marker_color=min(counts,key=lambda color:(counts[color],color))
        marker=min((p for p in cells if g[p[0]][p[1]]==marker_color))
        records.append({"cells":set(cells),"marker":marker,"marker_color":marker_color,
                        "full_centered_three":_full_centered_three(cells,marker)})
    records.sort(key=lambda rec:min(rec["cells"]))
    return {"height":h,"width":w,"background":bg,"anchors":anchors,"objects":records}


def _line_distance(marker, anchor):
    r,c=marker;ar,ac=anchor["point"]
    return abs(r-ar) if anchor["side"] in ("left","right") else abs(c-ac)


def _choose_anchor(record, anchors, setting, forced=None):
    if forced is not None:
        if forced=="first":return anchors[0]
        if forced=="middle":return anchors[len(anchors)//2]
        if forced=="last":return anchors[-1]
        raise ValueError("bad forced anchor")
    if setting=="matching_color":
        candidates=[a for a in anchors if a["color"]==record["marker_color"]]
        if not candidates:raise ValueError("no matching-color anchor")
        return min(candidates,key=lambda a:(abs(a["point"][0]-record["marker"][0])+
                                            abs(a["point"][1]-record["marker"][1]),a["point"]))
    if setting=="nearest_line":
        return min(anchors,key=lambda a:(_line_distance(record["marker"],a),a["point"]))
    raise ValueError("unknown assignment setting")


def _assignment(record, anchor, *, block_nudge=True):
    mr,mc=record["marker"];ar,ac=anchor["point"];dr=dc=0
    if anchor["side"] in ("left","right"):dr=ar-mr
    else:dc=ac-mc
    if block_nudge and record["full_centered_three"]:
        if anchor["side"]=="left":dc-=1
        elif anchor["side"]=="right":dc+=1
        elif anchor["side"]=="top":dr-=1
        else:dr+=1
    return dr,dc


def intermediate(grid, setting="matching_color"):
    if setting not in SETTINGS:raise ValueError("unknown assignment setting")
    info=analyze(grid)
    objects=[];assignments=[]
    for i,record in enumerate(info["objects"]):
        objects.append({"index":i,"cells":[list(p) for p in sorted(record["cells"])],
                        "marker":list(record["marker"]),"marker_color":record["marker_color"],
                        "full_centered_three":record["full_centered_three"]})
        anchor=_choose_anchor(record,info["anchors"],setting)
        dr,dc=_assignment(record,anchor)
        assignments.append({"object":i,"anchor":list(anchor["point"]),"anchor_color":anchor["color"],
                            "side":anchor["side"],"shift":[dr,dc]})
    return {"background":info["background"],"anchors":copy.deepcopy(info["anchors"]),
            "objects":objects,"assignments":assignments}


def _solve(grid, setting, *, forced=None, block_nudge=True, marker_only=False):
    if setting not in SETTINGS:raise ValueError("unknown assignment setting")
    g=_grid(grid);info=analyze(g);h=info["height"];w=info["width"];bg=info["background"]
    out=[row[:] for row in g]
    for rec in info["objects"]:
        for r,c in rec["cells"]:out[r][c]=bg
    for rec in info["objects"]:
        anchor=_choose_anchor(rec,info["anchors"],setting,forced)
        dr,dc=_assignment(rec,anchor,block_nudge=block_nudge)
        cells={rec["marker"]} if marker_only else rec["cells"]
        for r,c in sorted(cells):
            nr,nc=r+dr,c+dc
            if 0<=nr<h and 0<=nc<w:out[nr][nc]=g[r][c]
    return out


def solve(grid, setting="matching_color"):
    return _solve(grid,setting)


def solve_rival(grid, setting, name):
    if name not in RIVALS:raise ValueError("unknown rival")
    if name=="opposite_assignment":
        return solve(grid,"nearest_line" if setting=="matching_color" else "matching_color")
    if name=="all_to_first":return _solve(grid,setting,forced="first")
    if name=="all_to_middle":return _solve(grid,setting,forced="middle")
    if name=="all_to_last":return _solve(grid,setting,forced="last")
    if name=="no_block_nudge":return _solve(grid,setting,block_nudge=False)
    if name=="marker_only":return _solve(grid,setting,marker_only=True)
    if name=="identity":return copy.deepcopy(grid)
    raise AssertionError(name)


def _rng(seed,tag):
    data=json.dumps([seed,tag],sort_keys=True,separators=(",",":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(data).digest()[:16],"big"))


def _lanes(length,n):
    if n==1:return [length//2]
    return [round(2+i*(length-6)/(n-1)) for i in range(n)]


def _vertical_lanes(length,n):
    """Keep bodies at least one blank row from top/bottom border anchors."""
    if n==1:return [length//2]
    return [round(3+i*(length-7)/(n-1)) for i in range(n)]


def make_scene(seed,tag,h,w,*,orientation,stress):
    integer(seed,0,2**63-1,"seed");integer(h,12,30,"height");integer(w,12,30,"width")
    if orientation not in ("rows","columns"):raise ValueError("orientation must be rows or columns")
    rng=_rng(seed,tag);bg=8 if (seed+int(rng.random()*1000))%2==0 else 0
    g=[[bg]*w for _ in range(h)]
    n=5 if stress else 3
    marker_colors=list(MARKER_COLORS);rng.shuffle(marker_colors)
    if orientation=="rows":
        targets=[2,h//2,h-3];side="left" if rng.randrange(2)==0 else "right";edge=0 if side=="left" else w-1
        for i,row in enumerate(targets):g[row][edge]=marker_colors[i]
        centers=_lanes(w,n)
        for i in range(n):
            shape=SHAPES[i];marker_color=marker_colors[i%3];fill=FILL_COLORS[i]
            mr=targets[(i+1)%3];mc=centers[i]
            for dr,dc in shape:g[mr+dr][mc+dc]=fill
            g[mr][mc]=marker_color
    else:
        targets=[2,w//2,w-3];side="top" if rng.randrange(2)==0 else "bottom";edge=0 if side=="top" else h-1
        for i,col in enumerate(targets):g[edge][col]=marker_colors[i]
        centers=_vertical_lanes(h,n)
        for i in range(n):
            shape=SHAPES[i];marker_color=marker_colors[i%3];fill=FILL_COLORS[i]
            mr=centers[i];mc=targets[(i+1)%3]
            for dr,dc in shape:g[mr+dr][mc+dc]=fill
            g[mr][mc]=marker_color
    if solve(g,"matching_color")==solve(g,"nearest_line"):
        raise AssertionError("scene does not distinguish assignment settings")
    return g


def generate(seed,settings,demos,queries):
    integer(seed,0,2**63-1,"seed");integer(demos,2,6,"demos");integer(queries,1,4,"queries")
    if type(settings) is not dict or set(settings)!={"assignment"} or settings["assignment"] not in SETTINGS:
        raise ValueError("settings must be exactly assignment=matching_color|nearest_line")
    setting=settings["assignment"]
    train_shapes=[(12,14),(14,16),(16,18),(18,20),(20,22),(22,24)]
    query_shapes=[(14,16),(18,20),(24,27),(30,30)]
    def pair(i,shape,query=False):
        orientation="rows" if i%2==0 else "columns"
        g=make_scene(seed,["query" if query else "demo",i],*shape,orientation=orientation,stress=query and i>=2)
        return {"input":g,"output":solve(g,setting)}
    train=[pair(i,train_shapes[i]) for i in range(demos)]
    bank=[pair(i,s,True) for i,s in enumerate(query_shapes)]
    return {"train":train,"test":copy.deepcopy(bank[:queries]),"private_query_bank":bank}


def self_check(grid):
    issues=[]
    try:
        info=analyze(grid)
        if len(info["anchors"])<3:issues.append("fewer than three anchors")
        if solve(grid,"matching_color")==solve(grid,"nearest_line"):issues.append("settings do not differ")
    except Exception as exc:issues.append(str(exc))
    return issues


def dependency():
    return {
        "step_a":"Extract border singleton anchors and movable components, identify each component's rare anchor-colored marker, and assign a target line.",
        "intermediate":"The ordered per-object marker, selected anchor, side, and translation vector.",
        "step_b":"Erase original movable components and redraw every colored cell using those vectors, including the centered 3x3 block nudge toward its anchor side.",
        "why":"The renderer cannot know either translation axis or destination line until the input-dependent anchor assignment has been computed.",
    }
