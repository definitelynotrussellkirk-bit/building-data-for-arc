"""Generator for bd14c3bf — recolor blue objects matching the red exemplar's topology.

Rule: a red(2) exemplar defines a topology SIGNATURE = (concavities, holes), where
concavities are background regions of its bbox that touch the bbox border and holes
are enclosed background regions. Every blue(1) object whose signature equals the
exemplar's is recolored red; non-matching blue objects stay blue.

PRIOR VERSION DEGENERACY: it placed the red exemplar and ALL blue objects as the
SAME shape, so every blue matched and was recolored — the discriminative "match the
signature" behavior was never exercised (no blue ever stayed blue), unlike the
canonical examples. This version places BOTH matching blues (recolored) AND
non-matching blues (stay blue), classified by a verified Python mirror of the rule's
signature function.

Rule-safe diversity: grid size, the exemplar's signature, the number and shapes of
matching vs non-matching blues, and shape size/orientation (signature is invariant
under rotation/reflection/upscale, so those vary freely).
Rule-LOCKED: red=2 (exemplar + matches), blue=1; background 0; no other colors.
Degenerates: no_red, all_red, full_grid.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, paint_at

GENERATOR_ID = "f7ad176a9a24"
VERSION = "3.1.0"  # 3.1.0: add executable red-exemplar/match-vs-nonmatch self-check.
TASK_ID = "f7ad176a9a24"
SUMMARY = (
    "0-bg grid (size varies) with ONE red(2) exemplar object and several blue(1) "
    "objects. The exemplar has a topology signature (concavities, holes). SOME blue "
    "objects share that signature (different shapes/sizes/orientations allowed — "
    "topology is rotation/scale invariant); OTHERS have a different signature. Rule: "
    "recolor every signature-matching blue object to red; non-matching blues stay "
    "blue. Net: blue shapes topologically equal to the exemplar unify under red. "
    "(Was: all blues were the exemplar's shape, so every blue was recolored and the "
    "match/no-match distinction was never shown.)"
)

INVARIANTS = [
    "background is 0; the only colors are 0, 1 (blue), 2 (red)",
    "exactly one red exemplar object",
    ">=1 blue object matches the exemplar signature (recolored red -> output differs)",
    ">=1 blue object does NOT match (stays blue -> rule is discriminative)",
    "objects are separated by a 1-cell margin (distinct 4-connected components)",
]

DEGENERATE_TEXTURES = ("no_red", "all_red", "full_grid")
HELPFUL_TEXTURES = ("varied",)
_CARD = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Curated base shapes spanning distinct signatures; the pool also rotates/
# reflects/upscales these and adds random polyominoes, then classifies by mirror.
_BASES = [
    [(r, c) for r in range(2) for c in range(2)],                       # solid -> (0,0)
    [(r, c) for r in range(2) for c in range(3)],                       # solid -> (0,0)
    [(0, 0), (1, 0), (1, 1)],                                           # L     -> (1,0)
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0)],                   # U-ish -> (1,0)
    [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)],           # H     -> (2,0)
    [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)],                           # plus  -> (4,0)
    [(0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)],   # donut -> (0,1)
    [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4),                            # 2-hole-> (0,2)
     (1, 0), (1, 2), (1, 4),
     (2, 0), (2, 1), (2, 2), (2, 3), (2, 4)],
]

AXES = {
    "grid_h":     {"type": "int", "default": "12-15 easy / 14-19 med / 18-26 hard", "valid": "10..28"},
    "grid_w":     {"type": "int", "default": "12-15 easy / 14-19 med / 18-26 hard", "valid": "10..28"},
    "n_match":    {"type": "int", "default": "1-2 easy / 1-3 med / 2-4 hard", "valid": "1..5"},
    "n_other":   {"type": "int", "default": "1-2 easy / 2-3 med / 2-5 hard", "valid": "1..6"},
    "signature":  {"type": "str", "default": "rng over realized (concs,holes)", "valid": "topology"},
    "n_distinct_colors": {"type": "int", "default": "3 (0/1/2)", "valid": "3..3"},
    "density":    {"type": "str", "default": "sparse", "valid": "sparse"},
    "texture":    {"type": "str", "default": "varied",
                   "valid": "|".join(HELPFUL_TEXTURES + DEGENERATE_TEXTURES)},
}


def _norm(cells):
    mr = min(r for r, c in cells); mc = min(c for r, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _sig(cells):
    cs = set(_norm(cells))
    sh = max(r for r, c in cs) + 1; sw = max(c for r, c in cs) + 1
    zeros = [(r, c) for r in range(sh) for c in range(sw) if (r, c) not in cs]
    zset = set(zeros); seen = set(); comps = []
    for z in zeros:
        if z in seen:
            continue
        st = [z]; seen.add(z); comp = []
        while st:
            r, c = st.pop(); comp.append((r, c))
            for dr, dc in _CARD:
                n = (r + dr, c + dc)
                if n in zset and n not in seen:
                    seen.add(n); st.append(n)
        comps.append(comp)
    concs = sum(1 for cp in comps
                if any(r == 0 or r == sh - 1 or c == 0 or c == sw - 1 for r, c in cp))
    return (concs, len(comps) - concs)


def _rot(cells):
    m = max(r for r, c in cells)
    return _norm([(c, m - r) for r, c in cells])


def _reflect(cells):
    return _norm([(r, -c) for r, c in cells])


def _scale(cells, k):
    out = []
    for r, c in cells:
        for dr in range(k):
            for dc in range(k):
                out.append((r * k + dr, c * k + dc))
    return _norm(out)


def _variant(rng, cells):
    for _ in range(rng.randint(0, 3)):
        cells = _rot(cells)
    if rng.random() < 0.5:
        cells = _reflect(cells)
    return _scale(cells, rng.choice([1, 1, 2]))


def _rand_poly(rng, n):
    cells = {(0, 0)}
    while len(cells) < n:
        r, c = rng.choice(tuple(cells)); dr, dc = rng.choice(_CARD)
        cells.add((r + dr, c + dc))
    return _norm(cells)


def _build_pool(rng):
    """A pool of shapes grouped by signature."""
    groups: dict = {}
    cands = []
    for base in _BASES:
        for _ in range(4):
            cands.append(_variant(rng, base))
    for _ in range(30):
        cands.append(_variant(rng, _rand_poly(rng, rng.randint(4, 9))))
    for cells in cands:
        groups.setdefault(_sig(cells), []).append(cells)
    return groups


def _place(rng, g, occ, cells, h, w, color, margin=1):
    cells = _norm(cells)
    sh = max(r for r, c in cells) + 1; sw = max(c for r, c in cells) + 1
    if sh > h or sw > w:
        return False
    for _t in range(60):
        top = rng.randint(0, h - sh); left = rng.randint(0, w - sw)
        ok = True
        for r in range(top - margin, top + sh + margin):
            for c in range(left - margin, left + sw + margin):
                if 0 <= r < h and 0 <= c < w and occ[r][c]:
                    ok = False; break
            if not ok:
                break
        if not ok:
            continue
        for (r, c) in cells:
            g[top + r][left + c] = color
            occ[top + r][left + c] = True
        # reserve a 1-cell halo so components stay separate
        for r in range(top - margin, top + sh + margin):
            for c in range(left - margin, left + sw + margin):
                if 0 <= r < h and 0 <= c < w:
                    occ[r][c] = True
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if overrides.get("texture") in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(overrides["texture"], rng)
    if difficulty == "easy":
        hr, wr, mr, orr = (12, 15), (12, 15), (1, 2), (1, 2)
    elif difficulty == "hard":
        hr, wr, mr, orr = (18, 26), (18, 26), (2, 4), (2, 5)
    else:
        hr, wr, mr, orr = (14, 19), (14, 19), (1, 3), (2, 3)

    for _attempt in range(40):
        groups = _build_pool(rng)
        sigs = [s for s, lst in groups.items() if lst]
        # need a target signature AND at least one other signature for distractors
        multi = [s for s in sigs if len(groups[s]) >= 1]
        if len(sigs) < 2 or not multi:
            continue
        target = rng.choice(multi)
        others = [s for s in sigs if s != target]
        if not others:
            continue

        h = rng.randint(*hr); w = rng.randint(*wr)
        g = full_grid(h, w, 0)
        occ = [[False] * w for _ in range(h)]

        # red exemplar
        if not _place(rng, g, occ, rng.choice(groups[target]), h, w, 2):
            continue
        n_match = rng.randint(*mr); n_other = rng.randint(*orr)
        placed_match = 0
        for _ in range(n_match):
            if _place(rng, g, occ, rng.choice(groups[target]), h, w, 1):
                placed_match += 1
        placed_other = 0
        for _ in range(n_other):
            s = rng.choice(others)
            if _place(rng, g, occ, rng.choice(groups[s]), h, w, 1):
                placed_other += 1
        # both kinds must be present: output differs AND rule discriminates
        if placed_match >= 1 and placed_other >= 1:
            return g

    # deterministic fallback: H red exemplar + matching H blue + plus blue
    g = full_grid(14, 14, 0)
    H = [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)]
    plus = [(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)]
    paint_at(g, 1, 1, H, 2); paint_at(g, 1, 8, H, 1); paint_at(g, 8, 8, plus, 1)
    return g


def _draw_from_degenerate(name, rng):
    h, w = 14, 14
    g = full_grid(h, w, 0)
    H = [(0, 0), (0, 2), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)]
    if name == "no_red":
        paint_at(g, 2, 2, H, 1)            # blue only; no exemplar to match against
        return g
    if name == "all_red":
        paint_at(g, 2, 2, H, 2); paint_at(g, 8, 8, H, 2)  # no blue to recolor
        return g
    if name == "full_grid":
        for r in range(h):
            for c in range(w):
                g[r][c] = 1
        return g
    return g


def self_check(grid, *, difficulty=None, meta=None):
    from puzzle_generators.helpers.selfcheck import components, components_have_clearance
    errs = []
    colors = {v for row in grid for v in row}
    if not colors <= {0, 1, 2}:
        errs.append("topology task should use only colors 0,1,2")
    reds = components(grid, colors={2}, same_color=True)
    blues = components(grid, colors={1}, same_color=True)
    if len(reds) != 1:
        errs.append("need exactly one red exemplar object")
        return errs
    red_sig = _sig(reds[0]["cells"])
    match = [b for b in blues if _sig(b["cells"]) == red_sig]
    other = [b for b in blues if _sig(b["cells"]) != red_sig]
    if not match:
        errs.append("need at least one blue object matching the red signature")
    if not other:
        errs.append("need at least one non-matching blue object")
    if not components_have_clearance(grid, reds + blues, diagonal=False):
        errs.append("objects should be separated by background")
    return errs
