"""Generator for e937c5b85cdd (ARC task 689c358e) -- cross arms project to the frame.

Rule (canonical): the grid is an orange(7) chamber inside a magenta(6)
perimeter frame. Every interior object is a single-colored cross: a 5-cell
plus whose one extended arm is strictly longest (canonical extension is
exactly one cell, giving arms {1,1,1,2}). For each cross, the rule finds
its center (the unique 4-neighbor cell) and its strictly-longest arm, then
CLEARS the FACING border cell (the one the longest arm points to) to 0 and
PAINTS the OPPOSITE border cell with the cross's color.

Canonical demos are always 11x11 with exactly FOUR crosses colored
precisely {2,5,8,9}, every cross six cells with arm multiset [1,1,1,2],
all four arm directions witnessed across scenes, and -- critically -- no
two crosses ever project onto the same border cell: horizontal-arm crosses
(left/right) sit in distinct rows and vertical-arm crosses (up/down) in
distinct columns. The generator enforces that collision-free invariant: a
projection collision would let one cross's paint or clear overwrite
another's, which looks mislabeled to a learner (the recorded graylist root
cause: loss-HIGH unfittable-or-mislabeled). A dedicated canonical-archetype
prior (11x11, 4 crosses, official colors, arm 2) covers the official
geometry at >=25% in every band, while generalized colors, counts, grids,
and length-3 arms remain as disambiguating witnesses.

Combinatorial axes: grid_h, grid_w, cross_count, max_arm_len (exact max),
palette_kind, texture.
Branches witnessed: all four longest-arm directions, crosses hugging the
frame, arm length 2 (canonical) and 3 (extension), collision-free
multi-cross compositions, canonical archetype draws.
Degenerates: one_cross, four_directions, frame_hugger.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "e937c5b85cdd"
VERSION = "4.1.0"  # veto fix: canonical-archetype prior (11x11/4-cross/{2,5,8,9}/arm-2 >=25% all bands), max_arm_len exact-max + observed, cross-shape contract in self_check
TASK_ID = "e937c5b85cdd"
RULE_HASH = "538497122a9d"
SUMMARY = (
    "Orange(7) chamber inside a magenta(6) perimeter frame (11x11-heavy "
    "prior, 11..16 overall). Interior: 1..5 crosses (4 in the canonical "
    "archetype), each a 5-cell plus in its own non-{6,7} color with one "
    "arm extended (arms [1,1,1,2] canonically, [1,1,1,3] as an extension; "
    "the realized maximum arm length always equals max_arm_len). For each "
    "cross the rule clears the border cell its longest arm faces to 0 and "
    "paints the opposite border cell in the cross's color. Placement "
    "enforces the canonical collision-free invariant: horizontal-arm "
    "crosses occupy distinct rows and vertical-arm crosses distinct "
    "columns, so every cross's two border edits land on unique cells."
)

INVARIANTS = [
    "background is 7; the perimeter frame is 6",
    "every interior object is a single-colored cross: arms [1,1,1,L] with unique longest L in 2..3",
    "cross colors are distinct and not 6 or 7",
    "horizontal-arm crosses sit in distinct rows; vertical-arm crosses in distinct columns",
    "every cross changes the border (facing cell cleared to 0, opposite painted)",
]

PALETTE_KINDS = ("canonical", "extended")
DEGENERATE_TEXTURES = ("one_cross", "four_directions", "frame_hugger")
HELPFUL_TEXTURES = ()

AXES = {
    "grid_h":      {"type": "int", "default": "band rng 11..16 (11-biased)", "valid": "11..16"},
    "grid_w":      {"type": "int", "default": "band rng 11..16 (11-biased)", "valid": "11..16"},
    "cross_count": {"type": "int", "default": "band rng 1..5", "valid": "1..5"},
    "max_arm_len": {"type": "int", "default": "band 2..3 (exact max)", "valid": "2..3"},
    "palette_kind": {"type": "str", "default": "rng 0.75 canonical / 0.25 extended",
                     "valid": "|".join(PALETTE_KINDS)},
    "texture":     {"type": "str", "default": "none",
                    "valid": "|".join(DEGENERATE_TEXTURES)},
}

_DIRS = {"up": (-1, 0), "dn": (1, 0), "lt": (0, -1), "rt": (0, 1)}
_CARD = tuple(_DIRS.values())
_CROSS_COLORS = (1, 2, 3, 4, 5, 8, 9)
_CANONICAL_SIGNATURES = {
    (
        11,
        11,
        (2, 5, 8, 9),
        ((1, 1, 1, 2),) * 4,
    ),
}


def _components(grid):
    """Maximal 4-connected same-color interior components (non-6, non-7)."""
    h, w = len(grid), len(grid[0])
    seen = [[False] * w for _ in range(h)]
    comps = []
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            v = grid[r][c]
            if v in (6, 7) or seen[r][c]:
                continue
            stack, cells = [(r, c)], []
            seen[r][c] = True
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _CARD:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and not seen[nr][nc]
                            and grid[nr][nc] == v):
                        seen[nr][nc] = True
                        stack.append((nr, nc))
            comps.append((v, cells))
    return comps


def _cross_info(cells):
    """(center, arms) for a cross component: center = the max-neighbor
    cell; arms = same-column above/below and same-row left/right counts."""
    S = set(cells)
    best, bn = None, -1
    for (r, c) in cells:
        n = sum((r + dr, c + dc) in S for dr, dc in _CARD)
        if n > bn:
            best, bn = (r, c), n
    r, c = best
    return best, {
        "up": sum(1 for (rr, cc) in S if cc == c and rr < r),
        "dn": sum(1 for (rr, cc) in S if cc == c and rr > r),
        "lt": sum(1 for (rr, cc) in S if rr == r and cc < c),
        "rt": sum(1 for (rr, cc) in S if rr == r and cc > c),
    }


def _is_cross(cells):
    """The cross shape contract: exactly one 4-neighbor center, and arm
    counts sorted [1,1,1,L] with the unique longest L in 2..3 (6..7 cells
    total). Rejects ties, two extended arms ([1,1,2,3]), and over-long
    arms ([1,1,1,4])."""
    center, arms = _cross_info(cells)
    S = set(cells)
    four = sum(1 for (r, c) in S
               if sum((r + dr, c + dc) in S for dr, dc in _CARD) == 4)
    if four != 1:
        return False
    ordered = sorted(arms.values())
    return (ordered[:3] == [1, 1, 1] and ordered[3] in (2, 3)
            and len(cells) == 1 + sum(arms.values()))


def _rule_output(grid):
    """Independent Python re-implementation of the canonical oracle:
    per cross, clear the border cell the strictly-longest arm faces to 0
    and paint the opposite border cell with the cross's color."""
    h, w = len(grid), len(grid[0])
    out = [row[:] for row in grid]
    for color, cells in _components(grid):
        (r, c), arms = _cross_info(cells)
        mx = max(arms.values())
        if arms["up"] == mx:
            out[0][c] = 0
            out[h - 1][c] = color
        elif arms["dn"] == mx:
            out[h - 1][c] = 0
            out[0][c] = color
        elif arms["lt"] == mx:
            out[r][0] = 0
            out[r][w - 1] = color
        else:
            out[r][w - 1] = 0
            out[r][0] = color
    return out


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural invariants of a lawful instance: rectangular grid inside
    the declared 11..16 envelope; a solid 6 perimeter frame with a 7
    background; >=1 interior crosses, each a single-colored 5-cell plus
    with a strictly-longest arm (unique 4-neighbor center, unique max arm),
    distinct cross colors outside {6,7}; the collision-free invariant
    (horizontal-arm crosses in distinct rows, vertical-arm crosses in
    distinct columns) so no two crosses project onto the same border cell;
    and the rule visibly fires. Rejects arm ties (priority-rule ambiguity),
    projection collisions (overwrite ambiguity), broken frames, and
    identity draws."""
    if not grid or not grid[0]:
        return ["empty grid"]
    h, w = len(grid), len(grid[0])
    if any(len(row) != w for row in grid):
        return ["ragged grid"]
    errs = []
    if h > 16 or w > 16:
        errs.append(f"outside declared 11..16 envelope: {h}x{w}")
    if h < 11 or w < 11:
        errs.append(f"below 11x11 canonical floor: {h}x{w}")
    flat = [v for row in grid for v in row]
    if any(not isinstance(v, int) or isinstance(v, bool) or not 0 <= v <= 9
           for v in flat):
        errs.append("color outside 0..9")
    if errs:
        return errs
    # frame integrity: the whole perimeter is 6
    for c in range(w):
        if grid[0][c] != 6 or grid[h - 1][c] != 6:
            errs.append("top/bottom frame row is not solid 6")
            break
    for r in range(h):
        if grid[r][0] != 6 or grid[r][w - 1] != 6:
            errs.append("left/right frame column is not solid 6")
            break
    if set(v for r in range(1, h - 1) for c in range(1, w - 1)
           for v in [grid[r][c]]) - (set(_CROSS_COLORS) | {7}):
        errs.append("interior color outside {1,2,3,4,5,7,8,9}")
    if errs:
        return errs
    comps = _components(grid)
    if not comps:
        errs.append("no crosses inside the frame")
        return errs
    if not 1 <= len(comps) <= 5:
        errs.append(f"cross count {len(comps)} outside declared 1..5")
    colors = [color for color, _cells in comps]
    if len(set(colors)) != len(colors):
        errs.append("cross colors are not distinct")
    horiz_rows = {}
    vert_cols = {}
    for color, cells in comps:
        if not _is_cross(cells):
            errs.append(f"interior object of color {color} is not a "
                        f"[1,1,1,L] cross (unique longest L in 2..3, "
                        f"6..7 cells)")
            continue
        (r, c), arms = _cross_info(cells)
        mx = max(arms.values())
        direction = next(d for d in ("up", "dn", "lt", "rt") if arms[d] == mx)
        if direction in ("lt", "rt"):
            if r in horiz_rows:
                errs.append(f"horizontal-arm crosses share row {r} "
                            f"(projection collision)")
            horiz_rows[r] = color
        else:
            if c in vert_cols:
                errs.append(f"vertical-arm crosses share column {c} "
                            f"(projection collision)")
            vert_cols[c] = color
    if errs:
        return errs
    if _rule_output(grid) == grid:
        errs.append("identity draw: no border cell changes")
    return errs


def canonical_profile_signature(grid):
    """Return the complete linked profile used by the canonical-prior audit.

    This deliberately keeps rule-valid generalized instances separate from
    the empirical ARC profile.  For example, a collision-free 11x11 scene
    with four length-2 crosses but an extended-palette color is lawful, yet
    it is not evidence that the official {2,5,8,9} profile was sampled.
    """
    if self_check(grid):
        return None
    colors = []
    arm_profiles = []
    for color, cells in _components(grid):
        _center, arms = _cross_info(cells)
        colors.append(color)
        arm_profiles.append(tuple(sorted(arms.values())))
    return (
        len(grid),
        len(grid[0]),
        tuple(sorted(colors)),
        tuple(sorted(arm_profiles)),
    )


def observe_overrides(grid) -> dict:
    """Realized per-draw values of the exact semantic axes (KRF-0001/0002),
    derived from the grid itself: the number of interior crosses and the
    realized maximum arm length across them."""
    comps = _components(grid)
    max_arm = 0
    for _color, cells in comps:
        _center, arms = _cross_info(cells)
        max_arm = max(max_arm, max(arms.values()))
    return {"cross_count": len(comps), "max_arm_len": max_arm}


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Band-shaped random draw; an override must execute exactly on any
    band, so it is validated against the full declared range (KRF-0001)."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _banded_dim(ctx, overrides, label, lo, hi, valid_lo, valid_hi, p11):
    """Dimension draw biased onto the all-canonical 11 (the demos are
    always 11x11); an override must execute exactly on any band."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    if ctx.draw_rng(label + "_exact11").random() < p11:
        return 11
    return ctx.draw_int(label, lo, hi)


def _band_params(difficulty):
    """(dim range, cross-count range, arm length, p(exact 11), p(canonical
    archetype)). The archetype draw forces 11x11 / 4 crosses / official
    colors / arm 2 -- the exact official geometry; the generalized family
    keeps counts 1..5, length-3 arms, and extended colors as
    disambiguating witnesses."""
    if difficulty == "easy":
        return (11, 12), (1, 3), 2, 0.6, 0.5
    if difficulty == "hard":
        return (12, 16), (3, 5), 3, 0.5, 0.35
    return (11, 13), (2, 4), 2, 0.6, 0.5     # medium / default


def _place_cross(g, rng, color, occupied, used_rows, used_cols, arm_len,
                 force_k=False):
    """Place one plus with a strictly-longest arm in a random cardinal
    direction, honoring the collision-free invariant: horizontal-arm
    crosses need a fresh row, vertical-arm crosses a fresh column.
    Enumerates every legal (direction, size, position) candidate and picks
    one uniformly, so a placement is found whenever one exists. With
    force_k, only candidates whose extension realizes `arm_len` exactly are
    considered (used to guarantee the declared maximum arm). Returns the
    direction or None."""
    h, w = len(g), len(g[0])
    cands = []
    k_lo = arm_len - 1 if force_k else 1
    for d_name, d in _DIRS.items():
        horizontal = d_name in ("lt", "rt")
        for k in range(k_lo, arm_len):
            r_lo = 2 + (k if d[0] < 0 else 0)
            r_hi = h - 3 - (k if d[0] > 0 else 0)
            c_lo = 2 + (k if d[1] < 0 else 0)
            c_hi = w - 3 - (k if d[1] > 0 else 0)
            for r in range(r_lo, r_hi + 1):
                if horizontal and r in used_rows:
                    continue
                for c in range(c_lo, c_hi + 1):
                    if not horizontal and c in used_cols:
                        continue
                    cells = {(r, c), (r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)}
                    for step in range(2, k + 2):
                        cells.add((r + d[0] * step, c + d[1] * step))
                    # different-colored crosses may touch (canonical shows
                    # Manhattan-1 contact); only overlap is forbidden
                    if cells & occupied:
                        continue
                    cands.append((cells, r, c, horizontal, d_name))
    if not cands:
        return None
    cells, r, c, horizontal, d_name = cands[rng.randrange(len(cands))]
    for cr, cc in cells:
        g[cr][cc] = color
    occupied |= cells
    (used_rows if horizontal else used_cols).add(r if horizontal else c)
    return d_name


def generate(seed, sample_index, *, difficulty=None, **overrides):
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    rng = ctx.draw_rng("layout")
    texture = overrides.get("texture")
    if texture is not None:
        if texture in DEGENERATE_TEXTURES:
            extra = sorted(k for k, v in overrides.items()
                           if k != "texture" and v is not None)
            if extra:
                raise ValueError(
                    f"degenerate texture {texture!r} is a fixed diagnostic "
                    f"layout; it takes no other overrides, got {extra}")
            return _draw_from_degenerate(texture, rng)
        raise ValueError(f"unknown texture {texture!r}; valid: "
                         f"{DEGENERATE_TEXTURES}")

    dr, cr_, arm_default, p11, p_canon = _band_params(difficulty)
    canon = ctx.draw_rng("canon_prior").random() < p_canon

    def _dim(label, lo, hi):
        if label in overrides and overrides[label] is not None:
            return ctx.draw_int(label, 11, 16)
        if canon or ctx.draw_rng(label + "_exact11").random() < p11:
            # KRF-0004: the 11-biased shortcut records the realized dimension
            # under its declared label (typed draw; no RNG consumed).
            ctx.overrides[label] = 11
            return ctx.draw_int(label, 11, 16)
        return ctx.draw_int(label, lo, hi)

    h = _dim("grid_h", *dr)
    w = _dim("grid_w", *dr)
    if overrides.get("cross_count") is not None:
        n = ctx.draw_int("cross_count", 1, 5)
    elif canon:
        ctx.overrides["cross_count"] = 4
        n = ctx.draw_int("cross_count", 1, 5)
    else:
        n = ctx.draw_int("cross_count", cr_[0], cr_[1])
    if overrides.get("max_arm_len") is not None:
        max_arm = ctx.draw_int("max_arm_len", 2, 3)
    elif canon:
        ctx.overrides["max_arm_len"] = 2
        max_arm = ctx.draw_int("max_arm_len", 2, 3)
    else:
        # the band constant is still a selected exact value: record it
        ctx.overrides["max_arm_len"] = arm_default
        max_arm = ctx.draw_int("max_arm_len", 2, 3)

    palette_kind = overrides.get("palette_kind")
    if palette_kind is None:
        palette_kind = ("canonical"
                        if canon or ctx.draw_rng("palette_kind").random() < 0.75
                        else "extended")
    if palette_kind not in PALETTE_KINDS:
        raise ValueError(f"unknown palette_kind {palette_kind!r}")
    if palette_kind == "canonical":
        # the demos only ever use cross colors from {2, 5, 8, 9}
        pool = [2, 5, 8, 9] + ([1, 3, 4] if n > 4 else [])
    else:
        pool = list(_CROSS_COLORS)
    rng.shuffle(pool)
    colors = pool[:n]

    # Collision-free placement: every cross gets its own projection lane
    # (horizontal-arm crosses a fresh row, vertical-arm crosses a fresh
    # column). Direction/size draws are re-rolled per whole-layout attempt;
    # the drawn count is never silently shed -- only a genuinely infeasible
    # explicit combination fails loudly. Cross 0 always realizes the
    # declared maximum arm length (max_arm_len is an exact maximum).
    placed = 0
    for _layout in range(60):
        g = full_grid(h, w, 7)
        for c in range(w):
            g[0][c] = 6
            g[h - 1][c] = 6
        for r in range(h):
            g[r][0] = 6
            g[r][w - 1] = 6
        occupied = set()
        used_rows, used_cols = set(), set()
        placed = 0
        for i in range(n):
            if _place_cross(g, rng, colors[i], occupied, used_rows,
                            used_cols, max_arm, force_k=(i == 0)) is None:
                break
            placed += 1
        if placed == n:
            break
    else:
        raise ValueError(
            f"could not place {n} collision-free crosses on {h}x{w}")

    errs = self_check(g, difficulty=difficulty)
    if errs:
        raise ValueError(f"internal layout violated self_check: {errs}")
    return g


def _draw_from_degenerate(name, rng):
    """Fixed minimal layouts; every one is a lawful, self_check-clean draw."""
    g = full_grid(11, 11, 7)
    for c in range(11):
        g[0][c] = 6
        g[10][c] = 6
    for r in range(11):
        g[r][0] = 6
        g[r][10] = 6
    if name == "one_cross":
        # plus at (5,5) with a length-2 right arm
        for (r, c) in [(5, 5), (4, 5), (6, 5), (5, 4), (5, 6), (5, 7)]:
            g[r][c] = 2
        return g
    if name == "four_directions":
        # up-arm cross centered (4, 3): cells of the plus plus tip (2, 3)
        for (r, c) in [(4, 3), (3, 3), (5, 3), (4, 2), (4, 4), (2, 3)]:
            g[r][c] = 1
        # rt-arm cross centered (7, 6): tip (7, 8); row 7 distinct from lt row
        for (r, c) in [(7, 6), (6, 6), (8, 6), (7, 5), (7, 7), (7, 8)]:
            g[r][c] = 2
        # dn-arm cross centered (3, 8): tip (5, 8); col 8 distinct from up col 3
        for (r, c) in [(3, 8), (2, 8), (4, 8), (3, 7), (3, 9), (5, 8)]:
            g[r][c] = 3
        # lt-arm cross centered (8, 3): tip (8, 1); row 8 distinct from rt row 7
        for (r, c) in [(8, 3), (7, 3), (9, 3), (8, 2), (8, 4), (8, 1)]:
            g[r][c] = 4
        return g
    if name == "frame_hugger":
        # plus at (5,2) with a length-2 right arm; left arm cell touches frame
        for (r, c) in [(5, 2), (4, 2), (6, 2), (5, 1), (5, 3), (5, 4)]:
            g[r][c] = 9
        return g
    raise ValueError(f"unknown degenerate texture {name!r}")
