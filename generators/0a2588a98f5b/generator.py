"""Generator for arc_puzzle_bank_21_set13_s:S13_M3 — header count picks
symmetry class.

Rule: code = number of 1s in row 0 (positions irrelevant). wanted
class: code 1 -> col-symmetric ONLY, code 2 -> row-symmetric ONLY,
code 3 -> both, any other count (incl. 0) -> neither. The FIRST body
component (sorted by bbox top-left) of exactly that class is cropped
to its bbox and painted 8. A both-symmetric object does NOT match a
single-symmetry query (classes are exact). No matching object CRASHES
the rule ((first '())) — never generated.

Combinatorial axes: grid_h/w, symmetry_code, random per-class shapes,
texture (plain|multi_match|both_decoy|scattered_header|code0).
Degenerates: none survivable (missing class crashes, documented).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0a2588a98f5b"
VERSION = "3.1.1"  # diversity: wider per-class shapes (base 3-7 cells in 5x5; relaxed crop cap) to lift output uniq
TASK_ID = "0a2588a98f5b"

SUMMARY = (
    "Row-0 count of 1s picks a symmetry class (1: LR-sym only, 2: "
    "UD-sym only, 3: both, else: neither); first matching component "
    "crops to color 8. Shapes are RANDOM per class (was: 4 hardcoded "
    "shapes, unique_out=4 - a false intrinsic-low). multi_match "
    "boards carry TWO objects of the wanted class (top-left first "
    "wins); both_decoy boards add a both-symmetric object that does "
    "NOT match a single-symmetry query; scattered_header spreads the "
    "1s across row 0; code0 boards have an empty header (asym pick, "
    "bridge-verified)."
)

# Rivals: 'output the first body object' refuted by multi_match /
# placement. 'both-symmetric counts as either' refuted by both_decoy.
# 'header 1s must be left-packed' refuted by scattered_header.
# 'preserve color' refuted by every demo (output 8). 4 demos covering
# >=3 codes.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly one component of the WANTED class minimum (missing crashes)",
    "component symmetry classes are exact (both != row-only != col-only)",
    "components separated >=2 so they never merge",
]

DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ("plain", "multi_match", "both_decoy",
                    "scattered_header", "code0")

AXES = {
    "grid_h":        {"type": "int", "default": "rng 10..15", "valid": "9..18"},
    "grid_w":        {"type": "int", "default": "rng 12..18", "valid": "11..20"},
    "symmetry_code": {"type": "int", "default": "rng 1..3", "valid": "0..3"},
    "texture":       {"type": "str", "default": "rng helpful",
                      "valid": "plain|multi_match|both_decoy|"
                               "scattered_header|code0",
                      "doc": "multi_match: two wanted-class objects, "
                             "top-left first wins; both_decoy: a "
                             "both-symmetric object alongside a "
                             "single-symmetry query; code0: empty "
                             "header selects the asymmetric object."},
}

_COLORS = (2, 3, 4, 5, 6, 7, 9)


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Row-0 code (count of 1s) is 0-3; >=1 non-zero body cell in rows 1+."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    code = sum(1 for v in grid[0] if v == 1)
    if code > 3:
        errors.append(f"row-0 code count={code} > 3 (invalid symmetry code)")
    body_nz = any(grid[r][c] != 0 for r in range(1, h) for c in range(w))
    if not body_nz:
        errors.append("no non-zero cell in body (rows 1+); nothing to match")
    return errors


def _norm(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _cls(cells):
    n = _norm(cells)
    s = set(n)
    h = max(r for r, _ in n) + 1
    w = max(c for _, c in n) + 1
    rsym = all((h - 1 - r, c) in s for r, c in n)
    csym = all((r, w - 1 - c) in s for r, c in n)
    return 3 if (rsym and csym) else 1 if rsym else 2 if csym else 0


def _grow(rng, k, max_h, max_w):
    cells = [(0, 0)]
    seen = {(0, 0)}
    for _ in range(300):
        if len(cells) >= k:
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
    return _norm(cells)


def _shape_of_class(rng, want, max_h=5, max_w=5):
    for _ in range(400):
        base = _grow(rng, rng.randint(3, 7), max_h, max_w)
        s = set(base)
        h = max(r for r, _ in base) + 1
        w = max(c for _, c in base) + 1
        if want == 1:
            cells = _norm(list(s | {(2 * h - 1 - r, c) for r, c in s}))
        elif want == 2:
            cells = _norm(list(s | {(r, 2 * w - 1 - c) for r, c in s}))
        elif want == 3:
            m = s | {(r, 2 * w - 1 - c) for r, c in s}
            cells = _norm(list(m | {(2 * h - 1 - r, c) for r, c in m}))
        else:
            cells = base
        ch = max(r for r, _ in cells) + 1
        cw = max(c for _, c in cells) + 1
        if ch > 2 * max_h or cw > 2 * max_w:
            continue
        if _cls(cells) == want and _connected(cells):
            return cells
    raise ValueError(f"could not grow class-{want} shape")


def _connected(cells):
    s = set(cells)
    stack = [cells[0]]
    seen = {cells[0]}
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p = (r + dr, c + dc)
            if p in s and p not in seen:
                seen.add(p)
                stack.append(p)
    return len(seen) == len(s)


def _mirror(g):
    h, w = len(g), len(g[0])
    code = sum(1 for v in g[0] if v == 1)
    want = {1: 2, 2: 1, 3: 3}.get(code, 0)
    # rule classes: 1=row-sym(UD), 2=col-sym(LR); my _cls matches
    body = [row[:] for row in g[1:]]
    bh = len(body)
    seen = set()
    comps = []
    for r in range(bh):
        for c in range(w):
            v = body[r][c]
            if v == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < bh and 0 <= nc < w \
                            and (nr, nc) not in seen and body[nr][nc] == v:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    matches = [cs for cs in comps if _cls(cs) == want]
    if not matches:
        return None
    matches.sort(key=lambda cs: (min(r for r, _ in cs),
                                 min(c for _, c in cs)))
    tgt = matches[0]
    n = _norm(tgt)
    th = max(r for r, _ in n) + 1
    tw = max(c for _, c in n) + 1
    out = [[0] * tw for _ in range(th)]
    for r, c in n:
        out[r][c] = 8
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty,
                  overrides=overrides)
    texture = overrides.get("texture")
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain",
                                              "multi_match", "both_decoy",
                                              "scattered_header", "code0"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 12, 14)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 15)
        w = ctx.draw_int("grid_w", 16, 18)
    else:
        h = ctx.draw_int("grid_h", 10, 15)
        w = ctx.draw_int("grid_w", 12, 18)
    rng = ctx.draw_rng("layout")
    if texture == "code0":
        code = 0
    elif texture == "both_decoy":
        code = ctx.draw_int("symmetry_code", 1, 2)
    else:
        code = int(overrides.get("symmetry_code") or
                   ctx.draw_int("symmetry_code", 1, 3))
    want = {1: 2, 2: 1, 3: 3}.get(code, 0)

    # build the cast: one wanted + distractors of OTHER classes
    cast = [want]
    others = [c for c in (0, 1, 2, 3) if c != want]
    rng.shuffle(others)
    cast += others[:rng.randint(2, 3)]
    if texture == "multi_match":
        cast.append(want)
    if texture == "both_decoy" and 3 not in cast:
        cast.append(3)

    # Placing 4-6 shapes with a 1-cell separation gap on a small easy grid fails
    # for ~3% of seeds (congestion). Retrying alone doesn't clear it, so GROW the
    # canvas every 120 failed attempts — the rule is size-agnostic, so a slightly
    # larger board for a congested seed is fine and guarantees room.
    for _attempt in range(600):
        if _attempt and _attempt % 120 == 0:
            h += 1; w += 1
        g = full_grid(h, w, 0)
        if code > 0:
            if texture == "scattered_header":
                for c in rng.sample(range(w), code):
                    g[0][c] = 1
            else:
                for c in range(code):
                    g[0][c] = 1
        colors = rng.sample(_COLORS, min(len(cast), len(_COLORS)))
        ok = True
        occupied = []
        for cls_id, color in zip(cast, colors):
            shape = _shape_of_class(rng, cls_id)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            if sh > h - 1 or sw > w:
                # shape doesn't fit this (possibly small) grid; fail the attempt
                # cleanly so the outer retry/grow handles it instead of crashing
                # randint(1, h-sh) on h-sh < 1.
                ok = False
                break
            placed = False
            for _t in range(150):
                r0 = rng.randint(1, h - sh)
                c0 = rng.randint(0, w - sw)
                cells = [(r0 + r, c0 + c) for r, c in shape]
                if all(all(abs(r - orr) > 1 or abs(c - occ) > 1
                           for orr, occ in occupied) for r, c in cells):
                    for r, c in cells:
                        g[r][c] = color
                    occupied += cells
                    placed = True
                    break
            if not placed:
                ok = False
                break
        if not ok:
            continue
        if _mirror(g) is None:
            continue
        return g
    raise ValueError("could not realize symmetry-class board")
