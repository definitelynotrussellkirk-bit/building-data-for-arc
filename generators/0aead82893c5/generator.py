"""Generator for arc_puzzle_bank_21_set10_e:hard_j21 — symmetry-class
gallery pack.

Rule: every object's binary MASK is classified: LR+UD symmetric ->
both, LR-only -> vertical, UD-only -> horizontal, else neither. The
crops paste into a 2x2 collage (both TL, vertical TR, horizontal BL,
neither BR) with one blank row/col between, sized by the max dims per
band. Duplicate classes: the LAST object in scan order wins (set!
overwrite). A missing class CRASHES — every board covers all 4.
Classification is mask-based: colors are irrelevant.

Combinatorial axes: grid_h/w, shapes per class, texture
(plain|duplicate_class|same_color). NOTE: multicolor objects are
impossible here - the rule's (objects g 0) splits by color, so a
recolored cell would break the object into separate components.
Degenerates: none survivable (missing class crashes, documented).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0aead82893c5"
VERSION = "2.0.0"
TASK_ID = "0aead82893c5"
SUMMARY = (
    "One object per mask-symmetry class packs into a 2x2 gallery. "
    "Shapes are RANDOM per class with varied sizes (was: 4 fixed "
    "shapes at 4 fixed spots). duplicate_class boards add a 5th "
    "object doubling one class - the LAST in scan order wins "
    "(bridge-verified); same_color boards prove colors don't drive "
    "the classification."
)

# Rivals: 'classify by color' refuted by same_color. 'first/biggest
# duplicate wins' refuted by duplicate_class (last scan order).
# 4 demos with varied shapes/sizes.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "all 4 mask-symmetry classes present (missing class crashes)",
    "objects separated >=2 (same- and cross-color merging avoided)",
    "duplicate boards still cover all 4 classes",
]

DEGENERATE_TEXTURES = ()
HELPFUL_TEXTURES = ("plain", "duplicate_class", "same_color")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 11..15", "valid": "10..18"},
    "grid_w":  {"type": "int", "default": "rng 14..18", "valid": "12..22"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|duplicate_class|same_color",
                "doc": "duplicate_class: 5th object doubles a class, "
                       "last in scan order wins; same_color: all "
                       "objects one color."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def _grow(rng, k, max_h=4, max_w=4):
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
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _mask_cls(cells):
    s = set(cells)
    h = max(r for r, _ in cells) + 1
    w = max(c for _, c in cells) + 1
    lr = all((r, w - 1 - c) in s for r, c in cells)
    ud = all((h - 1 - r, c) in s for r, c in cells)
    if lr and ud:
        return "both"
    if lr:
        return "vertical"
    if ud:
        return "horizontal"
    return "neither"


def _shape_of(rng, want):
    for _ in range(500):
        base = _grow(rng, rng.randint(3, 6))
        s = set(base)
        h = max(r for r, _ in base) + 1
        w = max(c for _, c in base) + 1
        if want == "vertical":
            cells = sorted(s | {(r, 2 * w - 1 - c) for r, c in s})
        elif want == "horizontal":
            cells = sorted(s | {(2 * h - 1 - r, c) for r, c in s})
        elif want == "both":
            m = s | {(r, 2 * w - 1 - c) for r, c in s}
            cells = sorted(m | {(2 * h - 1 - r, c) for r, c in m})
        else:
            cells = base
        mr = min(r for r, _ in cells)
        mc = min(c for _, c in cells)
        cells = sorted((r - mr, c - mc) for r, c in cells)
        if max(r for r, _ in cells) > 5 or max(c for _, c in cells) > 5:
            continue
        if _mask_cls(cells) == want and _connected(cells):
            return cells
    raise ValueError(f"no {want} shape")


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
    seen = set()
    slots = {}
    for r in range(h):
        for c in range(w):
            v = g[r][c]
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
                    if 0 <= nr < h and 0 <= nc < w \
                            and (nr, nc) not in seen and g[nr][nc] == v:
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(rr for rr, _ in cells)
            r2 = max(rr for rr, _ in cells)
            c1 = min(cc for _, cc in cells)
            c2 = max(cc for _, cc in cells)
            crop = [row[c1:c2 + 1] for row in g[r1:r2 + 1]]
            # the rule masks the CROP: foreign cells inside the bbox
            # count toward this object's symmetry classification
            mask_cells = [(rr, cc) for rr, row in enumerate(crop)
                          for cc, v in enumerate(row) if v != 0]
            slots[_mask_cls(mask_cells)] = crop
    if len(slots) < 4:
        return None
    both, vert = slots["both"], slots["vertical"]
    horiz, neither = slots["horizontal"], slots["neither"]
    top_h = max(len(both), len(vert))
    bot_h = max(len(horiz), len(neither))
    left_w = max(len(both[0]), len(horiz[0]))
    right_w = max(len(vert[0]), len(neither[0]))
    out = [[0] * (left_w + 1 + right_w) for _ in range(top_h + 1 + bot_h)]

    def paste(crop, top, left):
        for r, row in enumerate(crop):
            for c, v in enumerate(row):
                if v != 0:
                    out[top + r][left + c] = v

    paste(both, 0, 0)
    paste(vert, 0, left_w + 1)
    paste(horiz, top_h + 1, 0)
    paste(neither, top_h + 1, left_w + 1)
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty,
                  overrides=overrides)
    texture = overrides.get("texture")
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain",
                                              "duplicate_class",
                                              "same_color"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 14, 16)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 14, 15)
        w = ctx.draw_int("grid_w", 17, 18)
    else:
        h = ctx.draw_int("grid_h", 11, 15)
        w = ctx.draw_int("grid_w", 14, 18)
    rng = ctx.draw_rng("layout")

    classes = ["both", "vertical", "horizontal", "neither"]
    if texture == "duplicate_class":
        classes.append(rng.choice(classes))
    if texture == "same_color":
        color = rng.choice(_COLORS)
        colors = [color] * len(classes)
    else:
        colors = rng.sample(_COLORS, len(classes))

    for _attempt in range(200):
        g = full_grid(h, w, 0)
        occupied = []
        ok = True
        for cls, color in zip(classes, colors):
            shape = _shape_of(rng, cls)
            sh = max(r for r, _ in shape) + 1
            sw = max(c for _, c in shape) + 1
            placed = False
            for _t in range(150):
                r0 = rng.randint(0, h - sh)
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
    raise ValueError("could not realize symmetry-gallery board")
def _symmetry_slots_from_grid(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    slots = set()
    count = 0
    for r in range(h):
        for c in range(w):
            v = grid[r][c]
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
                    if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                            and grid[nr][nc] == v):
                        seen.add((nr, nc)); stack.append((nr, nc))
            count += 1
            r1 = min(rr for rr, _ in cells); r2 = max(rr for rr, _ in cells)
            c1 = min(cc for _, cc in cells); c2 = max(cc for _, cc in cells)
            mask_cells = [(rr - r1, cc - c1) for rr, cc in cells]
            slots.add(_mask_cls(mask_cells))
    return slots, count


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errors = []
    if not grid or not grid[0]:
        return ["empty grid"]
    slots, count = _symmetry_slots_from_grid(grid)
    missing = {"both", "vertical", "horizontal", "neither"} - slots
    if missing:
        errors.append(f"missing symmetry classes: {sorted(missing)}")
    if count < 4:
        errors.append(f"expected at least four colored objects, got {count}")
    if _mirror(grid) is None:
        errors.append("canonical gallery mirror would fail to build all slots")
    return errors
