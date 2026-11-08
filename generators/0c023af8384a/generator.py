"""Generator for 0c023af8384a — union with the UD-flip.

Rule: starting FROM the input, each non-zero cell (row-major, reading
the ORIGINAL grid) paints its value at the vertically mirrored row
(h-1-r, c). Sources in BOTH halves mirror; mutually mirrored cells of
different colors SWAP; center-row cells (odd h) self-mirror (no-op);
a source on another's mirror spot is overwritten. Vertical twin of
099aeda5aa7b.

Combinatorial axes: grid_h/w, marks, texture
(plain|swap_pair|on_axis|dense).
Degenerates: empty_grid, already_symmetric (identity).
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0c023af8384a"
VERSION = "2.2.0"
TASK_ID = "0c023af8384a"
SUMMARY = (
    "Scattered marks copy to their mirrored ROW - sources sit in "
    "BOTH halves (refutes 'top-to-bottom copy'; the old generator "
    "was top-half only). swap_pair boards put different colors at "
    "mutually mirrored spots: they SWAP (mirror writes overwrite, "
    "input does not win). on_axis boards use a center-row no-op plus "
    "an effective source on odd heights, or an effective source touching "
    "the central seam on exact even heights. dense normally packs 8-14 "
    "marks while exact mark pins always take precedence."
)

# Rivals: 'copy top half down' refuted by bottom-half sources
# mirroring up. 'existing cells win' refuted by swap_pair. 'center
# row duplicates' refuted by on_axis no-ops. 3-4 demos with sources
# in both halves.
EXAMPLES_NEEDED = 3

INVARIANTS = [
    "sources appear in BOTH halves across the task",
    "swap_pair boards: a mirrored pair with different colors when marks >= 2",
    "on_axis boards: an axis-adjacent source and, when possible, a center-row no-op",
]

DEGENERATE_TEXTURES = ("empty_grid", "already_symmetric")
HELPFUL_TEXTURES = ("plain", "swap_pair", "on_axis", "dense")

AXES = {
    "grid_h":  {"type": "int", "default": "rng 6..12", "valid": "4..16"},
    "grid_w":  {"type": "int", "default": "rng 7..13", "valid": "5..18"},
    "marks":   {"type": "int", "default": "rng 3..6", "valid": "1..20"},
    "texture": {"type": "str", "default": "rng helpful",
                "valid": "plain|swap_pair|on_axis|dense",
                "doc": "swap_pair demonstrates overwrite/swap; on_axis uses "
                       "a center-row no-op when lawful and always retains an "
                       "effective near-axis source."},
}

_COLORS = (1, 2, 3, 4, 5, 6, 7, 8, 9)


def _mirror(g):
    h, w = len(g), len(g[0])
    out = [row[:] for row in g]
    for r in range(h):
        for c in range(w):
            v = g[r][c]
            if v != 0:
                out[h - 1 - r][c] = v
    return out


def observe_overrides(grid):
    """Recover the exact numeric control values from a returned grid."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        raise ValueError("grid must be nonempty and rectangular")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "marks": sum(cell != 0 for row in grid for cell in row),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Verify: non-empty board whose horizontal-midline mirror changes something."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return ["grid must be nonempty and rectangular"]
    errs = []
    h, w = len(grid), len(grid[0])
    nz = [(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0]
    if not nz:
        errs.append("grid is empty: no sources for vertical mirror")
    if h < 2:
        errs.append(f"height {h} too small for vertical mirror")
    if nz and _mirror(grid) == grid:
        errs.append("input is already horizontally symmetric; mirror rule is a no-op")
    return errs


def _strict_request(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError("unknown override: " + ", ".join(sorted(unknown)))


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _strict_request(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    ctx = gen_ctx(seed=seed, sample_index=sample_index,
                  version=VERSION, task_id=TASK_ID,
                  difficulty=difficulty, overrides=overrides)
    requested_texture = overrides.get("texture")
    if requested_texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(requested_texture, ctx)
    if requested_texture is None:
        texture = ctx.draw_choice(
            "texture", ("plain", "plain", "swap_pair", "on_axis", "dense")
        )
    else:
        texture = ctx.draw_choice("texture", HELPFUL_TEXTURES)

    if difficulty == "easy":
        h_bounds, w_bounds, mark_bounds = (6, 8), (7, 10), (2, 4)
    elif difficulty == "hard":
        h_bounds, w_bounds, mark_bounds = (10, 12), (11, 13), (5, 7)
    else:
        h_bounds, w_bounds, mark_bounds = (6, 12), (7, 13), (3, 6)

    exact_h = "grid_h" in overrides
    exact_marks = "marks" in overrides
    if exact_h:
        h = ctx.draw_int_strict("grid_h", 4, 16)
    elif texture == "on_axis":
        odd_heights = tuple(value for value in range(h_bounds[0], h_bounds[1] + 1) if value % 2)
        h = ctx.draw_choice("grid_h", odd_heights)
    else:
        h = ctx.draw_int_strict("grid_h", *h_bounds)
    w = ctx.draw_int_strict("grid_w", *((5, 18) if "grid_w" in overrides else w_bounds))
    if exact_marks:
        marks = ctx.draw_int_strict("marks", 1, 20)
    elif texture == "dense":
        marks = ctx.draw_int_strict("marks", 8, 14)
    else:
        marks = ctx.draw_int_strict("marks", *mark_bounds)

    rng = ctx.draw_rng("layout")
    g = full_grid(h, w, 0)
    used: set[tuple[int, int]] = set()
    remaining = marks

    def paint(r, c, color=None):
        nonlocal remaining
        if remaining <= 0 or (r, c) in used:
            return False
        g[r][c] = rng.choice(_COLORS) if color is None else color
        used.add((r, c))
        remaining -= 1
        return True

    if texture == "swap_pair":
        r = rng.randint(0, h // 2 - 1)
        c = rng.randint(0, w - 1)
        if remaining >= 2:
            ca, cb = rng.sample(_COLORS, 2)
            paint(r, c, ca)
            paint(h - 1 - r, c, cb)
        else:
            paint(r, c)

    if texture == "on_axis" and remaining:
        if h % 2 and remaining >= 2:
            # Reserve at least one mark for an effective off-axis source.
            axis_target = min(rng.randint(1, 2), remaining - 1)
            axis = h // 2
            while axis_target:
                c = rng.randint(0, w - 1)
                if paint(axis, c):
                    axis_target -= 1
        # An even grid has no fixed row; a source touching the seam is the
        # closest lawful analogue.  It is also used for a one-mark odd request
        # so the exact pin never degenerates into an identity lesson.
        if remaining and (marks == 1 or h % 2 == 0):
            near_axis = h // 2 - 1
            paint(near_axis, rng.randint(0, w - 1))

    candidates = [(r, c) for r in range(h) for c in range(w) if (r, c) not in used]
    rng.shuffle(candidates)
    for r, c in candidates:
        if remaining <= 0:
            break
        paint(r, c)
    if remaining:
        exc = ValueError(f"marks={marks} cannot fit in a {h}x{w} grid")
        exc.incompatible_axes = ("grid_h", "grid_w", "marks")
        raise exc

    # An unlucky layout can be mirror-symmetric.  Preserve dimensions and
    # the exact mark count while breaking that symmetry.  A populated mirrored
    # pair can be split by color; an odd-height axis-only layout instead moves
    # one center-row mark to an empty off-axis cell.
    if _mirror(g) == g:
        changed = False
        for r in range(h // 2):
            for c in range(w):
                if g[r][c] != 0 and g[h - 1 - r][c] != 0:
                    replacement = next(color for color in _COLORS if color != g[h - 1 - r][c])
                    g[r][c] = replacement
                    changed = True
                    break
            if changed:
                break
        if not changed and h % 2:
            axis = h // 2
            source = next(((axis, c) for c in range(w) if g[axis][c] != 0), None)
            target = next(
                ((r, c) for r in range(h) if r != axis for c in range(w) if g[r][c] == 0),
                None,
            )
            if source is not None and target is not None:
                sr, sc = source
                tr, tc = target
                g[tr][tc], g[sr][sc] = g[sr][sc], 0
    if _mirror(g) == g:
        raise ValueError("could not construct a non-identity mirror lesson")
    return g


def _draw_from_degenerate(name, ctx):
    """Draw explicitly requested negative examples outside the helpful axis."""
    rng = ctx.draw_rng("degenerate_layout")
    h = ctx.draw_int_strict("grid_h", *((4, 16) if "grid_h" in ctx.overrides else (6, 10)))
    w = ctx.draw_int_strict("grid_w", *((5, 18) if "grid_w" in ctx.overrides else (7, 12)))
    g = full_grid(h, w, 0)
    if name == "empty_grid":
        return g
    for _ in range(rng.randint(2, 4)):
        r = rng.randint(0, h // 2 - 1)
        c = rng.randint(0, w - 1)
        color = rng.choice(_COLORS)
        g[r][c] = color
        g[h - 1 - r][c] = color
    return g
