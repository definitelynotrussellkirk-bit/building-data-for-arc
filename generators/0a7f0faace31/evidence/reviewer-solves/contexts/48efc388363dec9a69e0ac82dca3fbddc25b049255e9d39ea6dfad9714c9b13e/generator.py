"""Guide-bbox selection with connected glyphs and explicit teaching witnesses.

The unchanged canonical Racket rule selects the first monochromatic 4-connected
component whose floor bbox center lies inside the inclusive bbox of ALL 7s,
then takes its raw crop. Background is 5. This module creates inputs only;
Python mirrors/rivals below are authoring checks, never label authorities.

Defaults cycle teaching, teaching, ordinary by sample index. The compound
teaching boards distinguish eighteen canonical-fitting rivals. Other textures
retain varied connected glyphs, positions and frame styles. See notes.md for
scope, exact override incompatibilities and remaining distribution limits.
"""
from __future__ import annotations

from functools import partial

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.shape import RING_3X3

GENERATOR_ID = "0a7f0faace31"
TASK_ID = GENERATOR_ID
RULE_HASH = "b5a68207c8ed"
VERSION = "3.0.1"
SUMMARY = (
    "Crop the first 4-connected glyph whose floor bbox center is inside the "
    "bbox of all 7 marks. Connected ordinary glyphs and compound teaching "
    "boards distinguish containment, overlap, rounding, scan order, color "
    "grouping, connectivity, object masking and fixed-ring shortcuts."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
INVARIANTS = [
    "background is 5; the nonempty bbox of all 7s defines the guide",
    "at least one non-5/7 component has an inclusive floor center inside",
    "the actual selected component has a non-solid raw crop",
    "ordinary glyphs are connected; teaching boards include repeated colors and foreign crop cells",
    "advertised axes are observed from pixels; incompatible full-frame crossings raise",
]
DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ("plain", "multi_inside", "center_out", "sticks_out", "teaching")
_STYLES = ("corners", "dashed", "full", "two_corners")
AXES = {
    "grid_h": {"type": "int", "default": "canonical/broad mixture 12..24 in every band", "valid": "12..24"},
    "grid_w": {"type": "int", "default": "canonical/broad mixture 12..24 in every band", "valid": "12..24"},
    "frame_style": {"type": "str", "default": "compatible corners/dashed/full/two_corners", "valid": "corners|dashed|full|two_corners"},
    "texture": {"type": "str", "default": "teaching,teaching,ordinary repeating schedule", "valid": "plain|multi_inside|center_out|sticks_out|teaching"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"frame_style": "full", "texture": "sticks_out"},
    {"frame_style": "full", "texture": "center_out"},
    {"frame_style": "full", "texture": "teaching"},
]
GLYPH_KINDS = ("hollow_ring", "solid_3x3", "plus", "L_shape", "blob")
_GLYPHS = {
    "hollow_ring": list(RING_3X3),
    "solid_3x3": [(r, c) for r in range(3) for c in range(3)],
    "plus": [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],
    "L_shape": [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
}
_COLORS = (0, 1, 2, 3, 4, 6, 8, 9)
SCHEDULE_PROFILES = ("teaching", "ordinary")


def schedule_profile(seed, sample_index, difficulty=None):
    """Default curriculum; explicit texture/style requests may replace it."""
    return "ordinary" if sample_index % 3 == 2 else "teaching"


def _blob(rng, max_dim=4):
    """Random connected polyomino. Bbox capped at max_dim (allowing
    non-square boxes via independent row/col extents) so the cropped
    output covers more sizes/shapes than the fixed glyph set."""
    target = rng.randint(4, 9)
    max_h = rng.randint(2, max_dim)
    max_w = rng.randint(2, max_dim)
    cells = [(0, 0)]
    seen = {(0, 0)}
    for _ in range(300):
        if len(cells) >= target:
            break
        r, c = cells[rng.randrange(len(cells))]
        dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
        p = (r + dr, c + dc)
        if p in seen:
            continue
        rs = [q[0] for q in seen] + [p[0]]
        cs = [q[1] for q in seen] + [p[1]]
        if max(rs) - min(rs) + 1 > max_h or max(cs) - min(cs) + 1 > max_w:
            continue
        cells.append(p)
        seen.add(p)
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _glyph_cells(kind, rng):
    return _blob(rng) if kind == "blob" else _GLYPHS[kind]


def _selected_glyph(rng):
    """The SELECTED glyph's raw crop IS the output, so it must NOT fill its bbox
    (a solid crop -> degenerate solid output). Excludes solid_3x3 and rejects any
    bbox-filling blob; falls back to the hollow ring."""
    nonsolid = ("hollow_ring", "plus", "L_shape")
    for _ in range(40):
        kind = "blob" if rng.random() < 0.6 else rng.choice(nonsolid)
        cells = _glyph_cells(kind, rng)
        rs = [r for r, _ in cells]; cs = [c for _, c in cells]
        bb_area = (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1)
        if bb_area > len(cells):  # has >=1 interior bg hole
            return cells
    return list(RING_3X3)


def _components(g, connectivity=4, group_color=False):
    seen=set(); out=[]; h=len(g); w=len(g[0])
    for r in range(h):
        for c in range(w):
            color=g[r][c]
            if color in (5,7) or (r,c) in seen: continue
            stack=[(r,c)]; seen.add((r,c)); cells=[]
            if group_color:
                cells=[(a,b) for a in range(h) for b in range(w) if g[a][b]==color]
                seen.update(cells)
            else:
                while stack:
                    a,b=stack.pop(); cells.append((a,b))
                    ds=[(-1,0),(1,0),(0,-1),(0,1)]
                    if connectivity==8: ds += [(-1,-1),(-1,1),(1,-1),(1,1)]
                    for da,db in ds:
                        p=(a+da,b+db)
                        if 0<=p[0]<h and 0<=p[1]<w and p not in seen and g[p[0]][p[1]]==color:
                            seen.add(p); stack.append(p)
            rs=[p[0] for p in cells]; cs=[p[1] for p in cells]
            out.append({'color':color,'cells':cells,'bbox':(min(rs),min(cs),max(rs),max(cs))})
    return out

def _predict(g, rival='authority_mirror'):
    sevens=[(r,c) for r,row in enumerate(g) for c,v in enumerate(row) if v==7]
    if not sevens: return None if rival == 'authority_mirror' else [[5]]
    gr0=min(r for r,c in sevens); gr1=max(r for r,c in sevens)
    gc0=min(c for r,c in sevens); gc1=max(c for r,c in sevens)
    objs=_components(g, 8 if rival=='eight_connected' else 4, rival=='one_object_per_color')
    selected=[]
    for o in objs:
        r0,c0,r1,c1=o['bbox']; cr=(r0+r1)//2; cc=(c0+c1)//2
        keep=gr0<=cr<=gr1 and gc0<=cc<=gc1
        if rival=='fully_contained': keep=gr0<=r0<=r1<=gr1 and gc0<=c0<=c1<=gc1
        elif rival=='any_overlap': keep=any(gr0<=r<=gr1 and gc0<=c<=gc1 for r,c in o['cells'])
        elif rival=='real_center': keep=gr0<=(r0+r1)/2<=gr1 and gc0<=(c0+c1)/2<=gc1
        elif rival=='ceil_center': keep=gr0<=(r0+r1+1)//2<=gr1 and gc0<=(c0+c1+1)//2<=gc1
        elif rival=='strict_center': keep=gr0<cr<gr1 and gc0<cc<gc1
        if keep: selected.append(o)
    if rival == 'smallest_nonscalar':
        selected = [o for o in selected if len(o['cells']) > 1]
    elif rival == 'smallest_nonsolid':
        selected = [o for o in selected if len({g[r][c]
                    for r in range(o['bbox'][0],o['bbox'][2]+1)
                    for c in range(o['bbox'][1],o['bbox'][3]+1)}) > 1]
    # Rivals are total grid predictors. A wrong rule with no selected object
    # predicts a background scalar; the authority mirror still reports None.
    if not selected: return None if rival == 'authority_mirror' else [[5]]
    o=selected[0]
    if rival=='last_eligible': o=selected[-1]
    elif rival=='largest_eligible': o=max(selected,key=lambda o:len(o['cells']))
    elif rival in ('smallest_eligible','smallest_nonscalar','smallest_nonsolid'):
        o=min(selected,key=lambda o:len(o['cells']))
    elif rival=='widest_eligible_bbox':
        o=max(selected,key=lambda o:o['bbox'][3]-o['bbox'][1]+1)
    elif rival=='widest_aspect_eligible':
        o=max(selected,key=lambda o:(o['bbox'][3]-o['bbox'][1]+1)/(o['bbox'][2]-o['bbox'][0]+1))
    elif rival=='sparsest_eligible_bbox':
        o=min(selected,key=lambda o:len(o['cells'])/((o['bbox'][3]-o['bbox'][1]+1)*(o['bbox'][2]-o['bbox'][0]+1)))
    elif rival=='nearest_guide_center':
        o=min(objs,key=lambda o:((o['bbox'][0]+o['bbox'][2]-gr0-gr1)**2+(o['bbox'][1]+o['bbox'][3]-gc0-gc1)**2))
    r0,c0,r1,c1=o['bbox']
    if rival=='object_mask':
        s=set(o['cells']); return [[g[r][c] if (r,c) in s else 5 for c in range(c0,c1+1)] for r in range(r0,r1+1)]
    if rival=='always_hollow_ring':
        return [[o['color'] if (r,c)!=(1,1) else 5 for c in range(3)] for r in range(3)]
    return [row[c0:c1+1] for row in g[r0:r1+1]]

RIVALS = ('fully_contained','any_overlap','real_center','ceil_center','strict_center',
          'eight_connected','one_object_per_color','object_mask','last_eligible',
          'largest_eligible','smallest_eligible','nearest_guide_center','always_hollow_ring',
          'widest_eligible_bbox','widest_aspect_eligible','sparsest_eligible_bbox',
          'smallest_nonscalar','smallest_nonsolid')


def _mirror(grid):
    """Authoring mirror, independently checked against the Racket authority."""
    return _predict(grid)


def _geometry(grid):
    marks = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7]
    guide = (min(r for r, _ in marks), min(c for _, c in marks),
             max(r for r, _ in marks), max(c for _, c in marks))
    glyph_components = _components(grid)
    r0, c0, r1, c1 = guide
    eligible = [obj for obj in glyph_components
                if r0 <= (obj["bbox"][0] + obj["bbox"][2]) // 2 <= r1
                and c0 <= (obj["bbox"][1] + obj["bbox"][3]) // 2 <= c1]
    return marks, guide, glyph_components, eligible


def _is_teaching(grid):
    """Recognize the compound's object relations directly from pixels.

    This is a structural witness, not a comparison with rival predictions.
    The semantic gate separately compares rival predictions with Racket outputs.
    """
    _, (gr0, gc0, gr1, gc1), glyph_components, eligible = _geometry(grid)
    if not eligible:
        return False
    selected = eligible[0]
    r0, c0, r1, c1 = selected["bbox"]
    cells = set(selected["cells"])
    color = selected["color"]
    # Even width, floor center on the right guide boundary, body protruding.
    if (c1 - c0 + 1) % 2 or (c0 + c1) // 2 != gc1 or c1 <= gc1:
        return False
    before = glyph_components[:glyph_components.index(selected)]
    early_overlap = any(any(gr0 <= r <= gr1 and gc0 <= c <= gc1
                            for r, c in obj["cells"]) for obj in before)
    repeated = [obj for obj in glyph_components if obj is not selected and obj["color"] == color]
    diagonal = any((r + dr, c + dc) in cells
                   for obj in repeated for r, c in obj["cells"]
                   for dr, dc in ((-1,-1),(-1,1),(1,-1),(1,1)))
    foreign = any(grid[r][c] not in (5, color)
                  for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))
    smaller = any(len(obj["cells"]) < len(cells) for obj in eligible[1:])
    larger = any(len(obj["cells"]) > len(cells) for obj in eligible[1:])
    def distance(obj):
        a, b, c, d = obj["bbox"]
        return (a + c - gr0 - gr1) ** 2 + (b + d - gc0 - gc1) ** 2
    nearer = any(distance(obj) < distance(selected) for obj in eligible[1:])
    sw, sh = c1-c0+1, r1-r0+1
    def broad_sparse(obj):
        a,b,c,d = obj["bbox"]
        oh,ow = c-a+1,d-b+1
        return (ow > sw and ow/oh > sw/sh and len(obj["cells"])/(oh*ow) < len(cells)/(sh*sw))
    smaller_nonsolid = any(1 < len(obj["cells"]) < len(cells)
        and len({grid[r][c] for r in range(obj["bbox"][0],obj["bbox"][2]+1)
                           for c in range(obj["bbox"][1],obj["bbox"][3]+1)}) > 1
        for obj in eligible[1:])
    return bool(early_overlap and repeated and diagonal and foreign and smaller and larger and nearer
                and smaller_nonsolid and any(broad_sparse(obj) for obj in eligible[1:]))


def observe_overrides(grid):
    """Recover exact dimensions, frame style and texture from returned pixels."""
    marks, (r0, c0, r1, c1), glyph_components, eligible = _geometry(grid)
    marks = set(marks)
    corners = {(r0,c0),(r0,c1),(r1,c0),(r1,c1)}
    perimeter = {(r,c) for r in range(r0,r1+1) for c in range(c0,c1+1)
                 if r in (r0,r1) or c in (c0,c1)}
    if marks == perimeter:
        style = "full"
    elif marks == corners:
        style = "corners"
    elif len(marks) == 2:
        style = "two_corners"
    elif corners < marks < perimeter:
        style = "dashed"
    else:
        style = "irregular"  # Canonical partial guides need not match an authoring style.
    selected = eligible[0]
    protrudes = any(not (r0 <= r <= r1 and c0 <= c <= c1) for r,c in selected["cells"])
    outside_overlap = any(obj not in eligible and any(r0 <= r <= r1 and c0 <= c <= c1
                                                     for r,c in obj["cells"]) for obj in glyph_components)
    if _is_teaching(grid):
        texture = "teaching"
    elif protrudes:
        texture = "sticks_out"
    elif outside_overlap:
        texture = "center_out"
    elif len(eligible) >= 2:
        texture = "multi_inside"
    else:
        texture = "plain"
    return {"grid_h":len(grid), "grid_w":len(grid[0]), "frame_style":style, "texture":texture}


def self_check(grid, *, difficulty=None, meta=None):
    if not isinstance(grid, (list, tuple)) or not grid or not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or len(row) != len(grid[0]) for row in grid):
        return ["ragged grid"]
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be integer ARC colors 0..9"]
    out = _mirror(grid)
    if out is None:
        return ["no glyph centered in the nonempty 7-guide bbox"]
    if len({value for row in out for value in row}) < 2:
        return ["the selected component's raw crop must be nonsolid in this sampler"]
    return []


def strict_canonical_like(grid):
    """Task-lawful nonsolid crop domain, including every canonical input."""
    return self_check(grid)


def _draw_marks(g, fr, fc, fh, fw, style, rng):
    r2, c2 = fr + fh - 1, fc + fw - 1
    corners = {(fr,fc),(fr,c2),(r2,fc),(r2,c2)}
    perimeter = {(r,c) for r in range(fr,r2+1) for c in range(fc,c2+1)
                 if r in (fr,r2) or c in (fc,c2)}
    if any(g[r][c] != 5 for r,c in corners):
        raise ValueError("glyph collides with a guide corner")
    if style == "two_corners":
        cells = rng.choice([[(fr,fc),(r2,c2)],[(fr,c2),(r2,fc)]])
    elif style == "corners":
        cells = corners
    elif style == "full":
        if any(g[r][c] != 5 for r,c in perimeter):
            raise ValueError("full frame cannot overwrite glyph cells")
        cells = perimeter
    elif style == "dashed":
        available = sorted(p for p in perimeter-corners if g[p[0]][p[1]] == 5)
        # At least one noncorner mark, with genuine gaps and an unchanged bbox.
        count = rng.randint(1, max(1, len(available)//2))
        cells = corners | set(rng.sample(available, count))
    else:
        raise ValueError(f"unknown frame style {style!r}")
    for r,c in cells:
        g[r][c] = 7


def _teaching_grid(h, w, style, rng, palette_size):
    """Translate and recolor a compound witness; never rotate scan-order evidence."""
    g = full_grid(h, w, 5)
    dr, dc = rng.randint(0, h-12), rng.randint(0, w-12)
    colors = rng.sample(_COLORS, 5 if palette_size == 7 else 4)
    selected_color, later_color, overlap_color, foreign_color = colors[:4]
    variants = (
        [(r,c) for r in range(3) for c in range(4) if r in (0,2) or c in (0,3)],
        [(r,c) for r in range(3) for c in range(4) if r == 0 or c == 0],
        [(r,c) for r in range(3) for c in range(4) if r in (0,2) or c == 0],
    )
    selected = rng.choice(variants)
    def put(cells, r0, c0, color):
        for r,c in cells:
            rr, cc = r+r0+dr, c+c0+dc
            if g[rr][cc] != 5:
                raise RuntimeError("compound glyph collision")
            g[rr][cc] = color
    put(selected, 0, 0, selected_color)  # Same shape and color outside the guide.
    put(list(RING_3X3), 1, 4, overlap_color)
    put([(0,0)], 3, 11, selected_color)  # Diagonal, not cardinal, connection.
    put(selected, 4, 7, selected_color)
    put([(0,0)], 5, 8, foreign_color)  # Raw crop must preserve this pixel.
    # A broad sparse connected distractor defeats width/aspect/density rules.
    later = [(r,c) for r in range(4) for c in range(9) if r == 0 or c == 0]
    put(later, 7, 0, later_color)
    # A smaller nonsolid component also defeats scalar-filtered size rules.
    put([(0,0),(0,1),(1,0)], 8, 3, foreign_color)
    if palette_size == 7:
        put([(0,0)], 11, 0, colors[4])
    _draw_marks(g, dr+3, dc+1, 8, 8, style, rng)
    if self_check(g) or not _is_teaching(g):
        raise RuntimeError("compound witness construction violated its geometry")
    return g


def _ordinary_grid(h, w, texture, style, rng):
    for _attempt in range(80):
        g = full_grid(h, w, 5)
        lo_f = 9 if texture == "multi_inside" else 7
        fh = rng.randint(min(lo_f, h - 4), min(11, h - 4))
        fw = rng.randint(min(lo_f, w - 4), min(11, w - 4))
        fr = rng.randint(1, h - fh - 1)
        fc = rng.randint(1, w - fw - 1)
        _draw_marks(g, fr, fc, fh, fw, style, rng)
        colors = rng.sample(_COLORS, min(5, len(_COLORS)))
        ci = 0

        def free(cells):
            return all(0 <= r < h and 0 <= c < w and g[r][c] == 5
                       and all(g[ar][ac] in (5, 7)
                               for ar, ac in ((r-1, c), (r+1, c),
                                              (r, c-1), (r, c+1))
                               if 0 <= ar < h and 0 <= ac < w)
                       for r, c in cells)

        def place_inside(strict=True):
            nonlocal ci
            # the SELECTED glyph's crop is the output; require a non-bbox-filling
            # shape (blob-biased) so the cropped output is never a solid block.
            cells = _selected_glyph(rng)
            sh = max(r for r, _ in cells) + 1
            sw = max(c for _, c in cells) + 1
            for _t in range(150):
                if strict:
                    r0 = rng.randint(fr + 1, fr + fh - 1 - sh)
                    c0 = rng.randint(fc + 1, fc + fw - 1 - sw)
                else:
                    # center in, body sticking out some side
                    r0 = rng.randint(max(0, fr - 1),
                                     min(h - sh, fr + fh - sh + 1))
                    c0 = rng.randint(max(0, fc - 1),
                                     min(w - sw, fc + fw - sw + 1))
                abs_cells = [(r0 + r, c0 + c) for r, c in cells]
                ctr = ((min(r for r, _ in abs_cells) +
                        max(r for r, _ in abs_cells)) // 2,
                       (min(c for _, c in abs_cells) +
                        max(c for _, c in abs_cells)) // 2)
                if not (fr <= ctr[0] <= fr + fh - 1 and
                        fc <= ctr[1] <= fc + fw - 1):
                    continue
                if strict and not all(fr < r < fr + fh - 1 and
                                      fc < c < fc + fw - 1
                                      for r, c in abs_cells):
                    continue
                if not strict and all(fr <= r <= fr + fh - 1 and
                                      fc <= c <= fc + fw - 1
                                      for r, c in abs_cells):
                    continue
                if free(abs_cells):
                    for r, c in abs_cells:
                        g[r][c] = colors[ci % len(colors)]
                    ci += 1
                    return True
            return False

        def place_outside(touch_edge=False):
            nonlocal ci
            kind = rng.choice(GLYPH_KINDS)
            cells = _glyph_cells(kind, rng)
            sh = max(r for r, _ in cells) + 1
            sw = max(c for _, c in cells) + 1
            for _t in range(200):
                r0 = rng.randint(0, h - sh)
                c0 = rng.randint(0, w - sw)
                abs_cells = [(r0 + r, c0 + c) for r, c in cells]
                ctr = ((min(r for r, _ in abs_cells) +
                        max(r for r, _ in abs_cells)) // 2,
                       (min(c for _, c in abs_cells) +
                        max(c for _, c in abs_cells)) // 2)
                inside_ctr = (fr <= ctr[0] <= fr + fh - 1 and
                              fc <= ctr[1] <= fc + fw - 1)
                if inside_ctr:
                    continue
                overlaps = any(fr <= r <= fr + fh - 1 and
                               fc <= c <= fc + fw - 1
                               for r, c in abs_cells)
                if touch_edge != overlaps:
                    continue
                if free(abs_cells):
                    for r, c in abs_cells:
                        g[r][c] = colors[ci % len(colors)]
                    ci += 1
                    return True
            return False

        ok = True
        if texture == "sticks_out":
            ok = place_inside(strict=False)
        else:
            ok = place_inside(strict=True)
        if ok and texture == "multi_inside":
            ok = place_inside(strict=True)
        if ok and texture == "center_out":
            ok = place_outside(touch_edge=True)
        n_out = rng.randint(1, 3)
        for _ in range(n_out):
            place_outside(touch_edge=False)
        if not ok or self_check(g):
            continue
        observed = observe_overrides(g)
        if observed["texture"] != texture or observed["frame_style"] != style:
            continue
        return g
    raise ValueError("could not realize guide-crop board")


def _axis(ctx, overrides, name, valid, default):
    # Explicit controls keep their complete valid domain in every difficulty.
    return ctx.draw_choice(name, valid if overrides.get(name) is not None else (default,))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides)-set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    for name, value in overrides.items():
        if value is None:
            continue
        if name in ("grid_h", "grid_w"):
            if type(value) is not int or not 12 <= value <= 24:
                raise ValueError(f"{name} must be an integer in 12..24")
        elif name == "texture" and value not in HELPFUL_TEXTURES:
            raise ValueError(f"unknown texture {value!r}")
        elif name == "frame_style" and value not in _STYLES:
            raise ValueError(f"unknown frame style {value!r}")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    anchors = ((13,14), (17,16), (17,18))
    canonical = ctx.draw_choice("size_profile", (True, True, False))
    if canonical:
        favored = (anchors[0],)*3 if difficulty == "easy" else (anchors[1],anchors[2]) if difficulty == "hard" else ()
        dh, dw = ctx.draw_choice("canonical_size", anchors+favored)
    else:
        dh, dw = ctx.draw_rng("broad_size").randint(12,24), ctx.draw_rng("broad_width").randint(12,24)
    h = _axis(ctx, overrides, "grid_h", tuple(range(12,25)), dh)
    w = _axis(ctx, overrides, "grid_w", tuple(range(12,25)), dw)
    default_texture = schedule_profile(seed, sample_index, difficulty)
    if overrides.get("frame_style") == "full":
        default_texture = rng.choice(("plain", "multi_inside"))
    elif default_texture == "ordinary":
        default_texture = rng.choice(HELPFUL_TEXTURES[:-1])
    texture = _axis(ctx, overrides, "texture", HELPFUL_TEXTURES, default_texture)
    compatible_styles = tuple(style for style in _STYLES if not (style == "full" and texture in ("sticks_out", "center_out", "teaching")))
    if overrides.get("frame_style") == "full" and texture in ("sticks_out", "center_out", "teaching"):
        raise ValueError(f"frame_style=full is incompatible with texture={texture}: an intact boundary cannot be crossed")
    style = _axis(ctx, overrides, "frame_style", _STYLES, rng.choice(compatible_styles))
    if texture == "teaching":
        palette_size = 7 if (h,w) in ((17,16),(17,18)) else 6
        return _teaching_grid(h, w, style, rng, palette_size)
    return _ordinary_grid(h, w, texture, style, rng)


SEMANTIC_RIVALS = {name: partial(_predict, rival=name) for name in RIVALS}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {"compound_selection": _is_teaching}
WITNESS_RIVALS = {"compound_selection": list(RIVALS)}


def lesson_identifiable(demos, query):
    """Finite declared-rival check; it is not a universal induction claim."""
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if any(not isinstance(pair, dict) or "input" not in pair or "output" not in pair for pair in demos):
        return ["demonstrations must contain input and output"]
    reasons = []
    for index, pair in enumerate(demos):
        if _mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} differs from the authoring mirror")
    query_grid = query["input"] if isinstance(query, dict) else query
    query_output = query.get("output", _mirror(query_grid)) if isinstance(query, dict) else _mirror(query_grid)
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos) and rival(query_grid) != query_output:
            reasons.append(f"{name} fits all demonstrations but differs on the query")
    return reasons
