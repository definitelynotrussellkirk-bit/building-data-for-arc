"""Expand 4-isolated cells, not arbitrary foreground, into clipped pluses.

Helpful lessons cycle interior, boundary+domino, diagonal-pair+domino scenes.
Three consecutive demonstrations at fixed seed refute the declared shortcuts.
Different-color expansion collisions are deliberately excluded from training:
Racket has a row-major first-writer policy, but canonical examples do not teach it.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = TASK_ID = "0f26224a6da3"
VERSION = "3.0.0"
RULE_HASH = "867443694c3b"
SUMMARY = (
    "Zero-background 7..15 grids with exactly 2..5 four-isolated sources. "
    "Sources expand one step in four cardinal directions, clipped at borders; "
    "connected distractor cells remain unchanged. A three-scene curriculum mixes "
    "interior sources, boundary sources with a domino, and same-color diagonal "
    "sources with a domino. No different-color expansion collisions."
)
INVARIANTS = [
    "background is zero; cells are integers 0..9; dimensions 7..15",
    "2..5 four-isolated active sources, with at most one inert two-cell domino",
    "no different-color source expansions compete for the same blank cell",
    "at least one blank cardinal neighbor is filled; helpful draws are nonidentity",
]
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
PALETTES = {"warm": (2,4,6,7,9), "cool": (1,3,5,8),
            "broad": (1,2,3,4,5,6,7,8,9), "primary": (1,2,4)}
HELPFUL_TEXTURES = PALETTE_KINDS
DEGENERATE_TEXTURES = ("no_cells", "full_cells", "full_grid")
SCHEDULE_PROFILES = ("interior", "edge_distractor", "diagonal_distractor")
AXES = {
    "grid_h": {"type":"int", "default":"rng 7..9 interior; 7..15 otherwise", "valid":"7..15"},
    "grid_w": {"type":"int", "default":"rng 7..9 interior; 7..15 otherwise", "valid":"7..15"},
    "n_cells": {"type":"int", "default":"easy 2..3, medium 2..4, hard 3..5", "valid":"2..5",
                "doc":"Exact number of four-isolated active sources, excluding the domino."},
    "palette_kind": {"type":"enum", "default":"rng", "valid":"|".join(PALETTE_KINDS)},
    "scene": {"type":"enum", "default":"three-scene cycle", "valid":"|".join(SCHEDULE_PROFILES)},
    "texture": {"type":"enum", "default":"alias for palette_kind", "valid":"|".join(HELPFUL_TEXTURES),
                "doc":"Degenerate diagnostic names are opt-in, outside this helpful axis domain."},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"texture": a, "palette_kind": b} for a in PALETTE_KINDS for b in PALETTE_KINDS if a != b
] + [{"texture": name, "n_cells": None} for name in DEGENERATE_TEXTURES] + [
    {"texture": name, "scene": None} for name in DEGENERATE_TEXTURES]
_DIRS4 = ((-1,0),(1,0),(0,-1),(0,1))
_DIRS8 = tuple((dr,dc) for dr in (-1,0,1) for dc in (-1,0,1) if dr or dc)


def schedule_profile(seed, sample_index, difficulty=None):
    """Only guarantees fixed-seed, consecutive-index lessons without scene overrides."""
    return SCHEDULE_PROFILES[(seed + sample_index) % len(SCHEDULE_PROFILES)]


def _neighbors(r, c, h, w, dirs=_DIRS4):
    return [(r+dr,c+dc) for dr,dc in dirs if 0 <= r+dr < h and 0 <= c+dc < w]


def _sources(grid, dirs=_DIRS4):
    h,w=len(grid),len(grid[0])
    return [(r,c) for r in range(h) for c in range(w) if grid[r][c] != 0
            and all(grid[nr][nc] == 0 for nr,nc in _neighbors(r,c,h,w,dirs))]


def _distance(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


def _place(rng, h, w, n, scene):
    """Bounded rejection with exact cardinalities; no truncation/fallback lattice."""
    all_cells = [(r,c) for r in range(h) for c in range(w)]
    interior = [(r,c) for r in range(1,h-1) for c in range(1,w-1)]
    for _ in range(256):
        if scene == "edge_distractor":
            # Both corners and noncorner edges have positive probability.
            corners = [(0,0),(0,w-1),(h-1,0),(h-1,w-1)]
            edges = [(r,c) for r,c in all_cells if r in (0,h-1) or c in (0,w-1)]
            points = [rng.choice(corners if rng.randrange(2) == 0 else edges)]
        elif scene == "diagonal_distractor":
            r,c = rng.randrange(1,h-2),rng.randrange(1,w-2)
            points = [(r,c),(r+1,c+1)] if rng.randrange(2) else [(r+1,c),(r,c+1)]
        else:
            points = []
        candidates = list(interior if scene == "interior" else all_cells)
        rng.shuffle(candidates)
        for p in candidates:
            if len(points) == n:
                break
            if all(_distance(p,q) >= 3 for q in points):
                points.append(p)
        if len(points) != n:
            continue
        if scene == "interior":
            return points, []
        dominos = [(p,q) for p in all_cells for q in _neighbors(*p,h,w)
                   if p < q and all(_distance(x,s) >= 3 for x in (p,q) for s in points)]
        if dominos:
            return points, list(rng.choice(dominos))
    raise ValueError("could not place exact n_cells and scene in grid_h/grid_w after 256 attempts")


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for key,lo,hi in (("grid_h",7,15),("grid_w",7,15),("n_cells",2,5)):
        if key in overrides and (type(overrides[key]) is not int or not lo <= overrides[key] <= hi):
            raise ValueError(f"{key} must be an integer in {lo}..{hi}")
    for key,legal in (("palette_kind", PALETTE_KINDS),("scene", SCHEDULE_PROFILES),
                      ("texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES)):
        if key in overrides and overrides[key] not in legal:
            raise ValueError(f"{key} must be one of {legal}")
    texture = overrides.get("texture")
    if texture in HELPFUL_TEXTURES and overrides.get("palette_kind", texture) != texture:
        raise ValueError("texture and palette_kind select incompatible palettes")
    if texture in DEGENERATE_TEXTURES and ("n_cells" in overrides or "scene" in overrides):
        raise ValueError("diagnostic texture is incompatible with n_cells/scene")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    effective = dict(overrides)
    texture = overrides.get("texture")
    if texture in HELPFUL_TEXTURES:
        effective["palette_kind"] = texture
    # The schedule is observable via scene, not an additional hidden random draw.
    effective.setdefault("scene", schedule_profile(seed,sample_index,difficulty))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=effective)
    scene = ctx.draw_choice("scene", SCHEDULE_PROFILES)
    h = ctx.draw_int("grid_h",7,15 if "grid_h" in overrides or scene != "interior" else 9)
    w = ctx.draw_int("grid_w",7,15 if "grid_w" in overrides or scene != "interior" else 9)
    kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    pool = PALETTES[kind]
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture,h,w,pool[0])
    lo,hi = {"easy":(2,3), "medium":(2,4), "hard":(3,5)}.get(difficulty,(2,4))
    n = ctx.draw_int("n_cells",2 if "n_cells" in overrides else lo,
                     5 if "n_cells" in overrides else hi)
    points, domino = _place(ctx.draw_rng("layout"),h,w,n,scene)
    colors = ctx.draw_rng("colors")
    g = full_grid(h,w,0)
    for r,c in points:
        g[r][c] = colors.choice(pool)
    if scene == "diagonal_distractor":
        r,c=points[1]
        g[r][c]=g[points[0][0]][points[0][1]]
    for r,c in domino:
        g[r][c] = colors.choice(pool)
    return g


def _draw_from_degenerate(name,h,w,color):
    g=full_grid(h,w,0)
    if name == "full_grid":
        return full_grid(h,w,color)
    if name == "full_cells":
        # Diagnostic over-density: >=9 active dots, beyond helpful 2..5.
        for r in range(1,h,2):
            for c in range(1,w,2):
                g[r][c]=color
    return g


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid,(list,tuple)) or not grid or not isinstance(grid[0],(list,tuple)) or not grid[0]:
        return ["grid must be nonempty and rectangular"]
    h,w=len(grid),len(grid[0])
    if any(not isinstance(row,(list,tuple)) or len(row)!=w for row in grid):
        return ["grid must be nonempty and rectangular"]
    if any(type(v) is not int or not 0 <= v <= 9 for row in grid for v in row):
        return ["grid cells must be integer colors 0..9, not booleans"]
    if not (7 <= h <= 15 and 7 <= w <= 15):
        return ["helpful grid dimensions must be 7..15"]
    points=_sources(grid)
    if not 2 <= len(points) <= 5:
        return ["helpful grid needs 2..5 four-isolated active sources"]
    inert={(r,c) for r in range(h) for c in range(w) if grid[r][c]} - set(points)
    if inert and (len(inert)!=2 or _distance(*tuple(inert)) != 1):
        return ["inert foreground must be one two-cell cardinal domino"]
    targets={}
    for r,c in points:
        for p in _neighbors(r,c,h,w):
            if grid[p[0]][p[1]] == 0:
                if p in targets and targets[p] != grid[r][c]:
                    return ["different-color expansion fronts share a blank target"]
                targets[p] = grid[r][c]
    if not targets:
        return ["no observable expansion"]
    return []


def strict_canonical_like(grid):
    errors=self_check(grid)
    if errors:
        return errors
    h,w=len(grid),len(grid[0]); points=_sources(grid)
    if not (7 <= h <= 11 and 7 <= w <= 11):
        return ["outside compact canonical-like size range"]
    if sum(v!=0 for row in grid for v in row) != len(points):
        return ["canonical examples have no connected distractor"]
    if any(r in (0,h-1) or c in (0,w-1) for r,c in points):
        return ["canonical sources are interior"]
    if any(_distance(a,b)<3 for i,a in enumerate(points) for b in points[i+1:]):
        return ["canonical expansion fronts do not overlap"]
    return []


def observe_overrides(grid):
    return {"grid_h":len(grid),"grid_w":len(grid[0]),"n_cells":len(_sources(grid))}


def _paint(grid, points):
    out=[list(row) for row in grid];h,w=len(grid),len(grid[0])
    for r,c in sorted(points):
        for nr,nc in _neighbors(r,c,h,w):
            if out[nr][nc] == 0:
                out[nr][nc]=grid[r][c]
    return out


def rule_mirror(grid):
    """Diagnostic Python mirror, never a replacement label authority."""
    return _paint(grid,_sources(grid))


def _expand_every_foreground(grid):
    return _paint(grid,[(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v])


def _interior_only(grid):
    h,w=len(grid),len(grid[0])
    return _paint(grid,[(r,c) for r,c in _sources(grid) if 0<r<h-1 and 0<c<w-1])


def _eight_isolation(grid):
    return _paint(grid,_sources(grid,_DIRS8))


SEMANTIC_RIVALS = {"expand_every_foreground":_expand_every_foreground,
                   "interior_only":_interior_only,"eight_neighbor_isolation":_eight_isolation}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _refutes(name):
    return lambda grid: self_check(grid)==[] and SEMANTIC_RIVALS[name](grid)!=rule_mirror(grid)


SEMANTIC_WITNESSES = {name:_refutes(name) for name in SEMANTIC_RIVALS}
WITNESS_RIVALS = {name:[name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query) -> list[str]:
    """Finite-rival check, NOT a proof of uniqueness over all possible rules."""
    reasons=[]
    for i,demo in enumerate(demos):
        if self_check(demo["input"]):
            reasons.append(f"demo {i} outside helpful domain")
        elif rule_mirror(demo["input"])!=demo["output"]:
            reasons.append(f"demo {i} output disagrees with rule mirror")
    if self_check(query["input"]):
        reasons.append("query outside helpful domain")
    for name,rival in LESSON_COMPETITORS.items():
        if all(rival(d["input"])==d["output"] for d in demos):
            reasons.append(f"declared rival {name} survives all demonstrations")
    return reasons
