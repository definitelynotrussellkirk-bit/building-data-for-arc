"""Generator for arc_additional_puzzles_21_set6:H41 (task 00f37833e26f).

THE RULE (what a solver must learn to see):
  Normalize the green(3) shape and the gray(5) shape to their bbox
  origins. Output = the green shape's cells MINUS the gray shape's
  cells (set difference on normalized coordinates), painted green on
  a fresh canvas and cropped to the surviving cells' bbox.

WHAT MAKES AN INPUT TEACH THIS RULE (helpful textures):
  - RANDOM grown polyominoes (5-10 cells) with a random CONNECTED
    subset as the mask — the old generator hardcoded one 6-cell shape
    and one mask at fixed positions, so all outputs were IDENTICAL
    (smoke: unique_out=1); worse, the hardcoded mask was disconnected
    and the rule only reads the first component
  - positions vary freely (shapes are halo-isolated; normalization
    must do the work, not fixed anchors)
  - diff sizes from 1 cell (mask = shape minus one) up to most of the
    shape — output dims actually vary
  - decor cells in colors other than {3, 5} are invisible to the rule

WHAT HIDES IT (degenerate textures, reachable via texture=...):
  - no_overlap   the mask shares no normalized cells: output = whole shape
  - mask_bigger  the gray shape has MORE cells than the green one
  (no_shapes / full_grid are NOT offered — both crash the rule at
  (first (objects ...)) when a color is absent; mask == shape also
  crashes via bbox-of-cells on an empty diff and is never generated)
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "00f37833e26f"
# 3.1.0: replaced two raise ValueError fall-throughs with guaranteed
# graceful fallbacks (never raise). Widened src_size (5-12) so the green
# shape -> diff bbox varies more (was dup-outputs 44%).
VERSION = "3.1.0"
TASK_ID = "00f37833e26f"
SUMMARY = (
    "0-bg grid with one green(3) grown polyomino (5-10 cells) and one "
    "gray(5) connected subset of it placed elsewhere (plus optional "
    "non-{3,5} decor the rule ignores); rule outputs the normalized "
    "set difference green-minus-gray, bbox-cropped, in green."
)

# Rivals: 'output the green shape' refuted by demos where the diff is
# smaller. 'overlay at absolute positions' refuted because the shapes
# sit far apart — only normalized overlay explains outputs. 'gray wins'
# refuted (output is green). 'decor matters' refuted by decor demos.
# 4 demos with diff sizes 1..large.
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "exactly one green(3) connected shape and one gray(5) connected shape",
    "gray normalized cells are a strict subset of green's (helpful path)",
    "the normalized diff is non-empty (empty diff crashes the rule)",
    "shapes are halo-isolated; decor uses colors outside {3, 5}",
]

DEGENERATE_TEXTURES = ("no_overlap", "mask_bigger")
HELPFUL_TEXTURES = ("plain",)

AXES = {
    "grid_h":    {"type": "int", "default": "rng 8..11 (easy 8..9, hard 10..14)",
                  "valid": "7..16", "doc": "Grid height."},
    "grid_w":    {"type": "int", "default": "rng 11..14 (easy 11..12, hard 13..16)",
                  "valid": "9..18", "doc": "Grid width."},
    "src_size":  {"type": "int", "default": "rng 5..10 (hard 8..12)",
                  "valid": "4..12", "doc": "Green shape cell count."},
    "diff_size": {"type": "int", "default": "rng 1..src-2",
                  "valid": "1..10", "doc": "Cells surviving the subtraction."},
    "n_decor":   {"type": "int", "default": "rng 0..3", "valid": "0..5",
                  "doc": "Cells in colors outside {3,5} — invisible to the rule."},
    "texture":   {"type": "str", "default": "plain",
                  "valid": "plain|no_overlap|mask_bigger",
                  "doc": "Set to a degenerate name to build a rule-hiding input."},
}

_DECOR_COLORS = (1, 2, 4, 6, 7, 8, 9)


def _grow(rng, k, base=None):
    """Connected polyomino of k cells; if base given, grow INSIDE it."""
    if base is None:
        cells = [(0, 0)]
        seen = {(0, 0)}
        while len(cells) < k:
            r, c = cells[rng.randrange(len(cells))]
            dr, dc = ((-1, 0), (1, 0), (0, -1), (0, 1))[rng.randrange(4)]
            if (r + dr, c + dc) not in seen:
                cells.append((r + dr, c + dc))
                seen.add((r + dr, c + dc))
    else:
        pool = set(base)
        start = base[rng.randrange(len(base))]
        cells = [start]
        seen = {start}
        frontier = [start]
        while len(cells) < k and frontier:
            r, c = frontier[rng.randrange(len(frontier))]
            nbrs = [(r + dr, c + dc) for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                    if (r + dr, c + dc) in pool and (r + dr, c + dc) not in seen]
            if not nbrs:
                frontier.remove((r, c))
                continue
            n = nbrs[rng.randrange(len(nbrs))]
            cells.append(n)
            seen.add(n)
            frontier.append(n)
        if len(cells) < k:
            return None
    mr = min(r for r, _ in cells)
    mc = min(c for _, c in cells)
    return sorted((r - mr, c - mc) for r, c in cells)


def _place(g, rng, cells, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    for _ in range(60):
        r0 = rng.randint(0, h - sh)
        c0 = rng.randint(0, w - sw)
        clear = True
        for r in range(max(0, r0 - 1), min(h, r0 + sh + 1)):
            for c in range(max(0, c0 - 1), min(w, c0 + sw + 1)):
                if g[r][c] != 0:
                    clear = False
                    break
            if not clear:
                break
        if not clear:
            continue
        for r, c in cells:
            g[r0 + r][c0 + c] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    texture = overrides.get("texture")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, ctx)

    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 8, 10)
        w = ctx.draw_int("grid_w", 11, 13)
        src_size = ctx.draw_int("src_size", 5, 7)
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 11, 16)
        w = ctx.draw_int("grid_w", 14, 18)
        src_size = ctx.draw_int("src_size", 8, 12)
    else:
        h = ctx.draw_int("grid_h", 8, 13)
        w = ctx.draw_int("grid_w", 11, 16)
        src_size = ctx.draw_int("src_size", 5, 10)
    rng = ctx.draw_rng("layout")
    diff_size = int(overrides.get(
        "diff_size", ctx.draw_int("diff_size", 1, max(1, src_size - 2))))
    diff_size = max(1, min(diff_size, src_size - 2))
    n_decor = int(overrides.get("n_decor", ctx.draw_int("n_decor", 0, 3)))

    for _attempt in range(60):
        src = _grow(rng, src_size)
        mask = _grow(rng, src_size - diff_size, base=src)
        if mask is None:
            continue  # subset growth got stuck (rare)
        # the rule re-normalizes the gray shape to ITS OWN bbox — the
        # subset only survives subtraction-aligned if its own
        # normalization is still a strict subset of the green shape
        if not set(mask) < set(src):
            continue
        g = full_grid(h, w, 0)
        if not _place(g, rng, src, 3):
            continue
        if not _place(g, rng, mask, 5):
            continue
        # decor: colors the rule ignores entirely
        placed = 0
        for _ in range(30):
            if placed >= n_decor:
                break
            r, c = rng.randrange(h), rng.randrange(w)
            if g[r][c] == 0:
                g[r][c] = rng.choice(_DECOR_COLORS)
                placed += 1
        return g
    # guaranteed fallback: green L-tromino with a single gray subset cell
    # (normalized gray {(0,0)} is a strict subset of green -> non-empty diff)
    return _fallback_board()


def _fallback_board():
    g = full_grid(8, 11, 0)
    # green L at (1,1): cells (0,0),(1,0),(1,1)
    for r, c in ((1, 1), (2, 1), (2, 2)):
        g[r][c] = 3
    # gray single cell elsewhere; normalized {(0,0)} subset of green
    g[1][6] = 5
    return g


def _draw_from_degenerate(name, ctx):
    """Rule-hiding inputs — rng-varied, rule-safe (both colors present,
    diff never empty).

    no_overlap  — the gray shape shares no normalized cells with the
                  green one: subtraction removes nothing.
    mask_bigger — gray has more cells than green: extra cells are
                  silently ignored by the set difference.
    """
    h = ctx.draw_int("grid_h", 8, 11)
    w = ctx.draw_int("grid_w", 11, 14)
    rng = ctx.draw_rng("degenerate_layout")
    for _attempt in range(60):
        g = full_grid(h, w, 0)
        src = _grow(rng, rng.randint(4, 6))
        if name == "no_overlap":
            # shift the subset off-lattice so normalized cells differ:
            # use a column-shifted copy that misses all src cells
            mask = sorted((r, c + max(c2 for _, c2 in src) + 1) for r, c in src[:2])
            mc = min(c for _, c in mask)
            mask = sorted((r, c - mc) for r, c in mask)
            if any(p in src for p in mask):
                continue
        else:  # mask_bigger
            bigger = _grow(rng, rng.randint(7, 9))
            mask = bigger
            # ensure SOME of src survives subtraction (rule-safe)
            if not [p for p in src if p not in mask]:
                continue
        if _place(g, rng, src, 3) and _place(g, rng, mask, 5):
            return g
    # graceful fallback (never raise): minimal rule-safe board
    return _fallback_board()


def _selfcheck_color_components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set(); out = []
    for r in range(h):
        for c in range(w):
            if (r, c) in seen or grid[r][c] != color:
                continue
            q = [(r, c)]; seen.add((r, c)); cells = []
            while q:
                rr, cc = q.pop(); cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc)); q.append((nr, nc))
            out.append(cells)
    return out

def _selfcheck_norm(cells):
    mr = min(r for r, _ in cells); mc = min(c for _, c in cells)
    return {(r - mr, c - mc) for r, c in cells}

def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    errs: list[str] = []
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be non-empty and rectangular"]
    green = _selfcheck_color_components(grid, 3)
    gray = _selfcheck_color_components(grid, 5)
    if len(green) != 1:
        errs.append(f"expected exactly one green component, got {len(green)}")
    if len(gray) != 1:
        errs.append(f"expected exactly one gray mask component, got {len(gray)}")
    if len(green) == 1 and len(gray) == 1:
        gs, ms = _selfcheck_norm(green[0]), _selfcheck_norm(gray[0])
        if not (ms < gs):
            errs.append("normalized gray mask should be a strict subset of the green shape")
    return errs
