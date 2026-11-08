"""Generator for 358ba94e.

Rule: take the first non-zero color; for each component of that color,
count the ZERO cells inside its bbox (any zeros, not just enclosed).
Crop the component whose zero-count is UNIQUE among all components.

Combinatorial axes: grid_h/w, color, n_objects, texture
(plain|shape_mix|lone_object).
Degenerates: lone_object (a single object's count is trivially unique
-> it gets cropped), full_grid (one solid object, crop = grid,
identity). all_same was DROPPED: when no count is unique the rule hits
(first #f) and CRASHES.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "07ae7be573fc"
VERSION = "3.0.2"  # self_check now verifies exactly one unique bbox zero-count
TASK_ID = "07ae7be573fc"
SUMMARY = (
    "Same-color objects; exactly one has a UNIQUE bbox zero-count and "
    "is cropped. Shapes mix solids (0), L/S/T pieces (1-2), and rings "
    "of several sizes (1-6), so the unique object - and the output "
    "dims - vary; the duplicate-count pair can be two DIFFERENT shapes "
    "with equal counts. (Was: always two 2x2 solids + one 3x3 ring - "
    "output was always a 3x3 ring crop; all_same crashed the rule.)"
)

# Rivals: 'crop the ring' refuted by boards where the unique object is
# a solid among rings, or an L among solids. 'unique SHAPE wins'
# refuted by duplicate pairs of different shapes sharing a count.
# 'count enclosed holes only' refuted by L-shapes (open zeros count).
# 4 demos with varied unique kinds.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "all non-zero cells share one color",
    "EXACTLY one component's zero-count is unique; every other count appears >=2 times (mirror-verified)",
    "components are halo-separated",
]

DEGENERATE_TEXTURES = ("lone_object", "full_grid")
HELPFUL_TEXTURES = ("plain", "shape_mix")

AXES = {
    "grid_h":    {"type": "int", "default": "rng 10..15", "valid": "9..18"},
    "grid_w":    {"type": "int", "default": "rng 12..16", "valid": "10..20"},
    "color":     {"type": "color", "default": "rng !0", "valid": "1..9"},
    "n_objects": {"type": "int", "default": "rng 3..5", "valid": "3..6"},
    "texture":   {"type": "str", "default": "rng helpful",
                  "valid": "plain|shape_mix|lone_object|full_grid",
                  "doc": "shape_mix: the duplicate-count pair uses two "
                         "DIFFERENT shapes with the same zero-count."},
}

# A small fixed bank stays as a deterministic fallback, but the main
# path now draws RANDOM connected shapes with a chosen bbox zero-count
# so the unique cropped output varies in geometry (not 9 frozen shapes).
_SOLID2 = [(r, c) for r in range(2) for c in range(2)]          # 0
_RING33 = [(r, c) for r in range(3) for c in range(3)
           if not (r == 1 and c == 1)]                          # 1
_BANK = [(_SOLID2, 0), (_RING33, 1)]


def _zero_count(shape):
    h = max(r for r, _ in shape) + 1
    w = max(c for _, c in shape) + 1
    return h * w - len(shape)


def _connected(cells):
    s = set(cells)
    if not s:
        return False
    seen = {next(iter(s))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            p = (r + dr, c + dc)
            if p in s and p not in seen:
                seen.add(p)
                stack.append(p)
    return len(seen) == len(s)


def _norm(cells):
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _random_shape_with_zerocount(rng, want_zc, tries=200):
    """A random connected polyomino whose bbox zero-count == want_zc.

    Build a random bbox (incl. non-square), fill it solid, then carve
    `want_zc` interior/edge cells while keeping the remainder connected
    and the bbox dimensions intact (so the zero-count is exactly want_zc).
    """
    for _ in range(tries):
        bh = rng.randint(2, 5)
        bw = rng.randint(2, 5)
        area = bh * bw
        if want_zc >= area - 1 or want_zc < 0:
            continue
        full = [(r, c) for r in range(bh) for c in range(bw)]
        # candidate cells to remove: anything except we must keep at
        # least one cell on each bbox edge so dims stay bh x bw.
        cells = set(full)
        removable = list(full)
        rng.shuffle(removable)
        removed = 0
        for (r, c) in removable:
            if removed == want_zc:
                break
            trial = cells - {(r, c)}
            # keep bbox dims: still a cell in row 0, row bh-1, col 0, col bw-1
            rs = {rr for rr, _ in trial}
            cs = {cc for _, cc in trial}
            if 0 not in rs or bh - 1 not in rs or 0 not in cs or bw - 1 not in cs:
                continue
            if not _connected(trial):
                continue
            cells = trial
            removed += 1
        if removed == want_zc and _zero_count(_norm(cells)) == want_zc:
            return _norm(cells)
    return None


def _place(g, rng, shape, color, taken):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in shape) + 1
    sw = max(c for _, c in shape) + 1
    if sh > h or sw > w:
        return False
    for _ in range(120):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        cells = {(r0 + r, c0 + c) for r, c in shape}
        # halo over the BBOX (zeros inside a bbox must stay zeros, and
        # another object's cell inside this bbox would corrupt counts)
        box = {(r, c) for r in range(r0 - 1, r0 + sh + 1)
               for c in range(c0 - 1, c0 + sw + 1)}
        if box & taken:
            continue
        for r, c in cells:
            g[r][c] = color
        taken |= {(r, c) for r in range(r0, r0 + sh)
                  for c in range(c0, c0 + sw)}
        return True
    return False


def _mirror(g):
    h, w = len(g), len(g[0])
    mc = next((v for row in g for v in row if v != 0), None)
    if mc is None:
        return None
    seen = [[False] * w for _ in range(h)]
    infos = []
    for r0 in range(h):
        for c0 in range(w):
            if g[r0][c0] != mc or seen[r0][c0]:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < h and 0 <= cc < w and not seen[rr][cc] \
                            and g[rr][cc] == mc:
                        seen[rr][cc] = True
                        stack.append((rr, cc))
            r1 = min(r for r, _ in cells)
            r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells)
            c2 = max(c for _, c in cells)
            holes = sum(1 for r in range(r1, r2 + 1)
                        for c in range(c1, c2 + 1) if g[r][c] == 0)
            infos.append((r1, c1, r2, c2, holes))
    counts = [i[4] for i in infos]
    uniq = next((i for i in infos if counts.count(i[4]) == 1), None)
    if uniq is None:
        return None
    r1, c1, r2, c2, _ = uniq
    return [row[c1:c2 + 1] for row in g[r1:r2 + 1]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)
    if texture is None:
        texture = ctx.draw_choice("texture", ("plain", "plain", "shape_mix"))
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 10, 12)
        w = ctx.draw_int("grid_w", 12, 14)
        n = ctx.draw_int("n_objects", 3, 3)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 13, 15)
        w = ctx.draw_int("grid_w", 14, 16)
        n = ctx.draw_int("n_objects", 4, 5)
    else:
        h = ctx.draw_int("grid_h", 10, 15)
        w = ctx.draw_int("grid_w", 12, 16)
        n = ctx.draw_int("n_objects", 3, 5)
    color = int(overrides.get("color") or ctx.draw_color("color", exclude={0}))
    rng = ctx.draw_rng("layout")

    def _shape(zc):
        """Random shape with bbox zero-count zc, with a bank fallback."""
        s = _random_shape_with_zerocount(rng, zc)
        if s is not None:
            return s
        cands = [sh for sh, c in _BANK if c == zc]
        return rng.choice(cands) if cands else _SOLID2

    for _attempt in range(120):
        # pick a duplicate zero-count (shared by >=2 objects) and a
        # distinct unique zero-count (one object). Counts come from the
        # rule's domain (bbox zero-count of small shapes).
        possible = list(range(0, 7))
        dup_count = rng.choice(possible)
        uniq_count = rng.choice([c for c in possible if c != dup_count])
        if texture == "shape_mix":
            # the duplicate-count pair are two DIFFERENT random shapes
            pair = []
            for _ in range(12):
                s = _shape(dup_count)
                if all(s != p for p in pair):
                    pair.append(s)
                if len(pair) == 2:
                    break
            if len(pair) < 2:
                pair = [_shape(dup_count), _shape(dup_count)]
        else:
            s = _shape(dup_count)
            pair = [list(s), list(s)]
        shapes = [list(pair[0]), list(pair[1])]
        while len(shapes) < n - 1:
            shapes.append(_shape(dup_count))
        shapes.append(_shape(uniq_count))
        rng.shuffle(shapes)

        g = full_grid(h, w, 0)
        taken: set = set()
        if all(_place(g, rng, s, color, taken) for s in shapes):
            exp = _mirror(g)
            if exp is None:
                continue
            # the unique object must be OUR unique shape (count check)
            zc = [_zero_count(s) for s in shapes]
            if sum(1 for z in zc if zc.count(z) == 1) != 1:
                continue
            return g
    raise ValueError("could not realize unique-hole board")


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """All non-zero cells share one color and exactly one component has a
    zero-count that appears once among component bboxes."""
    if not grid or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    h, w = len(grid), len(grid[0])
    errors = []
    non_bg = {grid[r][c] for r in range(h) for c in range(w) if grid[r][c] != 0}
    if len(non_bg) != 1:
        errors.append(f"expected exactly 1 non-bg color, found {len(non_bg)}")
        return errors
    color = next(iter(non_bg)) if non_bg else None
    if color is None:
        return ["no non-background objects found"]
    seen = [[False] * w for _ in range(h)]
    counts = []
    for r0 in range(h):
        for c0 in range(w):
            if grid[r0][c0] != color or seen[r0][c0]:
                continue
            stack = [(r0, c0)]
            seen[r0][c0] = True
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and not seen[nr][nc] and grid[nr][nc] == color:
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            r1 = min(r for r, _ in cells); r2 = max(r for r, _ in cells)
            c1 = min(c for _, c in cells); c2 = max(c for _, c in cells)
            zeros = sum(1 for r in range(r1, r2 + 1) for c in range(c1, c2 + 1) if grid[r][c] == 0)
            counts.append(zeros)
    if len(counts) < 3:
        errors.append(f"expected at least 3 same-color components, found {len(counts)}")
    unique_counts = [zc for zc in counts if counts.count(zc) == 1]
    if len(unique_counts) != 1:
        errors.append(f"expected exactly one unique bbox zero-count, got counts={sorted(counts)}")
    if _mirror(grid) is None:
        errors.append("mirror rule could not identify a unique-zero-count component")
    return errors


def _draw_from_degenerate(name, ctx):
    """lone_object — one object: its count is trivially unique, the
    rule CROPS it (not identity). full_grid — a single solid object
    covering everything: crop = whole grid, identity. rng-varied.
    (all_same dropped: no unique count -> (first #f) crash.)"""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int("grid_h", 10, 13)
    w = ctx.draw_int("grid_w", 11, 14)
    color = rng.randint(1, 9)
    if name == "full_grid":
        return full_grid(h, w, color)
    g = full_grid(h, w, 0)
    shape, _ = _BANK[rng.randrange(len(_BANK))]
    taken: set = set()
    _place(g, rng, shape, color, taken)
    return g
