"""Generator for arc_puzzle_bank_21_set24_s:S24_M7 — order colors by onion-depth.

Rule: for each connected component, compute its max onion depth. Sort
components by (depth ascending, color ascending). Output is a 1xN
grid of colors in sorted order.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid, draw_rect

GENERATOR_ID = "ff4dfc92ad29"
VERSION = "2.2.0"  # fix: exclude 9 from components (rule treats 9 as bg); rectangles per depth + optional 9-decoy
TASK_ID = "ff4dfc92ad29"

SUMMARY = (
    "Large 0-bg grid with N (3-4) connected components of varied "
    "thicknesses. Each component is a solid RECTANGLE (shorter side "
    "2d-1 or 2d -> distinct onion depths d=1..N) in its own color "
    "from {1..8}; an optional color-9 square is a decoy the rule "
    "ignores. Rule: for each component, compute max onion depth (how "
    "many concentric layers peel away). Sort components by (depth "
    "ascending, color ascending). Output is 1×N grid of the colors "
    "in sorted order."
)

EXAMPLES_NEEDED = 3

INVARIANTS = [
    "0-bg grid",
    "N (3-4) components in distinct non-bg colors",
    "components have DISTINCT max onion depths (so primary sort key is unambiguous)",
    "components are well-separated (no 4-conn merging)",
]

# Free axes the runner may override. Keys match the keyed draw_int labels in
# generate() (n_comps is off the layout rng, not keyed). Defaults are the medium
# band, valid spans easy..hard. (Width is large to fit the 1×N output ordering
# and the up-to-7×7 onion squares.)
AXES = {
    "grid_h": {"type": "int", "default": "rng 11..13", "valid": "9..15",
               "doc": "Grid height (easy 9..11, medium 11..13, hard 12..15)."},
    "grid_w": {"type": "int", "default": "rng 17..24", "valid": "14..28",
               "doc": "Grid width (easy 14..18, medium 17..24, hard 20..28)."},
}


def _try_place(g, rng, cells, color):
    h, w = len(g), len(g[0])
    sh = max(r for r, _ in cells) + 1
    sw = max(c for _, c in cells) + 1
    for _ in range(80):
        r0 = rng.randint(0, h - sh); c0 = rng.randint(0, w - sw)
        ok = True
        for r in range(max(0, r0 - 1), min(h, r0 + sh + 1)):
            for c in range(max(0, c0 - 1), min(w, c0 + sw + 1)):
                if g[r][c] != 0:
                    ok = False
                    break
            if not ok:
                break
        if not ok:
            continue
        for dr, dc in cells:
            g[r0 + dr][c0 + dc] = color
        return True
    return False


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    if difficulty == "easy":
        h = ctx.draw_int("grid_h", 9, 11)
        w = ctx.draw_int("grid_w", 14, 18)
        n_comps = 3
    elif difficulty == "hard":
        h = ctx.draw_int("grid_h", 12, 15)
        w = ctx.draw_int("grid_w", 20, 28)
        n_comps = 4  # depths 1..4 (sides 1,3,5,7); depth-5 needs a 9×9 that won't pack
    else:
        # Floor 11 (not 10): a 10-tall grid can't pack a 7×7 + 5×5 onion pair
        # when n_comps=4, so ~17% of layouts fail to place. 11 drops that to ~1%.
        h = ctx.draw_int("grid_h", 11, 13)
        w = ctx.draw_int("grid_w", 17, 24)
        n_comps = rng.randint(3, 4)
    # Exclude 9: the rule treats color 9 as BACKGROUND (`keep-cell?` drops 0 and 9),
    # so a color-9 component would be invisible and silently shrink the output.
    colors = rng.sample([1, 2, 3, 4, 5, 6, 7, 8], n_comps)
    # depth-d component: a FILLED RECTANGLE whose shorter side is 2d-1 or 2d
    # (onion depth = ceil(min_side/2) = d), longer side varied, random orientation.
    # Distinct depths 1..n_comps keep the primary sort key unambiguous while
    # rectangles (not only odd squares) add shape diversity.
    sizes = []
    for d in range(1, n_comps + 1):
        mn = rng.choice([2 * d - 1, 2 * d])
        ln = mn + rng.randint(0, 2)
        sizes.append((mn, ln) if rng.randint(0, 1) else (ln, mn))
    rng.shuffle(sizes)
    # Grow the grid (output is tiny 1xN, so input size is free) so a row-pack of
    # all rectangles is always feasible -> placement can never fail.
    row_w = sum(sw for _, sw in sizes) + n_comps + 1
    col_h = max(sh for sh, _ in sizes) + 2
    h = min(30, max(h, col_h))
    w = min(30, max(w, row_w))
    # Outer retry: every component MUST land, else the 1×N output has fewer rows
    # than n_comps and silently breaks the distinct-depths invariant. _try_place
    # can fail when a large square gets boxed out, so resample the whole layout.
    # On the tightest feasible combo (medium h=11/w=17, n_comps=4: a 7×7+5×5+3×3+
    # 1×1 pack that only fits side-by-side) the random placement order occasionally
    # draws the 7×7 last after the small squares fragmented the space, so a seed
    # can need up to ~1600 independent attempts (measured: 0 fail at 5000, max
    # ~1617). The old cap of 200 left ~4/300 medium seeds raising. Raised to 4000:
    # every seed that already succeeded within 200 returns at the exact same outer
    # attempt with the same draws (byte-identical); only the previously-raising
    # deep-retry seeds now get the attempts they need. Retry-exhaustion class.
    def add_decoy(grid):
        # Optional color-9 DECOY square: the rule treats 9 as background and
        # ignores it, so it never becomes a component -> exercises that the 9
        # exclusion is learned, without changing the output ordering.
        if rng.randint(0, 1) == 0:
            ds = rng.choice([2, 3, 4])
            _try_place(grid, rng, [(r, c) for r in range(ds) for c in range(ds)], 9)

    # Try scattered placement first (adds input position variety) ...
    for _outer in range(800):
        g = full_grid(h, w, 0)
        if all(_try_place(g, rng, [(r, c) for r in range(sh) for c in range(sw)], color)
               for color, (sh, sw) in zip(colors, sizes)):
            add_decoy(g)
            return g
    # ... else deterministic row-pack (guaranteed to fit by the grid sizing above).
    g = full_grid(h, w, 0)
    left = 1
    for color, (sh, sw) in zip(colors, sizes):
        for dr in range(sh):
            for dc in range(sw):
                g[1 + dr][left + dc] = color
        left += sw + 1
    add_decoy(g)
    return g


def _nondecoy_components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] in (0, 9) or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                x, y = stack.pop()
                cells.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < h and 0 <= ny < w and (nx, ny) not in seen
                            and grid[nx][ny] == color):
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            out.append((color, set(cells)))
    return out


def _onion_depth(cells):
    cells = set(cells)
    depth = 0
    while cells:
        boundary = {
            (r, c) for r, c in cells
            if any((r + dr, c + dc) not in cells
                   for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        }
        if not boundary:
            break
        cells -= boundary
        depth += 1
    return depth


def self_check(grid, *, difficulty=None, meta=None):
    if not grid or not grid[0]:
        return ["empty grid"]
    msgs = []
    comps = _nondecoy_components(grid)
    if not (3 <= len(comps) <= 4):
        msgs.append(f"expected 3-4 non-decoy components, found {len(comps)}")
    if len({color for color, _ in comps}) != len(comps):
        msgs.append("component colors are not distinct")
    depths = [_onion_depth(cells) for _, cells in comps]
    if len(set(depths)) != len(depths):
        msgs.append("component onion depths are not distinct")
    for _, cells in comps:
        rs = [r for r, _ in cells]
        cs = [c for _, c in cells]
        if (max(rs) - min(rs) + 1) * (max(cs) - min(cs) + 1) != len(cells):
            msgs.append("component is not a solid rectangle")
            break
    return sorted(set(msgs))
