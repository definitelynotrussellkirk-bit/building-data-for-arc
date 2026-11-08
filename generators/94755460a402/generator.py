"""Semantic generator for ARC task 94755460a402.

Two code cells select a colored rectangular frame and a transformation.  Crop
the chosen frame's strict interior to its nonzero content, then transform it.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "94755460a402"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "7c0a4d00e188"
SUMMARY = "Select the first rectangular frame matching (0,0), crop its interior to content, and apply the command at (0,1)."
INVARIANTS = [
    "background is literal color 0",
    "the first two cells encode selector and command",
    "two through four exact rectangular frames have nonempty interiors",
    "the first selector-colored frame is chosen",
    "commands mean clockwise, 180, left-right flip, transpose, or identity",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_train_3", "public_train_4", "public_test_1")
GENERAL_SPECS = {
    "two_first_cw": (2, 0, 1, False),
    "two_last_180": (2, 1, 2, False),
    "three_first_flip": (3, 0, 3, False),
    "three_middle_transpose": (3, 1, 4, False),
    "three_last_identity": (3, 2, 5, False),
    "four_first_180": (4, 0, 2, False),
    "four_middle_flip": (4, 2, 3, False),
    "four_last_cw": (4, 3, 1, False),
    "three_duplicate_first_transpose": (3, 0, 4, True),
}
GENERAL_PROFILES = tuple(GENERAL_SPECS)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {"scene_profile": {"type": "str", "default": "weighted exact-public and frame-command lessons", "valid": "public_train_1|public_train_2|public_train_3|public_train_4|public_test_1|two_first_cw|two_last_180|three_first_flip|three_middle_transpose|three_last_identity|four_first_180|four_middle_flip|four_last_cw|three_duplicate_first_transpose"}}

_PUBLIC_BLOBS = {
    "public_train_1": "910000000000000000/000000000000000000/000111110009999900/000120310009200900/000124010009340900/000100010009045900/000111110009000900/000000000009999900/000006666600000000/000006220600000000/000006030600000000/000006666600000000/000000000000000000",
    "public_train_2": "8200000000000000000/0000000000000000000/0088888800000000000/0085060800111111000/0080700800120301000/0080000800124001000/0080000800100001000/0088888800100001000/0000000000111111000/0000000000009999900/0000000000009220900/0000000000009030900/0000000000009999900/0000000000000000000",
    "public_train_3": "13000000000000000000/00000000000000000000/00001111111009999900/00001200001009220900/00001340001009030900/00001045001009000900/00001000001009999900/00001111111000000000/00000000666666000000/00000000650606000000/00000000607006000000/00000000666666000000/00000000000000000000",
    "public_train_4": "64000000000000000000/00000000000000000000/00000000000000000000/00099999900066666600/00092030900062000600/00092400900063400600/00090000900060450600/00090000900060000600/00099999900060000600/00000000000066666600/00000011111000000000/00000012201000000000/00000010301000000000/00000011111000000000/00000000000000000000",
    "public_test_1": "910000000000000000/000000000000000000/009999990011111100/009506090012030100/009070090012400100/009000090010000100/009000090010000100/009999990010000100/000000000011111100/000066666000000000/000062206000000000/000060306000000000/000066666000000000/000000000000000000",
}
_PUBLIC_INPUTS = {name: [[int(v) for v in row] for row in blob.split("/")] for name, blob in _PUBLIC_BLOBS.items()}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}
_PROFILE_KEYS = {(count, index, cmd, duplicate): name for name, (count, index, cmd, duplicate) in GENERAL_SPECS.items()}


def _valid(grid):
    if not isinstance(grid, (list, tuple)) or not grid: return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or len(grid[0]) < 2: return ["grid needs at least two columns"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid): return ["grid must be rectangular"]
    if any(isinstance(v, bool) or not isinstance(v, int) or not 0 <= v <= 9 for row in grid for v in row): return ["cells must be ARC colors"]
    return []


def _components(grid):
    h, w = len(grid), len(grid[0]); seen = set(); out = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen: continue
            todo=[(r,c)]; cells=set()
            while todo:
                rr,cc=todo.pop()
                if not 0<=rr<h or not 0<=cc<w or (rr,cc) in seen or grid[rr][cc]!=color: continue
                seen.add((rr,cc));cells.add((rr,cc));todo += [(rr-1,cc),(rr+1,cc),(rr,cc-1),(rr,cc+1)]
            r1=min(x for x,y in cells);c1=min(y for x,y in cells);r2=max(x for x,y in cells);c2=max(y for x,y in cells)
            out.append({"color":color,"cells":cells,"bbox":(r1,c1,r2,c2)})
    return out


def _frame_cells(r1,c1,r2,c2):
    return {(r,c) for r in range(r1,r2+1) for c in range(c1,c2+1) if r in (r1,r2) or c in (c1,c2)}


def _crop(grid):
    cells=[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v!=0]
    if not cells: return None
    r1=min(r for r,c in cells);c1=min(c for r,c in cells);r2=max(r for r,c in cells);c2=max(c for r,c in cells)
    return [row[c1:c2+1] for row in grid[r1:r2+1]]


def _apply(grid, cmd):
    if cmd==1: return [list(row) for row in zip(*grid[::-1])]
    if cmd==2: return [row[::-1] for row in grid[::-1]]
    if cmd==3: return [row[::-1] for row in grid]
    if cmd==4: return [list(row) for row in zip(*grid)]
    return [row[:] for row in grid]


def _analysis(grid):
    errors=_valid(grid); result={"errors":errors,"scene_profile":None}
    if errors:return result
    selector, raw_cmd=grid[0][0],grid[0][1]
    if selector==0: errors.append("selector must be nonzero")
    if raw_cmd==0: errors.append("command must be nonzero")
    frames=[]
    for obj in _components(grid):
        r1,c1,r2,c2=obj["bbox"]
        if r2-r1+1>=3 and c2-c1+1>=3 and obj["cells"]==_frame_cells(r1,c1,r2,c2): frames.append(obj)
    if not 2<=len(frames)<=4: errors.append("scene must contain two through four exact frames")
    matches=[i for i,obj in enumerate(frames) if obj["color"]==selector]
    if not matches: errors.append("selector must match at least one frame"); return result
    selected_index=matches[0]; chosen=frames[selected_index];r1,c1,r2,c2=chosen["bbox"]
    motif=[row[c1+1:c2] for row in grid[r1+1:r2]]; cropped=_crop(motif)
    if cropped is None: errors.append("selected frame interior must contain nonzero content"); return result
    branch=raw_cmd if raw_cmd in (1,2,3,4) else 5; output=_apply(cropped,raw_cmd)
    duplicate=len(matches)>1
    profile=_PUBLIC_SIGNATURES.get(tuple(map(tuple,grid)))
    if profile is None and not errors: profile=_PROFILE_KEYS.get((len(frames),selected_index,branch,duplicate))
    if profile not in SCENE_PROFILES: errors.append("frame-count/selection/command tuple does not match a declared profile")
    result.update({"selector":selector,"raw_cmd":raw_cmd,"command_branch":branch,"frames":frames,"matching_indices":tuple(matches),"selected_index":selected_index,"chosen":chosen,"motif":motif,"cropped":cropped,"output":output,"scene_profile":profile,"errors":errors})
    return result


def canonical_profile_signature(grid):
    a=_analysis(grid);p=a.get("scene_profile");return p if not a["errors"] and p in PUBLIC_PROFILES else None

def observe_overrides(grid):
    a=_analysis(grid)
    if a["errors"]: raise ValueError("; ".join(a["errors"]))
    return {"scene_profile":a["scene_profile"]}

def rule_mirror(grid):
    a=_analysis(grid)
    if a["errors"]: raise ValueError("; ".join(a["errors"]))
    return [row[:] for row in a["output"]]

def _band(d):
    if d in (None,"medium"):return "medium"
    if d in ("easy","hard"):return d
    raise ValueError(f"unknown difficulty: {d!r}")

def _draw_frame(g,r1,c1,r2,c2,color):
    for r,c in _frame_cells(r1,c1,r2,c2):g[r][c]=color

def _general(rng,profile,band):
    count,selected,branch,duplicate=GENERAL_SPECS[profile]
    ranges={"easy":(13,18,15,22),"medium":(15,20,18,26),"hard":(18,23,22,30)}
    hlo,hhi,wlo,whi=ranges[band];h=rng.randint(hlo,hhi);w=rng.randint(wlo,whi)
    g=[[0]*w for _ in range(h)];g[0][1]=rng.choice((5,6,7,8,9)) if branch==5 else branch
    sh=(h-3)//2;sw=(w-1)//2
    slots=[(2,0,sh,sw),(2,sw+1,sh,w-sw-1),(3+sh,0,h-3-sh,sw),(3+sh,sw+1,h-3-sh,w-sw-1)]
    colors=rng.sample(range(1,10),count);selector=colors[selected]
    if duplicate: colors[-1]=selector
    for i,(sr,sc,hh,ww) in enumerate(slots[:count]):
        fh=rng.randint(4,max(4,hh));fw=rng.randint(4,max(4,ww));r1=sr;c1=sc+rng.randint(0,ww-fw)
        _draw_frame(g,r1,c1,r1+fh-1,c1+fw-1,colors[i])
        ih,iw=fh-2,fw-2;ch=rng.randint(2,ih);cw=rng.randint(2,iw);offr=rng.randint(0,ih-ch);offc=rng.randint(0,iw-cw)
        positions={(0,0),(ch-1,cw-1)};allp=[(r,c) for r in range(ch) for c in range(cw) if (r,c) not in positions];rng.shuffle(allp);positions.update(allp[:rng.randint(1,min(6,len(allp)))])
        palette=[v for v in range(1,10) if v!=colors[i]]
        for rr,cc in positions:g[r1+1+offr+rr][c1+1+offc+cc]=rng.choice(palette)
    g[0][0]=selector
    return g

def generate(seed,sample_index,*,difficulty=None,**overrides):
    unknown=set(overrides)-{"scene_profile"}
    if unknown:raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested=overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:raise ValueError(f"unknown scene_profile: {requested!r}")
    band=_band(difficulty);ctx=gen_ctx(seed=seed,sample_index=sample_index,version=VERSION,task_id=TASK_ID,difficulty=band,overrides=overrides)
    profile=ctx.draw_choice("scene_profile",list(PUBLIC_PROFILES)+[p for p in GENERAL_PROFILES for _ in range(3)])
    if profile in PUBLIC_PROFILES:return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general(ctx.draw_rng("layout"),profile,band)

def self_check(grid,*,difficulty=None,meta=None):return list(_analysis(grid)["errors"])
